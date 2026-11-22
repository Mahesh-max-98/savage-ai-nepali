# Savage AI Nepali — Joke & Meme Creator

**Tagline:** नयाँ दृष्टि, नयाँ हाँसो।

Savage AI Nepali creates original, funny Nepali and Nepanglish jokes with matching meme images. It prepares content for you to review and publish manually.

## What it does

- Generates original Nepali and Nepanglish jokes using Groq.
- Varies joke topics and formats: short dialogues, relatable one-liners, savage comebacks, and expectation-vs-reality humour.
- Creates a matching square meme illustration.
- Saves each joke as a Markdown file and each image in `generated/`.
- Keeps an index of previously generated jokes to reduce repetition.
- Lets you manually start a generation run from GitHub Actions.

## Important: manual publishing only

**This repository does not publish anything to Facebook.** It does not call the Facebook Graph API and does not need a Facebook Page ID or Facebook access token. You choose which generated joke/image to upload to your Page.

## Setup

1. Open **Settings → Secrets and variables → Actions**.
2. Add one repository secret: `GROQ_API_KEY`.
3. Open **Actions → Savage AI Nepali · Joke & Meme Creator → Run workflow**.
4. Select `generate` and run the workflow.
5. Open the latest commit and the `generated/` folder to view/copy the joke and image.

The model defaults to `openai/gpt-oss-120b`. The free Groq tier is subject to its current limits.

## Generated content

Each run adds:
- A `.md` file containing the joke, hashtags, and image link.
- A matching `.png` meme image.
- An updated `generated/index.json` content history.

Review jokes before posting. AI-generated content can occasionally need editing.
