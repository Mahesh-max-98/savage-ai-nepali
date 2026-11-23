# Nepali News Assistant

The news monitor is separate from the joke/meme generator. It collects public RSS headlines and short feed excerpts, asks Groq to create an original 3–8-line Nepali brief, and stores the source URL for traceability.

## Configured discovery sources
- NEB official-site notices/results via Google News RSS restricted to neb.gov.np
- BBC Nepali via Google News RSS restricted to bbc.com/nepali
- RONB / RONB Post via Google News RSS restricted to ronbpost.com
- Onlinekhabar public RSS
- OK Khabar via Google News RSS restricted to okkhabar.com
- Laligurash Media Network via Google News RSS restricted to laligurash.com

The monitor does not scrape Facebook pages. Facebook Page feeds require eligible Meta permissions and app review; use Meta's official APIs only. BBC's Information Syndication API requires an authorised relationship and API key, so this project does not bypass that access requirement.

## Publishing controls
- NEWS_DRY_RUN=true is the default: create drafts, do not publish.
- Set NEWS_DRY_RUN=false only after checking drafts and confirming the Facebook Page connection.
- Text posts use the Page /{page-id}/feed endpoint with only a message field: no photo or link attachment is sent.
- Maximum 2 news posts per scheduled run by default.
- Duplicate story IDs are stored in generated/news_index.json.
- The AI receives headlines and short feed excerpts only; it must not invent details or reproduce full articles.
- The original source URL is kept in run history; the Facebook post names the source but omits a URL to prevent link-preview images.

## GitHub Actions secrets
Add these in Repository Settings -> Secrets and variables -> Actions:
- GROQ_API_KEY
- FACEBOOK_PAGE_ID
- FACEBOOK_PAGE_ACCESS_TOKEN

The Page token must belong to the Page and have the required publishing permission approved by Meta. Never commit tokens to the repository.

Run Actions -> Savage AI Nepali - News Monitor. Keep dry-run enabled for the first test. The scheduled workflow also defaults to dry-run.
