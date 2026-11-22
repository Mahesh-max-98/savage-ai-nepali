# Free setup — Savage AI Nepali

This version avoids paid hosting and paid AI image APIs.

## Free architecture

- GitHub Actions: scheduled Python job every 30 minutes.
- Groq: free-tier text API for captions (subject to provider limits).
- Pollinations: best-effort free AI image endpoint. If unavailable or rate-limited, a local Pillow poster is generated instead.
- Meta Graph API: publishes the image and caption to your Facebook Page.
- Repository JSON files: posting state and history.
- GitHub Pages: optional free, read-only dashboard.

No Render web service, background worker, paid database, or OpenAI image API is required.

## 1. Add private GitHub Actions secrets

Open this repository:

**Settings → Secrets and variables → Actions → New repository secret**

Add these names one at a time:

| Secret name | Value |
|---|---|
| `GROQ_API_KEY` | Your Groq API key |
| `FACEBOOK_PAGE_ID` | Your Facebook Page ID |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | Your Page access token |

Keep the values private. Never put them in source files, issues, screenshots, or chats.

## 2. Enable GitHub Actions

Open the repository's **Actions** tab and enable workflows if GitHub asks.

The workflow is scheduled at minute 15 and 45 of each hour (UTC), every 30 minutes. GitHub can delay or occasionally skip scheduled runs during high load. In public repositories, scheduled workflows are disabled if the repository has no activity for 60 days.

## 3. Start or pause automation

Open **Actions → Savage AI Nepali · Free Auto Publisher → Run workflow**.

Choose one action:
- `enable`: turn scheduled posting on.
- `pause`: stop scheduled posting.
- `publish_now`: create and publish one post immediately.
- `status`: inspect the current status in the workflow logs.

Automation is initially paused. The default daily limit is 8 posts, even though the scheduler checks every 30 minutes.

## 4. Optional free dashboard

Open **Settings → Pages**:
1. Under Build and deployment, choose **Deploy from a branch**.
2. Choose branch `main` and folder `/docs`.
3. Save and wait for GitHub Pages to publish.

Dashboard: https://mahesh-max-98.github.io/savage-ai-nepali/

The dashboard is public and read-only. Use the Actions tab for start/pause/publish controls.

## 5. Facebook requirements

The Page token must belong to a Page you manage and have the required publishing permissions. The Meta app and your Page role may need appropriate permissions and review. See the official [Meta Page Photos API documentation](https://developers.facebook.com/docs/graph-api/reference/page/photos/).

## Free-tier limitations

- Scheduled jobs are not guaranteed to run at the exact minute. GitHub may delay them; scheduled workflows in public repos can be disabled after 60 days without repository activity.
- Standard GitHub-hosted runners are free for public repositories. Keep the repository public for this setup; source code and posting history will be publicly visible. Repository secrets are stored separately from code.
- Groq has rate limits and service availability limits. If its free quota is exhausted, a run will fail until quota resets or access is restored.
- The free Pollinations image endpoint is best-effort and may rate-limit or change. If it fails, the program makes a local poster instead; that fallback is not AI-generated.
- Facebook may reject publishing if the token expires, permissions are missing, or the Page has restrictions.
- This setup has no paid always-on server and cannot promise uninterrupted 24/7 delivery.

## Change the posting cap

Edit `data/state.json` on the main branch. Keep `interval_minutes` at 30 and set `daily_limit` between 1 and 48. The default is 8 posts per day to reduce spam risk. Commit the change.
