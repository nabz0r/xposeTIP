"""Google News RSS scraper — free, unlimited, recent news (~30 days).

URL: https://news.google.com/rss/search?q=%22Mario+Grotz%22&hl=en&gl=US&ceid=US:en

No API key required. Returns RSS XML. ~30 days of results.
Uses Option B: store Google redirect URL, no redirect resolution.
"""
import logging
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import requests

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
MAX_ARTICLES = 10  # Store max 5, but parse more for dedup margin
MAX_STORED = 5     # Max articles stored per target from RSS
REQUEST_TIMEOUT = 12

# Google News RSS locale codes
GOOGLE_NEWS_LOCALE_MAP = {
    "fr": {"hl": "fr", "gl": "FR", "ceid": "FR:fr"},
    "de": {"hl": "de", "gl": "DE", "ceid": "DE:de"},
    "es": {"hl": "es", "gl": "ES", "ceid": "ES:es"},
    "it": {"hl": "it", "gl": "IT", "ceid": "IT:it"},
    "pt": {"hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419"},
    "nl": {"hl": "nl", "gl": "NL", "ceid": "NL:nl"},
    "en": {"hl": "en", "gl": "US", "ceid": "US:en"},
}


def search_google_news_rss(
    name: str,
    lang: str = "en",
    context: str | None = None,
) -> list[dict]:
    """Search Google News RSS for recent articles mentioning a person.

    Args:
        name: Full name to search (e.g., "Mario Grotz")
        lang: Language code (en, fr, de, etc.)
        context: Optional context keywords (company, city) appended to query

    Returns:
        List of article dicts with title, url, source, date, description.
    """
    if not name or len(name.strip()) < 4:
        return []

    try:
        import feedparser
    except ImportError:
        logger.warning("Google News RSS: feedparser not installed")
        return []

    # Build URL with quoted name + optional context keywords
    query = f'"{name}"'
    if context:
        query += f" {context}"
    locale = GOOGLE_NEWS_LOCALE_MAP.get(lang, GOOGLE_NEWS_LOCALE_MAP["en"])

    params = {
        "q": query,
        "hl": locale["hl"],
        "gl": locale["gl"],
        "ceid": locale["ceid"],
    }

    url = f"{GOOGLE_NEWS_RSS_URL}?q={quote_plus(query)}&hl={locale['hl']}&gl={locale['gl']}&ceid={locale['ceid']}"

    try:
        resp = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; xposeTIP/1.0)",
                "Accept": "application/rss+xml, application/xml, text/xml",
            },
        )

        if resp.status_code == 429:
            logger.warning("Google News RSS: Rate limited (HTTP 429)")
            return []
        if resp.status_code != 200:
            logger.warning("Google News RSS: HTTP %d for '%s'", resp.status_code, name)
            return []

        feed = feedparser.parse(resp.text)

        if not feed.entries:
            logger.debug("Google News RSS: No entries for '%s' (lang=%s)", name, lang)
            return []

        results = []
        seen_titles = set()

        for entry in feed.entries[:MAX_ARTICLES]:
            raw_title = (entry.get("title") or "").strip()
            if not raw_title:
                continue

            # Google News format: "Headline - Source Name"
            # Split on last " - " to extract source
            title = raw_title
            source_name = ""
            if " - " in raw_title:
                parts = raw_title.rsplit(" - ", 1)
                title = parts[0].strip()
                source_name = parts[1].strip() if len(parts) > 1 else ""

            # Dedup by normalized title
            title_norm = re.sub(r'\s+', ' ', title.lower().strip())
            if title_norm in seen_titles:
                continue
            seen_titles.add(title_norm)

            # URL — Option B: store Google redirect URL
            url = entry.get("link", "")

            # Parse date (RFC 822)
            pub_date = None
            if entry.get("published"):
                try:
                    pub_date = parsedate_to_datetime(entry["published"]).isoformat()
                except Exception:
                    pub_date = entry.get("published")

            # Source from <source> tag if available
            source_info = entry.get("source", {})
            if hasattr(source_info, "get"):
                source_href = source_info.get("href", "")
                if not source_name and source_info.get("value"):
                    source_name = source_info["value"]
            else:
                source_href = ""

            source_domain = source_href.replace("https://", "").replace("http://", "").rstrip("/") if source_href else ""

            description = (entry.get("summary") or entry.get("description") or "").strip()
            # Strip HTML tags from description
            description = re.sub(r'<[^>]+>', '', description).strip()

            results.append({
                "title": title,
                "url": url,
                "source": source_domain or source_name,
                "date": pub_date,
                "description": description or f"{title} — {source_name}",
                "language": lang,
                "country": "",
                "data": {
                    "source_domain": source_domain,
                    "source_name": source_name,
                    "language": lang,
                    "pub_date": pub_date,
                    "google_news_url": url,
                    "scraper": "google_news_rss",
                },
                "severity": "info",
            })

        # Cap at MAX_STORED
        results = results[:MAX_STORED]

        logger.info("Google News RSS: Found %d articles for '%s' (lang=%s)", len(results), name, lang)
        return results

    except requests.exceptions.Timeout:
        logger.warning("Google News RSS: Timeout for '%s'", name)
        return []
    except requests.exceptions.RequestException as e:
        logger.warning("Google News RSS: Request error for '%s': %s", name, e)
        return []
    except Exception:
        logger.exception("Google News RSS: Unexpected error for '%s'", name)
        return []
