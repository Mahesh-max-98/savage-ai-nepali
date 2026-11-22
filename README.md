# Savage AI Nepali

A Nepali/Nepanglish humour content studio with an authenticated dashboard, AI caption generation, generated meme artwork, and scheduled Facebook Page publishing.

## Features

- Dashboard with start/pause controls, schedule settings, service checks, and recent post history
- Short original captions across rotating humour categories
- Generated image required for every post
- Near-duplicate caption checks and basic safety filtering
- PostgreSQL-backed settings, post history, and image storage
- Separate Render worker for scheduled jobs
- Meta Graph API Page photo publishing

## Getting started

Read [SETUP.md](SETUP.md) for required API credentials, Facebook Page permissions, local development, and Render deployment instructions.

**Security:** Never commit API keys, Facebook access tokens, or dashboard passwords. Store them only as private environment variables.

**Automation is paused by default.** Configure the providers, sign in, verify the connections, and start the worker from the dashboard only when you're ready.
