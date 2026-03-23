"""Identity Enricher — re-queries identity APIs with discovered real name.

Called after profile aggregation when:
1. We found a primary_name from scanners
2. The identity_estimation is empty or based on a non-name email prefix
"""
import logging
import re
import time

import httpx

logger = logging.getLogger(__name__)

GENDERIZE_URL = "https://api.genderize.io/?name={name}"
AGIFY_URL = "https://api.agify.io/?name={name}"
NATIONALIZE_URL = "https://api.nationalize.io/?name={name}"

# Simple in-memory cache (reset per worker restart)
_identity_cache = {}
CACHE_TTL = 86400  # 24 hours


def _get_cached(name: str, api: str):
    key = f"{api}:{name.lower()}"
    entry = _identity_cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["data"]
    return None


def _set_cache(name: str, api: str, data):
    key = f"{api}:{name.lower()}"
    _identity_cache[key] = {"data": data, "ts": time.time()}


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
        cached = _get_cached(discovered_first, "genderize")
        if cached is not None:
            est.update(cached)
        else:
            try:
                time.sleep(0.5)  # Rate limit: max 2 req/sec
                resp = client.get(GENDERIZE_URL.format(name=discovered_first))
                if resp.status_code == 200:
                    data = resp.json()
                    result = {}
                    if data.get("gender"):
                        result["gender"] = data["gender"]
                        result["gender_probability"] = data.get("probability")
                        result["gender_source"] = f"genderize.io (name: {discovered_first})"
                    est.update(result)
                    _set_cache(discovered_first, "genderize", result)
                elif resp.status_code == 429:
                    logger.warning("Genderize rate limited, skipping")
            except Exception:
                logger.debug("Genderize re-query failed")

        # Agify
        cached = _get_cached(discovered_first, "agify")
        if cached is not None:
            est.update(cached)
        else:
            try:
                time.sleep(0.5)
                resp = client.get(AGIFY_URL.format(name=discovered_first))
                if resp.status_code == 200:
                    data = resp.json()
                    result = {}
                    if data.get("age"):
                        result["age"] = data["age"]
                        result["age_sample_count"] = data.get("count", 0)
                        result["age_source"] = f"agify.io (name: {discovered_first})"
                    est.update(result)
                    _set_cache(discovered_first, "agify", result)
                elif resp.status_code == 429:
                    logger.warning("Agify rate limited, skipping")
            except Exception:
                logger.debug("Agify re-query failed")

        # Nationalize
        cached = _get_cached(discovered_first, "nationalize")
        if cached is not None:
            est.update(cached)
        else:
            try:
                time.sleep(0.5)
                resp = client.get(NATIONALIZE_URL.format(name=discovered_first))
                if resp.status_code == 200:
                    data = resp.json()
                    result = {}
                    countries = data.get("country", [])
                    if countries:
                        result["nationalities"] = [
                            {"country_code": c["country_id"], "probability": c["probability"]}
                            for c in countries[:3]
                        ]
                        result["nationality_source"] = f"nationalize.io (name: {discovered_first})"
                    est.update(result)
                    _set_cache(discovered_first, "nationalize", result)
                elif resp.status_code == 429:
                    logger.warning("Nationalize rate limited, skipping")
            except Exception:
                logger.debug("Nationalize re-query failed")

        client.close()

    except Exception:
        logger.exception("Identity enrichment failed")

    return est
