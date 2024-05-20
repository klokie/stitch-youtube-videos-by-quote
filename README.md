# python script to stitch YouTube videos by quote

## installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## configuration

- get a YouTube API key from [Google Developers Console](https://console.developers.google.com/)
  - [YouTube Data API v3 – APIs & Services – stitch-youtube-vide… – Google Cloud console](https://console.cloud.google.com/apis/library/youtube.googleapis.com)
- create a file named `.env` in the root directory
- add the following lines to `.env`:

```toml
YOUTUBE_API_KEY=""
```

## usage

```bash
python stitch.py
```
