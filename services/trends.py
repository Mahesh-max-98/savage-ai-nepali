import logging
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)
HEADERS = {"User-Agent": "SavageAINepali/1.0 (trend research)"}
TIMEOUT = 12
MAX_ITEMS = 12


def _clean(value):
    return re.sub(r"\s+", " ", (value or "")).strip()


def _fetch_rss(url, source, limit=6):
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except (requests.RequestException, ET.ParseError) as exc:
        logger.info("Trend source %s unavailable: %s", source, exc)
        return []

    items = []
    for item in root.findall(".//item")[:limit]:
        title = _clean(item.findtext("title"))
        description = _clean(item.findtext("description"))
        if title:
            items.append({
                "title": title[:180],
                "context": re.sub(r"<[^>]+>", " ", description)[:240],
                "source": source,
            })
    return items


def get_trend_context():
    """Fetch public trend headlines only; never copy joke text or creator posts."""
    trends_url = "https://trends.google.com/trending/rss?geo=NP"
    news_query = quote('(Nepal OR Nepali) (meme OR comedy OR viral OR social media trend)')
    news_url = (
        "https://news.google.com/rss/search?q="
        + news_query
        + "&hl=en-NP&gl=NP&ceid=NP:en"
    )

    found = []
    found.extend(_fetch_rss(trends_url, "Google Trends Nepal", limit=6))
    found.extend(_fetch_rss(news_url, "Google News Nepal humour trends", limit=6))

    unique = []
    seen = set()
    for item in found:
        key = re.sub(r"[^\w]", "", item["title"].lower())
        if key and key not in seen:
            seen.add(key)
            unique.append(item)

    return {
        "items": unique[:MAX_ITEMS],
        "sources_checked": ["Google Trends Nepal RSS", "Google News RSS (Nepal humour query)"],
        "status": "live trends found" if unique else "trend feeds unavailable; using evergreen Nepali humour themes",
    }
