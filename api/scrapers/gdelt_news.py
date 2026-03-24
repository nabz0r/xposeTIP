"""GDELT News Search scraper.

Searches the GDELT Global Knowledge Graph for news articles mentioning a person.
Free API, no key required, covers 100+ languages, updated every 15 minutes.

API docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-v2-updated-documentation/
"""
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import requests

logger = logging.getLogger(__name__)

GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
MAX_RESULTS = 10
REQUEST_TIMEOUT = 15


def search_gdelt_news(name: str, domain: str | None = None) -> list[dict]:
    """Search GDELT for news articles mentioning a person.

    Args:
        name: Full name to search (e.g., "Benjamin Lavault")
        domain: Optional email domain to add context (e.g., "threatconnect.com")

    Returns:
        List of article dicts with title, url, source, date, description.
    """
    if not name or len(name.strip()) < 4:
        return []

    # Build query: quoted name for exact match
    query = f'"{name}"'

    # Add domain context if corporate email
    if domain and "." in domain:
        company = domain.split(".")[0]
        if len(company) > 3:
            query += f" {company}"

    params = {
        "query": query,
        "mode": "ArtList",
        "maxrecords": str(MAX_RESULTS),
        "format": "json",
        "sort": "DateDesc",
        "timespan": "5y",  # Last 5 years
    }

    try:
        resp = None
        for attempt in range(2):
            resp = requests.get(
                GDELT_API_URL,
                params=params,
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": "xposeTIP/1.0"},
            )

            if resp.status_code == 429:
                if attempt == 0:
                    logger.info("GDELT: 429 rate limited — retrying in 5s")
                    import time
                    time.sleep(5)
                    continue
                else:
                    logger.warning("GDELT: 429 — giving up after retry")
                    return []

            if resp.status_code != 200:
                logger.warning("GDELT: HTTP %d for query '%s'", resp.status_code, name)
                return []

            break  # Success

        if resp is None or resp.status_code != 200:
            return []

        data = resp.json()
        articles = data.get("articles", [])

        # Retry without quotes if quoted search returned 0 results
        # (rare names sometimes need broader matching)
        if not articles and '"' in params["query"]:
            logger.debug("GDELT: No results with quotes for '%s' — retrying unquoted", name)
            unquoted_query = name
            if domain and "." in domain:
                company = domain.split(".")[0]
                if len(company) > 3:
                    unquoted_query += f" {company}"
            params["query"] = unquoted_query
            resp2 = requests.get(
                GDELT_API_URL, params=params, timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": "xposeTIP/1.0"},
            )
            if resp2.status_code == 200:
                data = resp2.json()
                articles = data.get("articles", [])

        if not articles:
            logger.debug("GDELT: No articles found for '%s'", name)
            return []

        results = []
        seen_titles = set()

        for art in articles[:MAX_RESULTS]:
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
            date_str = art.get("seendate", "")
            pub_date = None
            if date_str:
                try:
                    pub_date = datetime.strptime(date_str[:14], "%Y%m%d%H%M%S").isoformat()
                except (ValueError, IndexError):
                    pub_date = date_str[:8] if len(date_str) >= 8 else None

            source_domain = art.get("domain", "")
            language = art.get("language", "")
            source_country = art.get("sourcecountry", "")

            # Build snippet from socialimage alt or title
            snippet = art.get("socialimage", "")
            if snippet and len(snippet) > 200:
                snippet = ""

            results.append({
                "title": title,
                "url": url,
                "source": source_domain,
                "date": pub_date,
                "description": f"{title} — {source_domain}",
                "language": language,
                "country": source_country,
                "data": {
                    "source_domain": source_domain,
                    "language": language,
                    "source_country": source_country,
                    "pub_date": pub_date,
                    "gdelt_url": url,
                },
                "severity": "info",
            })

        logger.info("GDELT: Found %d articles for '%s'", len(results), name)
        return results

    except requests.exceptions.Timeout:
        logger.warning("GDELT: Timeout for query '%s'", name)
        return []
    except requests.exceptions.RequestException as e:
        logger.warning("GDELT: Request error for '%s': %s", name, e)
        return []
    except Exception:
        logger.exception("GDELT: Unexpected error for '%s'", name)
        return []
