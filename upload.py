"""
upload.py - Upload a video to your own YouTube channel with the YouTube Data API v3.

Usage examples:
  python upload.py --file "clips\\hardik.mp4" --title "Hardik Pandya vs MrBeast #shorts" ^
      --description "Who won?" --tags mrbeast,cricket,shorts --privacy private

  python upload.py --file clip.mp4 --title "..." --privacy private --publish-at 2026-11-20T19:00:00+05:30

First run opens a browser to sign in with the Google account that owns the channel.
After that, the saved token.json is reused.

Note: until your Cloud project passes the YouTube API compliance audit, YouTube
locks API uploads to private, whatever --privacy you choose.
"""

import argparse
import os
import sys
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET = os.path.join(HERE, "client_secret.json")
TOKEN_FILE = os.path.join(HERE, "token.json")

# Common YouTube category IDs
CATEGORIES = {
    "film": "1", "music": "10", "sports": "17", "gaming": "20",
    "people": "22", "comedy": "23", "entertainment": "24",
}

RETRY_STATUS = {500, 502, 503, 504}
MAX_RETRIES = 5


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET):
                sys.exit(f"client_secret.json not found in {HERE}")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds


def build_body(args):
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
    description = args.description or ""
    if args.description_file:
        with open(args.description_file, encoding="utf-8") as f:
            description = f.read()

    status = {
        "privacyStatus": args.privacy,
        "selfDeclaredMadeForKids": False,
    }
    if args.publish_at:
        # Scheduled publishing requires the video to start as private.
        status["privacyStatus"] = "private"
        status["publishAt"] = args.publish_at

    return {
        "snippet": {
            "title": args.title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": CATEGORIES.get(args.category, args.category),
        },
        "status": status,
    }


def upload(youtube, file_path, body):
    media = MediaFileUpload(file_path, chunksize=8 * 1024 * 1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response, retries = None, 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")
        except HttpError as e:
            if e.resp.status in RETRY_STATUS and retries < MAX_RETRIES:
                retries += 1
                wait = 2 ** retries
                print(f"Server error {e.resp.status}, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
        except (ConnectionError, TimeoutError, OSError) as e:
            # Network drops (e.g. WinError 10054). Retry the same chunk.
            if retries < MAX_RETRIES:
                retries += 1
                wait = 2 ** retries
                print(f"Network error ({e}), retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
    return response


def main():
    p = argparse.ArgumentParser(description="Upload a video to YouTube.")
    p.add_argument("--file", required=True, help="Path to the video file")
    p.add_argument("--title", required=True, help="Video title (max 100 chars)")
    p.add_argument("--description", default="", help="Description text")
    p.add_argument("--description-file", help="Read description from a text file instead")
    p.add_argument("--tags", default="", help="Comma-separated tags")
    p.add_argument("--category", default="entertainment",
                   help="gaming, entertainment, sports, comedy, ... or a numeric ID")
    p.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    p.add_argument("--publish-at", help="Schedule time, ISO 8601, e.g. 2026-11-20T19:00:00+05:30")
    args = p.parse_args()

    if not os.path.isfile(args.file):
        sys.exit(f"File not found: {args.file}")

    youtube = build("youtube", "v3", credentials=get_credentials())
    try:
        result = upload(youtube, args.file, build_body(args))
    except (HttpError, OSError) as e:
        sys.exit(f"Upload failed: {e}")

    vid = result["id"]
    print("Done!")
    print(f"Video ID: {vid}")
    print(f"Link:     https://youtu.be/{vid}")
    print(f"Studio:   https://studio.youtube.com/video/{vid}/edit")


if __name__ == "__main__":
    main()
