"""Companies House UK scraper — searches UK official corporate register.

Endpoint: GET https://api.company-information.service.gov.uk/search/officers?q=<name>

Searches by officer name (directors, secretaries, persons of significant
control). UK primary source — richer than opencorporates for UK-specific
data (filing history, charges, PSCs). Free with API key, 600 req/5min.

API key: workspace-level setting `companies_house_uk_api_key`. Operator
registers via developer.company-information.service.gov.uk and adds to
workspace via UI. Without a key this scraper returns [].

Auth: HTTP Basic, API key as username, empty password.
"""
import logging
from difflib import SequenceMatcher

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

COMPANIES_HOUSE_URL = "https://api.company-information.service.gov.uk/search/officers"
REQUEST_TIMEOUT = 12
MAX_RESULTS = 15
MIN_CONFIDENCE = 0.70


def _name_similarity(name_a: str, name_b: str) -> float:
    """Same shape as sec_edgar_search and opencorporates_officers."""
    if not name_a or not name_b:
        return 0.0
    a = name_a.lower().strip().replace(",", "").replace(".", "")
    b = name_b.lower().strip().replace(",", "").replace(".", "")
    if a == b:
        return 1.0
    parts_a = set(a.split())
    parts_b = set(b.split())
    if parts_a == parts_b:
        return 0.95
    common = parts_a & parts_b
    if len(common) >= 2:
        return max(0.80, SequenceMatcher(None, a, b).ratio())
    return SequenceMatcher(None, a, b).ratio()


def search_companies_house_uk(primary_name: str, api_key: str | None = None) -> list[dict]:
    """
    Search Companies House UK officers by name.
    Returns empty list if api_key not provided (no anonymous access).
    """
    if not api_key:
        logger.debug("Companies House UK: no api_key, skipping")
        return []
    if not primary_name or len(primary_name.strip()) < 4:
        return []

    params = {"q": primary_name, "items_per_page": MAX_RESULTS}
    auth = HTTPBasicAuth(api_key, "")

    try:
        resp = requests.get(
            COMPANIES_HOUSE_URL, params=params, auth=auth,
            timeout=REQUEST_TIMEOUT,
            headers={"Accept": "application/json"},
        )
        if resp.status_code == 401:
            logger.warning("Companies House UK: 401 unauthorized — check api_key")
            return []
        if resp.status_code == 429:
            logger.warning("Companies House UK: rate limited (429)")
            return []
        if resp.status_code != 200:
            logger.warning("Companies House UK: HTTP %d for '%s'", resp.status_code, primary_name)
            return []

        data = resp.json()
        items = data.get("items") or []
        if not items:
            return []

        findings = []
        for item in items[:MAX_RESULTS]:
            officer_name = item.get("title") or ""
            confidence = _name_similarity(officer_name, primary_name)
            if confidence < MIN_CONFIDENCE:
                continue

            self_link = (item.get("links") or {}).get("self") or ""
            url = f"https://find-and-update.company-information.service.gov.uk{self_link}" if self_link else ""
            address = item.get("address_snippet") or ""
            appointment_count = item.get("appointment_count")
            dob = item.get("date_of_birth") or {}
            dob_str = f"{dob.get('month', '?'):02}/{dob.get('year', '?')}" if dob else ""

            findings.append({
                "title": f"UK officer: {officer_name}",
                "url": url,
                "description": f"{appointment_count} appointment(s) — {address}".strip(" —"),
                "severity": "medium",
                "indicator_type": "legal_record",
                "indicator_value": self_link or officer_name,
                "confidence": round(confidence, 3),
                "data": {
                    "scraper": "companies_house_uk",
                    "officer_name": officer_name,
                    "address_snippet": address,
                    "appointment_count": appointment_count,
                    "date_of_birth": dob_str,
                    "kind": item.get("kind"),
                    "matched_name": officer_name,
                    "match_confidence": round(confidence, 3),
                    "jurisdiction": "UK",
                    "source_type": "corporate_officer",
                },
            })

        logger.info(
            "Companies House UK: found %d officers for '%s' (from %d items)",
            len(findings), primary_name, len(items),
        )
        return findings

    except requests.exceptions.Timeout:
        logger.warning("Companies House UK: timeout for '%s'", primary_name)
        return []
    except requests.exceptions.RequestException as e:
        logger.warning("Companies House UK: request error for '%s': %s", primary_name, e)
        return []
    except (ValueError, KeyError) as e:
        logger.warning("Companies House UK: parse error for '%s': %s", primary_name, e)
        return []
