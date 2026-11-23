# Savage AI Nepali — Meme to Reels

This feature converts images recorded in `generated/index.json` into vertical MP4 videos with optional Nepali female narration.

## Output

- MP4 video: `reels/ready/`
- Facebook caption and hashtags: `reels/captions/`
- Processing history: `reels/index.json`
- Video format: 1080 × 1920, 30 FPS, H.264 MP4
- Default voice: `ne-NP-HemkalaNeural` (female Nepali voice)

## Narration

The default reel command creates spoken Nepali narration using the caption text. If the spoken line takes longer than eight seconds, the video duration is extended to fit it. Voice audio is embedded in the MP4 and temporary audio files are removed after rendering.

The speech provider is the Edge TTS service through the community `edge-tts` Python package. It needs an internet connection at render time, uses an online third-party service, and is not an Azure Speech subscription integration. Service availability or terms may change. Do not send private or sensitive text to an online speech service.

## Run locally

Install FFmpeg, ffprobe, and Noto Sans Devanagari fonts, then:

```bash
pip install -r requirements.txt
python reel_runner.py --limit 3
```

Create a silent reel:

```bash
python reel_runner.py --limit 3 --no-voice
```

Optional background music (use only music you created, own, or are licensed to use):

```bash
python reel_runner.py --limit 3 --music assets/your-licensed-track.mp3
```

Voice can be selected with `--voice`; the default is the female Nepali Hemkala voice.

## GitHub Actions

Open **Actions → Savage AI Nepali · Meme to Reels → Run workflow**. Choose the number of new reels and whether to include female narration. The daily scheduled run also creates narrated reels by default. The workflow commits videos and captions to `reels/` and uploads MP4s as a downloadable workflow artifact.

## Facebook publishing

This feature only prepares videos and captions. It does not upload or publish to Facebook. Review each reel and post it manually. Automatic publishing can be added separately after confirming the Page, app permissions, and supported Reels Publishing API setup.
