"""Interpol Red Notices API — direct search for wanted persons.

Endpoint: GET https://ws-public.interpol.int/notices/v1/red?name=Grotz&forename=Mario

Public API, no key needed. Provides photos, charges, and detailed info
that OpenSanctions may not include.

Only runs if OpenSanctions didn't already find an Interpol dataset match.
"""
import logging

import requests

logger = logging.getLogger(__name__)

INTERPOL_API_URL = "https://ws-public.interpol.int/notices/v1/red"
REQUEST_TIMEOUT = 12


def _split_name(full_name: str) -> tuple[str, str]:
    """Split full name into (first_name, last_name)."""
    parts = full_name.strip().split()
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    return full_name, ""


def _compute_interpol_confidence(notice: dict, primary_name: str,
                                  target_country: str | None = None,
                                  target_birth_year: int | None = None) -> float:
    """Compute match confidence for Interpol result.

    Base: 0.80 (exact name match from Interpol)
    + 0.10 if nationality matches
    + 0.10 if birth year matches
    """
    confidence = 0.80

    # Country bonus
    if target_country:
        nationalities = notice.get("nationalities", [])
        if isinstance(nationalities, list):
            nat_codes = [n.upper() if isinstance(n, str) else "" for n in nationalities]
            if target_country.upper() in nat_codes:
                confidence += 0.10

    # Birth year bonus
    if target_birth_year:
        dob = notice.get("date_of_birth")
        if dob and isinstance(dob, str):
            try:
                notice_year = int(dob.split("/")[0]) if "/" in dob else int(dob[:4])
                if abs(notice_year - target_birth_year) <= 2:
                    confidence += 0.10
            except (ValueError, IndexError):
                pass

    return min(confidence, 1.0)


def search_interpol_red_notices(primary_name: str,
                                 target_country: str | None = None,
                                 target_birth_year: int | None = None) -> list[dict]:
    """Search Interpol Red Notices for wanted persons.

    Args:
        primary_name: Full name to search
        target_country: ISO country code if known
        target_birth_year: Estimated birth year if known

    Returns:
        List of finding dicts ready for storage.
    """
    if not primary_name or len(primary_name.strip()) < 4:
        return []

    first_name, last_name = _split_name(primary_name)
    if not last_name:
        return []

    params = {
        "forename": first_name,
        "name": last_name,
        "resultPerPage": "5",
    }

    try:
        resp = requests.get(
            INTERPOL_API_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; xposeTIP/1.0; security research)",
                "Accept": "application/json",
            },
        )

        if resp.status_code == 403:
            logger.warning("Interpol: 403 Forbidden — may be geo-restricted. Skipping.")
            return []
        if resp.status_code == 429:
            logger.warning("Interpol: Rate limited (429)")
            return []
        if resp.status_code != 200:
            logger.warning("Interpol: HTTP %d for '%s'", resp.status_code, primary_name)
            return []

        data = resp.json()
        total = data.get("total", 0)
        embedded = data.get("_embedded", {})
        notices = embedded.get("notices", [])

        if not notices:
            logger.debug("Interpol: No red notices for '%s'", primary_name)
            return []

        findings = []
        for notice in notices[:5]:
            forename = (notice.get("forename") or "").strip()
            surname = (notice.get("name") or "").strip()
            caption = f"{forename} {surname}".strip()

            # Verify name match
            name_lower = primary_name.lower()
            notice_lower = caption.lower()
            notice_parts = set(notice_lower.replace(",", "").split())
            target_parts = set(name_lower.split())

            # Must have at least partial name overlap
            overlap = len(target_parts & notice_parts)
            if overlap < 1:
                continue

            confidence = _compute_interpol_confidence(
                notice, primary_name, target_country, target_birth_year
            )

            entity_id = notice.get("entity_id", "")
            charge = (notice.get("charge") or "").strip()
            nationalities = notice.get("nationalities", [])
            dob = notice.get("date_of_birth", "")
            sex = "Male" if notice.get("sex_id") == 1 else "Female" if notice.get("sex_id") == 2 else ""

            # Extract URLs
            links = notice.get("_links", {})
            notice_url = links.get("self", {}).get("href", "")
            thumbnail_url = links.get("thumbnail", {}).get("href", "")

            findings.append({
                "title": f"Interpol Red Notice: {caption}",
                "url": notice_url or f"https://www.interpol.int/en/How-we-work/Notices/Red-Notices",
                "description": charge[:500] if charge else f"Interpol Red Notice for {caption}",
                "severity": "critical",
                "indicator_type": "sanctions_match",
                "indicator_value": entity_id or f"interpol-{surname}-{forename}".lower(),
                "confidence": round(confidence, 3),
                "data": {
                    "scraper": "interpol_red_notices",
                    "entity_id": entity_id,
                    "caption": caption,
                    "datasets": ["interpol_red_notices"],
                    "dataset_labels": ["Interpol Red Notices"],
                    "match_confidence": round(confidence, 3),
                    "match_type": "potential",
                    "source_type": "name_search",
                    "topics": ["wanted"],
                    "subtype": "interpol_red_notice",
                    "charge": charge,
                    "nationalities": nationalities,
                    "date_of_birth": dob,
                    "sex": sex,
                    "notice_url": notice_url,
                    "thumbnail_url": thumbnail_url,
                    "country_of_birth": notice.get("country_of_birth_id", ""),
                },
            })

        logger.info("Interpol: Found %d red notices for '%s'", len(findings), primary_name)
        return findings

    except requests.exceptions.Timeout:
        logger.warning("Interpol: Timeout for '%s'", primary_name)
        return []
    except requests.exceptions.RequestException as e:
        logger.warning("Interpol: Request error for '%s': %s", primary_name, e)
        return []
    except Exception:
        logger.exception("Interpol: Unexpected error for '%s'", primary_name)
        return []
