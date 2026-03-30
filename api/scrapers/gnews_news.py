"""GNews.io scraper — recent news search by person name.

API: https://gnews.io/api/v4/search?q="firstname+lastname"&lang=en&max=10&apikey=KEY

Free tier: 100 requests/day, max 10 articles/request, 1-year archive.
Requires API key stored as 'gnews_api_key' in workspace settings.
"""
import logging
import re
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

GNEWS_API_URL = "https://gnews.io/api/v4/search"
MAX_ARTICLES = 10
REQUEST_TIMEOUT = 12

# GNews language codes
GNEWS_LANG_MAP = {
    "fr": {"lang": "fr"},
    "de": {"lang": "de"},
    "es": {"lang": "es"},
    "it": {"lang": "it"},
    "pt": {"lang": "pt"},
    "nl": {"lang": "nl"},
    "en": {"lang": "en"},
}


def search_gnews(
    name: str,
    api_key: str,
    lang: str = "en",
    country: str | None = None,
    context: str | None = None,
) -> list[dict]:
    """Search GNews.io for recent news articles about a person.

    Args:
        name: Full name to search (e.g., "Mario Grotz")
        api_key: GNews.io API key
        lang: Language code (en, fr, de, etc.)
        country: Optional country code filter (us, fr, de, lu, etc.)
        context: Optional context keywords (company, city) appended to query

    Returns:
        List of article dicts with title, url, source, date, description.
    """
    if not name or not api_key:
        return []

    # Exact name match via quotes, plus optional context keywords
    query = f'"{name}"'
    if context:
        query += f" {context}"

    params = {
        "q": query,
        "lang": lang,
        "max": str(MAX_ARTICLES),
        "sortby": "relevance",
        "apikey": api_key,
    }
    if country:
        params["country"] = country

    try:
        resp = requests.get(
            GNEWS_API_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "xposeTIP/1.0"},
        )

        if resp.status_code == 403:
            logger.error("GNews: Invalid or expired API key (HTTP 403)")
            return []
        if resp.status_code == 429:
            logger.warning("GNews: Rate limit exceeded (HTTP 429)")
            return []
        if resp.status_code != 200:
            logger.warning("GNews: HTTP %d for query '%s'", resp.status_code, name)
            return []

        data = resp.json()
        total = data.get("totalArticles", 0)
        articles = data.get("articles", [])

        if not articles:
            logger.debug("GNews: No articles for '%s' (lang=%s)", name, lang)
            return []

        results = []
        seen_titles = set()

        for art in articles[:MAX_ARTICLES]:
            title = (art.get("title") or "").strip()
            url = (art.get("url") or "").strip()

            if not title or not url:
                continue

            # Dedup by normalized title
            title_norm = re.sub(r'\s+', ' ', title.lower().strip())
            if title_norm in seen_titles:
                continue
            seen_titles.add(title_norm)

            # Parse date
            pub_date = art.get("publishedAt")
            if pub_date:
                try:
                    pub_date = datetime.fromisoformat(
                        pub_date.replace("Z", "+00:00")
                    ).isoformat()
                except (ValueError, TypeError):
                    pass

            source_info = art.get("source", {})
            source_name = source_info.get("name", "")
            source_url = source_info.get("url", "")
            source_domain = source_url.replace("https://", "").replace("http://", "").rstrip("/") if source_url else ""

            description = (art.get("description") or "").strip()
            content_snippet = (art.get("content") or "")[:500]
            image = art.get("image", "")

            results.append({
                "title": title,
                "url": url,
                "source": source_domain or source_name,
                "date": pub_date,
                "description": description or f"{title} — {source_name}",
                "language": lang,
                "country": country or "",
                "data": {
                    "source_domain": source_domain,
                    "source_name": source_name,
                    "language": lang,
                    "pub_date": pub_date,
                    "description": description,
                    "content_snippet": content_snippet[:300] if content_snippet else "",
                    "thumbnail": image,
                    "total_results": total,
                    "scraper": "gnews_news",
                },
                "severity": "info",
            })

        logger.info("GNews: Found %d articles for '%s' (lang=%s)", len(results), name, lang)
        return results

    except requests.exceptions.Timeout:
        logger.warning("GNews: Timeout for '%s'", name)
        return []
    except requests.exceptions.RequestException as e:
        logger.warning("GNews: Request error for '%s': %s", name, e)
        return []
    except Exception:
        logger.exception("GNews: Unexpected error for '%s'", name)
        return []
