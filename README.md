# Savage AI Nepali — free automation

A no-hosting-cost Nepali/Nepanglish humour publisher. The active free deployment uses **GitHub Actions** as the scheduler; it does not require Render, a paid worker, a paid database, or an OpenAI image API key.

## What it does

- Runs a scheduled check every 30 minutes (GitHub may delay scheduled runs).
- Uses Groq's API for short original captions.
- Tries a free Pollinations image endpoint; if unavailable, creates a local meme-style poster so the Facebook post still has an image.
- Checks recent captions for near-duplicates and basic unsafe language.
- Publishes a photo post to your Facebook Page through Meta Graph API.
- Saves posting history and status in the repository.
- Provides a free, read-only GitHub Pages dashboard.

## Setup

Read [FREE_SETUP.md](FREE_SETUP.md). Add the three private GitHub Actions secrets:
- `GROQ_API_KEY`
- `FACEBOOK_PAGE_ID`
- `FACEBOOK_PAGE_ACCESS_TOKEN`

Never commit secrets or paste them into public files or chats.

## Important

- Automation starts **paused**. Enable it manually from GitHub Actions.
- Default daily limit is 8 posts; interval is 30 minutes. This is a safety cap to avoid flooding your Page.
- GitHub Actions standard runners are free for public repositories. The repository must remain public for this setup to use the public-repository free runner allowance.
- Groq and Pollinations have service/rate limits; free access is not unlimited or guaranteed.
- The static dashboard is public and read-only. Use the GitHub Actions workflow page for controls.
- The previous Render/Flask deployment files are not used by the free automation path.
