# Savage AI Nepali — Meme to Reels

This feature converts images already recorded in `generated/index.json` into short vertical MP4 videos.

## Output

- MP4 video: `reels/ready/`
- Facebook caption and hashtags: `reels/captions/`
- Processing history: `reels/index.json`
- Video format: 1080 × 1920, 30 FPS, 8 seconds, H.264 MP4

The video uses a blurred full-screen background, keeps the original meme visible, adds the caption in a separate panel, and applies a gentle zoom. It is silent by default.

## Run locally

Install FFmpeg and Noto Sans Devanagari fonts, then:

```bash
pip install Pillow==11.3.0
python reel_runner.py --limit 3
```

Convert a specific image:

```bash
python reel_runner.py --image generated/example.png
```

Optional music:

```bash
python reel_runner.py --limit 3 --music assets/your-licensed-track.mp3
```

Only use music you created, own, or have permission to use. Without a music file, reels are exported silently.

## GitHub Actions

Open **Actions → Savage AI Nepali · Meme to Reels → Run workflow** and choose the number of new reels. The workflow also checks once daily for newly generated images. It commits videos and captions to `reels/` and uploads the MP4s as a downloadable workflow artifact.

## Facebook publishing

This feature only prepares videos and captions. It does not upload or publish to Facebook. Review each reel and post it manually. Automatic publishing can be added separately after confirming the Page, app permissions, and supported Reels Publishing API setup.
