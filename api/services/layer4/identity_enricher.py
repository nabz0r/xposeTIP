"""Identity Enricher — re-queries identity APIs with discovered real name.

Called after profile aggregation when:
1. We found a primary_name from scanners
2. The identity_estimation is empty or based on a non-name email prefix
"""
import logging
import re

import httpx

logger = logging.getLogger(__name__)

GENDERIZE_URL = "https://api.genderize.io/?name={name}"
AGIFY_URL = "https://api.agify.io/?name={name}"
NATIONALIZE_URL = "https://api.nationalize.io/?name={name}"


def enrich_identity(profile: dict, email: str) -> dict:
    """Re-query identity APIs if we have a better name than email prefix.

    Returns updated identity_estimation dict.
    """
    est = dict(profile.get("identity_estimation", {}))
    primary_name = profile.get("primary_name", "")

    if not primary_name:
        return est

    # Extract first name from discovered name
    parts = primary_name.strip().split()
    discovered_first = parts[0].lower() if parts else ""

    # Extract first name from email
    prefix = email.split("@")[0] if "@" in email else email
    cleaned = re.sub(r"\d+", "", prefix)
    email_parts = re.split(r"[._\-]", cleaned)
    email_first = email_parts[0].lower() if email_parts else ""

    # Only re-query if discovered name is different from email prefix
    if discovered_first == email_first:
        return est

    if len(discovered_first) < 2:
        return est

    logger.info("Identity enrichment: re-querying with '%s' (was '%s')", discovered_first, email_first)

    try:
        client = httpx.Client(timeout=10)

        # Genderize
        try:
            resp = client.get(GENDERIZE_URL.format(name=discovered_first))
            if resp.status_code == 200:
                data = resp.json()
                if data.get("gender"):
                    est["gender"] = data["gender"]
                    est["gender_probability"] = data.get("probability")
                    est["gender_source"] = f"genderize.io (name: {discovered_first})"
        except Exception:
            logger.debug("Genderize re-query failed")

        # Agify
        try:
            resp = client.get(AGIFY_URL.format(name=discovered_first))
            if resp.status_code == 200:
                data = resp.json()
                if data.get("age"):
                    est["age"] = data["age"]
                    est["age_sample_count"] = data.get("count", 0)
                    est["age_source"] = f"agify.io (name: {discovered_first})"
        except Exception:
            logger.debug("Agify re-query failed")

        # Nationalize
        try:
            resp = client.get(NATIONALIZE_URL.format(name=discovered_first))
            if resp.status_code == 200:
                data = resp.json()
                countries = data.get("country", [])
                if countries:
                    est["nationalities"] = [
                        {"country_code": c["country_id"], "probability": c["probability"]}
                        for c in countries[:3]
                    ]
                    est["nationality_source"] = f"nationalize.io (name: {discovered_first})"
        except Exception:
            logger.debug("Nationalize re-query failed")

        client.close()

    except Exception:
        logger.exception("Identity enrichment failed")

    return est
