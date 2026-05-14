"""UK Gazette scraper — UK official public record (London/Edinburgh/Belfast).

Endpoint: GET https://www.thegazette.co.uk/all-notices/notice/data.json?text=<name>

Searches all notices: personal insolvency, bankruptcy orders, deceased
estates, probate, partnership dissolutions, restrictions orders.
Crown copyright, Open Government Licence v3.0. No authentication required
but rate-limited (1 req / 10s per robots.txt).
"""
import logging
import time

import requests

logger = logging.getLogger(__name__)

REDIS_DISABLE_KEY = "uk_gazette:disabled"
REDIS_DISABLE_TTL = 3600

GAZETTE_URL = "https://www.thegazette.co.uk/all-notices/notice/data.json"
REQUEST_TIMEOUT = 20
MIN_NAME_CONFIDENCE = 0.75  # higher than BODACC — Gazette has more name overlap noise
MAX_RESULTS = 25

# Severity mapping for Gazette category codes
# (categorycode is a 1-digit prefix; first 2 digits identify subcategory)
# 11 = Personal insolvency, 17 = Companies House related, 19 = Deceased estates
CATEGORY_SEVERITY = {
    "11": "high",    # Personal insolvency / bankruptcy
    "17": "low",     # Companies House
    "19": "info",    # Deceased estates
    "20": "medium",  # Partnerships
    "29": "info",    # Awards / honors
}


def _is_disabled() -> bool:
    try:
        from api.config import settings
        import redis
        r = redis.from_url(settings.REDIS_URL)
        return r.exists(REDIS_DISABLE_KEY) > 0
    except Exception:
        return False


def _set_disabled():
    try:
        from api.config import settings
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.setex(REDIS_DISABLE_KEY, REDIS_DISABLE_TTL, "blocked")
        logger.warning("UK Gazette disabled for %ds", REDIS_DISABLE_TTL)
    except Exception:
        pass


def _compute_name_confidence(entry: dict, target_name: str) -> float:
    """Score how confidently a Gazette entry matches our target name."""
    if not target_name:
        return 0.0
    target_lower = target_name.lower().strip()
    target_parts = set(target_lower.split())
    if not target_parts or len(target_parts) < 2:
        # Single-token names are too noisy in Gazette
        return 0.0

    # Combine fields that may carry name
    haystack_pieces = []
    for key in ("title", "description", "content", "name"):
        v = entry.get(key)
        if v:
            haystack_pieces.append(str(v).lower())
    haystack = " | ".join(haystack_pieces)
    if not haystack:
        return 0.0

    if target_lower in haystack:
        return 0.95
    h_parts = set(haystack.replace(",", " ").replace(".", " ").split())
    overlap = len(target_parts & h_parts)
    if overlap >= len(target_parts):
        return 0.85
    return 0.0  # require all name parts to match (Gazette is noisy)


def search_uk_gazette(primary_name: str) -> list[dict]:
    """Search The Gazette for UK official record notices mentioning a person.

    Args:
        primary_name: full name (must be ≥2 tokens, otherwise too noisy)

    Returns:
        List of finding dicts ready for storage.
    """
    if not primary_name or len(primary_name.strip()) < 4:
        return []
    if len(primary_name.strip().split()) < 2:
        logger.debug("UK Gazette: name '%s' too short (need ≥2 tokens)", primary_name)
        return []
    if _is_disabled():
        logger.debug("UK Gazette: skipping — disabled")
        return []

    headers = {
        "User-Agent": "xposeTIP/1.0 (https://github.com/nabz0r/xposeTIP)",
        "Accept": "application/json",
    }
    # Quote name to favor exact phrase match
    params = {
        "text": f'"{primary_name}"',
        "results-page-size": MAX_RESULTS,
    }

    try:
        resp = requests.get(
            GAZETTE_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT,
        )

        if resp.status_code == 403:
            logger.warning(
                "UK Gazette: 403 forbidden — User-Agent may be blocked. "
                "Disabling 1h."
            )
            _set_disabled()
            return []

        if resp.status_code == 429:
            logger.warning("UK Gazette: rate limited (429), waiting 12s...")
            time.sleep(12)
            resp = requests.get(
                GAZETTE_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT,
            )

        if resp.status_code >= 500:
            logger.warning("UK Gazette: server error %d", resp.status_code)
            return []
        if resp.status_code != 200:
            logger.warning("UK Gazette: HTTP %d for '%s'", resp.status_code, primary_name)
            return []

        data = resp.json()
        entries = data.get("entry", []) or []
        if not entries:
            logger.debug("UK Gazette: no matches for '%s'", primary_name)
            return []

        findings = []
        for entry in entries:
            confidence = _compute_name_confidence(entry, primary_name)
            if confidence < MIN_NAME_CONFIDENCE:
                continue

            category_code = str(entry.get("category_code") or entry.get("categorycode") or "")[:2]
            severity = CATEGORY_SEVERITY.get(category_code, "medium")
            title = entry.get("title") or "UK Gazette notice"
            notice_id = entry.get("id") or entry.get("guid") or ""
            link = entry.get("link") or notice_id
            if isinstance(link, dict):
                link = link.get("@href") or ""
            edition = entry.get("publication") or entry.get("edition") or "London Gazette"
            published = entry.get("published") or entry.get("publication_date") or ""

            findings.append({
                "title": f"{edition}: {title}",
                "url": link or notice_id,
                "description": entry.get("description") or "",
                "severity": severity,
                "indicator_type": "legal_record",
                "indicator_value": notice_id,
                "confidence": round(confidence, 3),
                "data": {
                    "scraper": "uk_gazette_search",
                    "edition": edition,
                    "category_code": category_code,
                    "category": entry.get("category") or "",
                    "publication_date": published,
                    "issue": entry.get("issue") or "",
                    "notice_id": notice_id,
                    "jurisdiction": "UK",
                    "source_type": "legal_record",
                    "match_confidence": round(confidence, 3),
                },
            })

        logger.info(
            "UK Gazette: found %d notices for '%s' (from %d entries)",
            len(findings), primary_name, len(entries),
        )
        return findings

    except requests.exceptions.Timeout:
        logger.warning("UK Gazette: timeout for '%s'", primary_name)
        return []
    except requests.exceptions.RequestException as e:
        logger.warning("UK Gazette: request error for '%s': %s", primary_name, e)
        return []
    except Exception:
        logger.exception("UK Gazette: unexpected error for '%s'", primary_name)
        return []
