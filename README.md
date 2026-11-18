# Clip Uploader

A personal command-line tool that uploads short videos I have edited to my own YouTube channel, using the YouTube Data API v3 (`videos.insert`).

- Single user: only the channel owner uses it.
- Runs locally on my Windows PC. There is no server or database.
- OAuth scope: `https://www.googleapis.com/auth/youtube.upload` only.
- Privacy policy: https://[github-username].github.io/clip-uploader/

## Setup

1. Create a Google Cloud project, enable **YouTube Data API v3**, and create an OAuth client of type **Desktop app**.
2. Download the client file and save it as `client_secret.json` in this folder.
3. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

## Usage

```
python upload.py --file clip.mp4 --title "My clip #shorts" --description "..." --tags tag1,tag2 --privacy public
```

| Option | Meaning |
|---|---|
| `--file` | Video file to upload (required) |
| `--title` | Title, up to 100 characters (required) |
| `--description` / `--description-file` | Description text, or a text file containing it |
| `--tags` | Comma-separated tags |
| `--category` | `gaming`, `entertainment`, `sports`, `comedy`, ... or a numeric category ID (default `entertainment`) |
| `--privacy` | `private`, `unlisted` or `public` (default `private`) |
| `--publish-at` | Scheduled publish time in ISO 8601, e.g. `2026-11-20T19:00:00+05:30` |

On the first run a browser opens to sign in and grant consent. The token is saved to `token.json` and reused. The script uses resumable uploads and retries on server and network errors, then prints the video ID and YouTube Studio link.

## Data and privacy

`client_secret.json` and `token.json` stay on my computer and are excluded from this repository by `.gitignore`. No data is collected, stored elsewhere or shared. Access can be revoked at https://myaccount.google.com/permissions.

This tool uses YouTube API Services: [YouTube Terms of Service](https://www.youtube.com/t/terms), [Google Privacy Policy](https://policies.google.com/privacy).
