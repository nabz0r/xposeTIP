"""OpenCorporates officer search — finds company directorships and roles.

Endpoint: GET https://api.opencorporates.com/v0.4/officers/search?q=Mario+Grotz

200M+ companies, 300M+ officers from 150+ jurisdictions.
Free: 500 req/month with API key, limited anonymous access without.
"""
import logging
from difflib import SequenceMatcher

import requests

logger = logging.getLogger(__name__)

OPENCORPORATES_URL = "https://api.opencorporates.com/v0.4/officers/search"
REQUEST_TIMEOUT = 12
MIN_CONFIDENCE = 0.60
MAX_RESULTS = 10
MAX_CORPORATE_FINDINGS = 8


def _name_similarity(name_a: str, name_b: str) -> float:
    """Compute name similarity using SequenceMatcher."""
    if not name_a or not name_b:
        return 0.0
    # Normalize: lowercase, strip, remove commas
    a = name_a.lower().strip().replace(",", "").replace(".", "")
    b = name_b.lower().strip().replace(",", "").replace(".", "")
    # Direct match
    if a == b:
        return 1.0
    # Parts match (handles "GROTZ, Mario" vs "Mario Grotz")
    parts_a = set(a.split())
    parts_b = set(b.split())
    if parts_a == parts_b:
        return 0.95
    # SequenceMatcher
    return SequenceMatcher(None, a, b).ratio()


def _compute_confidence(officer_name: str, target_name: str,
                        jurisdiction: str | None = None,
                        target_country: str | None = None,
                        is_active: bool = False) -> float:
    """Compute match confidence for an officer result.

    confidence = name_similarity × 0.5 + jurisdiction_bonus × 0.3 + active_bonus × 0.2
    """
    name_sim = _name_similarity(officer_name, target_name)

    # Jurisdiction bonus
    if target_country and jurisdiction:
        if jurisdiction.upper() == target_country.upper():
            jurisdiction_bonus = 0.3
        else:
            jurisdiction_bonus = 0.1
    else:
        jurisdiction_bonus = 0.1  # Unknown

    # Active bonus
    active_bonus = 0.2 if is_active else 0.1

    return name_sim * 0.5 + jurisdiction_bonus + active_bonus


def search_opencorporates(primary_name: str,
                          api_key: str | None = None,
                          target_country: str | None = None) -> list[dict]:
    """Search OpenCorporates for company officer roles.

    Args:
        primary_name: Full name to search
        api_key: Optional OpenCorporates API token
        target_country: ISO country code if known

    Returns:
        List of finding dicts ready for storage.
    """
    if not primary_name or len(primary_name.strip()) < 4:
        return []

    params = {
        "q": primary_name,
        "per_page": str(MAX_RESULTS),
    }
    if api_key:
        params["api_token"] = api_key

    try:
        resp = requests.get(
            OPENCORPORATES_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "xposeTIP/1.0"},
        )

        if resp.status_code == 401:
            logger.warning("OpenCorporates: Invalid API key (401), trying anonymous")
            params.pop("api_token", None)
            resp = requests.get(
                OPENCORPORATES_URL, params=params,
                timeout=REQUEST_TIMEOUT, headers={"User-Agent": "xposeTIP/1.0"},
            )

        if resp.status_code == 403:
            logger.warning("OpenCorporates: Quota exceeded (403)")
            return []
        if resp.status_code == 404:
            return []
        if resp.status_code >= 500:
            logger.warning("OpenCorporates: Server error %d", resp.status_code)
            return []
        if resp.status_code != 200:
            logger.warning("OpenCorporates: HTTP %d for '%s'", resp.status_code, primary_name)
            return []

        data = resp.json()
        results = data.get("results", {})
        officers = results.get("officers", [])

        if not officers:
            logger.debug("OpenCorporates: No officers found for '%s'", primary_name)
            return []

        findings = []
        seen_companies = set()  # For dedup: (company_number, jurisdiction)

        for item in officers[:MAX_RESULTS]:
            officer = item.get("officer", {})
            if not officer:
                continue

            officer_name = (officer.get("name") or "").strip()
            position = (officer.get("position") or "").strip()
            start_date = officer.get("start_date")
            end_date = officer.get("end_date")
            is_active = end_date is None
            occupation = officer.get("occupation", "")
            nationality = officer.get("nationality", "")

            company = officer.get("company", {}) or {}
            company_name = (company.get("name") or "").strip()
            company_number = company.get("company_number", "")
            jurisdiction = (company.get("jurisdiction_code") or "").lower()
            company_url = company.get("opencorporates_url", "")
            registered_address = company.get("registered_address", "")

            if not officer_name or not company_name:
                continue

            # Dedup: same company
            dedup_key = (company_number.lower(), jurisdiction)
            if dedup_key in seen_companies and company_number:
                continue
            if company_number:
                seen_companies.add(dedup_key)

            # Compute confidence
            confidence = _compute_confidence(
                officer_name, primary_name,
                jurisdiction=jurisdiction,
                target_country=target_country,
                is_active=is_active,
            )

            if confidence < MIN_CONFIDENCE:
                continue

            officer_id = officer.get("id", "")
            jurisdiction_upper = jurisdiction.upper() if jurisdiction else ""

            findings.append({
                "title": f"{position or 'Officer'} at {company_name} ({jurisdiction_upper})"[:255],
                "url": company_url or f"https://opencorporates.com/officers/{officer_id}",
                "description": f"{officer_name} — {position or 'Officer'} at {company_name}",
                "severity": "low",
                "indicator_type": "corporate_officer",
                "indicator_value": str(officer_id) if officer_id else company_url,
                "confidence": round(confidence, 3),
                "data": {
                    "scraper": "opencorporates_officers",
                    "officer_name": officer_name,
                    "officer_id": officer_id,
                    "position": position,
                    "company_name": company_name,
                    "company_number": company_number,
                    "jurisdiction": jurisdiction,
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_active": is_active,
                    "occupation": occupation,
                    "nationality": nationality,
                    "registered_address": registered_address,
                    "company_url": company_url,
                    "match_confidence": round(confidence, 3),
                    "match_type": "potential",
                    "source_type": "name_search",
                },
            })

        # Sort: active first, then by confidence
        findings.sort(key=lambda f: (
            -int(f["data"].get("is_active", False)),
            -f.get("confidence", 0),
        ))

        # Cap at MAX_CORPORATE_FINDINGS
        findings = findings[:MAX_CORPORATE_FINDINGS]

        logger.info("OpenCorporates: Found %d officer roles for '%s'", len(findings), primary_name)
        return findings

    except requests.exceptions.Timeout:
        logger.warning("OpenCorporates: Timeout for '%s'", primary_name)
        return []
    except requests.exceptions.RequestException as e:
        logger.warning("OpenCorporates: Request error for '%s': %s", primary_name, e)
        return []
    except Exception:
        logger.exception("OpenCorporates: Unexpected error for '%s'", primary_name)
        return []
