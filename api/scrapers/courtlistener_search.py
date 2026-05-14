"""Courtlistener scraper — searches US federal court records (PACER + RECAP).

Endpoint: GET https://www.courtlistener.com/api/rest/v4/search/?type=r&party_name=...

Searches RECAP archive (Free Law Project's PACER mirror) for federal cases
where the target is a named party. US jurisdiction only — does not cover
state courts in any depth, and no coverage outside the US.

Token-based auth strongly recommended (anonymous rate limits unusable).
Free tier API key: https://www.courtlistener.com/sign-in/
"""
import logging
import time

import requests

logger = logging.getLogger(__name__)

REDIS_DISABLE_KEY = "courtlistener:disabled"
REDIS_DISABLE_TTL = 3600

COURTLISTENER_URL = "https://www.courtlistener.com/api/rest/v4/search/"
REQUEST_TIMEOUT = 15
MIN_NAME_CONFIDENCE = 0.70
MAX_RESULTS = 25  # cap per call — pagination disabled for MVP


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
        r.setex(REDIS_DISABLE_KEY, REDIS_DISABLE_TTL, "401")
        logger.warning("Courtlistener disabled for %ds after 401", REDIS_DISABLE_TTL)
    except Exception:
        pass


def _compute_name_confidence(case_name: str, party_field: str, target_name: str) -> float:
    """Compute name match confidence.

    Courtlistener returns caseName like "Smith v. Doe" and a party field.
    We do best-effort substring matching with token overlap.
    """
    if not target_name:
        return 0.0
    target_lower = target_name.lower().strip()
    target_parts = set(target_lower.split())
    if not target_parts:
        return 0.0

    best = 0.0
    for haystack in (party_field or "", case_name or ""):
        h_lower = haystack.lower()
        if target_lower in h_lower:
            best = max(best, 0.95)
            continue
        h_parts = set(h_lower.replace(",", "").replace(".", "").split())
        overlap = len(target_parts & h_parts)
        if overlap >= len(target_parts):
            best = max(best, 0.85)
        elif overlap >= 1:
            best = max(best, overlap / max(len(target_parts), len(h_parts)) * 0.7)
    return best


def search_courtlistener(primary_name: str, api_key: str | None = None) -> list[dict]:
    """Search Courtlistener RECAP for federal court cases by party name.

    Args:
        primary_name: Full name to search
        api_key: Courtlistener API token (strongly recommended)

    Returns:
        List of finding dicts ready for storage.
    """
    if not primary_name or len(primary_name.strip()) < 4:
        return []
    if _is_disabled():
        logger.debug("Courtlistener: skipping — disabled after 401")
        return []

    headers = {"User-Agent": "xposeTIP/1.0"}
    if api_key:
        headers["Authorization"] = f"Token {api_key}"

    params = {
        "type": "r",
        "party_name": primary_name,
    }

    try:
        resp = requests.get(
            COURTLISTENER_URL,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )

        if resp.status_code == 401:
            logger.warning(
                "Courtlistener: 401 Unauthorized — API token required. "
                "Configure 'courtlistener_api_key' in Settings → API Keys. "
                "Get a free token at https://www.courtlistener.com/sign-in/"
            )
            _set_disabled()
            return []

        if resp.status_code == 429:
            logger.warning("Courtlistener: rate limited (429), waiting 10s...")
            time.sleep(10)
            resp = requests.get(
                COURTLISTENER_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code == 429:
                logger.warning("Courtlistener: still rate limited after retry")
                return []

        if resp.status_code >= 500:
            logger.warning("Courtlistener: server error %d", resp.status_code)
            return []
        if resp.status_code != 200:
            logger.warning("Courtlistener: HTTP %d for '%s'", resp.status_code, primary_name)
            return []

        data = resp.json()
        results = data.get("results", []) or []
        if not results:
            logger.debug("Courtlistener: no matches for '%s'", primary_name)
            return []

        findings = []
        for r in results[:MAX_RESULTS]:
            case_name = r.get("caseName") or r.get("caseNameFull") or ""
            party_field = r.get("party") or r.get("party_name") or ""
            confidence = _compute_name_confidence(case_name, party_field, primary_name)
            if confidence < MIN_NAME_CONFIDENCE:
                continue

            absolute_url = r.get("absolute_url") or ""
            url = f"https://www.courtlistener.com{absolute_url}" if absolute_url.startswith("/") else absolute_url
            docket_number = r.get("docketNumber") or ""
            court = r.get("court") or r.get("court_id") or ""
            date_filed = r.get("dateFiled") or ""

            findings.append({
                "title": f"Court case: {case_name}" if case_name else "Court case (US federal)",
                "url": url,
                "description": f"{court} — {docket_number}" if docket_number else court,
                "severity": "medium",
                "indicator_type": "legal_record",
                "indicator_value": docket_number or r.get("docket_id") or "",
                "confidence": round(confidence, 3),
                "data": {
                    "scraper": "courtlistener_search",
                    "case_name": case_name,
                    "court": court,
                    "court_id": r.get("court_id"),
                    "docket_number": docket_number,
                    "docket_id": r.get("docket_id"),
                    "date_filed": date_filed,
                    "judge": r.get("judge") or "",
                    "nature_of_suit": r.get("nature_of_suit") or "",
                    "cause": r.get("cause") or "",
                    "jurisdiction": "US federal",
                    "source_type": "legal_record",
                    "match_confidence": round(confidence, 3),
                },
            })

        logger.info(
            "Courtlistener: found %d legal records for '%s' (from %d results)",
            len(findings), primary_name, len(results),
        )
        return findings

    except requests.exceptions.Timeout:
        logger.warning("Courtlistener: timeout for '%s'", primary_name)
        return []
    except requests.exceptions.RequestException as e:
        logger.warning("Courtlistener: request error for '%s': %s", primary_name, e)
        return []
    except Exception:
        logger.exception("Courtlistener: unexpected error for '%s'", primary_name)
        return []
