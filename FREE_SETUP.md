# Setup — Savage AI Nepali Joke & Meme Creator

This version creates jokes and meme images for you to publish manually. **It never posts to Facebook.**

## 1. Add the Groq key

Open the GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

Create only this secret:

| Secret name | Value |
|---|---|
| `GROQ_API_KEY` | Your Groq API key |

Do not add Facebook Page ID or Facebook Page Access Token. They are not used by this version. Never commit or share your Groq key.

## 2. Generate a joke and meme

1. Open the **Actions** tab.
2. Select **Savage AI Nepali · Joke & Meme Creator**.
3. Click **Run workflow**.
4. Select `generate`.
5. Click **Run workflow** again to start.

When it finishes, the workflow saves the joke and image into the repository's `generated/` folder.

## 3. Find your content

Open the repository's **Code** tab, then open `generated/`.

Each generation creates:
- A Markdown file with the joke and hashtags.
- A PNG image to use with the joke.
- An updated `index.json` history.

Download or open the image, copy the joke, review it, and publish it yourself on your Facebook Page whenever you choose.

## 4. Check content history

Run the workflow with the `status` action to view how many jokes have been generated and the latest entries.

## Notes

- The default model is `openai/gpt-oss-120b`.
- Groq free-tier limits and the free image endpoint may affect availability.
- The image endpoint is best-effort; if unavailable, the project creates a local poster.
- Review AI-generated content before posting.
- No Facebook publishing, Facebook token, or automatic posting schedule is included.


## Live trend research

The generator checks public Google Trends Nepal and Google News RSS feeds before creating a joke. It extracts headline topics only and asks the model to write a completely original Nepali/Nepanglish joke. Existing jokes, captions and punchlines are not copied. If live feeds fail, generation continues using general Nepali humour themes. Trend topics and feed status are saved with each generated item.
