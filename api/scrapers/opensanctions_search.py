"""OpenSanctions scraper — searches sanctions, PEP, and wanted lists.

Endpoint: POST https://api.opensanctions.org/match/default

Aggregates 40+ datasets: OFAC SDN, EU Consolidated, UN Security Council,
Interpol Red Notices, PEP lists, national sanctions (UK, CH, AU, CA, JP).

Free API, no key needed. Rate limit ~60 req/min.
"""
import logging
import time

import requests

logger = logging.getLogger(__name__)

OPENSANCTIONS_URL = "https://api.opensanctions.org/match/default"
REQUEST_TIMEOUT = 15
MIN_OPENSANCTIONS_SCORE = 0.70
MIN_FINAL_CONFIDENCE = 0.65

# Human-readable dataset labels
DATASET_LABELS = {
    "us_ofac_sdn": "OFAC SDN (US Treasury)",
    "us_ofac_cons": "OFAC Consolidated (US)",
    "eu_fsf": "EU Consolidated Sanctions",
    "un_sc_sanctions": "UN Security Council",
    "interpol_red_notices": "Interpol Red Notices",
    "gb_hmt_sanctions": "UK HMT Sanctions",
    "ch_seco_sanctions": "Swiss SECO Sanctions",
    "au_dfat_sanctions": "Australia DFAT Sanctions",
    "ca_dfatd_sema_sanctions": "Canada Sanctions",
    "jp_mof_sanctions": "Japan MOF Sanctions",
    "ua_nsdc_sanctions": "Ukraine NSDC Sanctions",
    "ru_nsd_isin": "Russia NSD",
    "everypolitician": "EveryPolitician (PEP)",
    "wd_peps": "Wikidata PEP",
    "us_cia_world_leaders": "CIA World Leaders",
    "ru_rupep": "Russian PEP",
    "ua_pep": "Ukraine PEP",
    "kg_fiu_national": "Kyrgyzstan FIU",
    "za_fic_sanctions": "South Africa FIC",
}

# Topics -> indicator_type mapping
TOPIC_TYPE_MAP = {
    "sanction": "sanctions_match",
    "debarment": "sanctions_match",
    "poi": "sanctions_match",
    "wanted": "sanctions_match",
    "crime": "sanctions_match",
    "role.pep": "pep_match",
    "role.rca": "pep_match",
}

# Topics -> subtype mapping
TOPIC_SUBTYPE_MAP = {
    "wanted": "wanted",
    "crime": "criminal_record",
    "role.pep": "pep",
    "role.rca": "pep_associate",
}

# Topics -> severity mapping
TOPIC_SEVERITY_MAP = {
    "sanction": "critical",
    "debarment": "high",
    "wanted": "critical",
    "crime": "high",
    "poi": "high",
    "role.pep": "medium",
    "role.rca": "low",
}


def _get_dataset_labels(datasets: list[str]) -> list[str]:
    """Convert dataset IDs to human-readable labels."""
    return [DATASET_LABELS.get(d, d) for d in datasets]


def _first_or_none(lst):
    """Return first element or None."""
    if lst and isinstance(lst, list) and len(lst) > 0:
        return lst[0]
    return None


def _determine_indicator_type(topics: list[str]) -> str:
    """Determine indicator_type from topics list."""
    for topic in topics:
        if topic in TOPIC_TYPE_MAP:
            return TOPIC_TYPE_MAP[topic]
    return "sanctions_match"


def _determine_subtype(topics: list[str]) -> str:
    """Determine subtype from topics list."""
    for topic in topics:
        if topic in TOPIC_SUBTYPE_MAP:
            return TOPIC_SUBTYPE_MAP[topic]
    return "sanctions"


def _determine_severity(topics: list[str]) -> str:
    """Determine severity from topics list."""
    best = "info"
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    for topic in topics:
        sev = TOPIC_SEVERITY_MAP.get(topic, "info")
        if sev_order.get(sev, 5) < sev_order.get(best, 5):
            best = sev
    return best


def _compute_name_confidence(returned_names: list[str], target_name: str) -> float:
    """Compute name match confidence between OpenSanctions result and our target."""
    if not returned_names or not target_name:
        return 0.0

    target_lower = target_name.lower().strip()
    target_parts = set(target_lower.split())

    best = 0.0
    for name in returned_names:
        name_lower = name.lower().strip()
        # Exact match
        if name_lower == target_lower:
            return 1.0
        # Reversed order match (GROTZ, Mario vs Mario Grotz)
        name_parts = set(name_lower.replace(",", "").split())
        if name_parts == target_parts:
            best = max(best, 0.95)
            continue
        # All parts present
        if target_parts.issubset(name_parts) or name_parts.issubset(target_parts):
            best = max(best, 0.85)
            continue
        # Partial match
        overlap = len(target_parts & name_parts)
        if overlap >= 1:
            ratio = overlap / max(len(target_parts), len(name_parts))
            best = max(best, ratio * 0.8)

    return best


def build_sanctions_query(primary_name: str, nationality: str | None = None,
                          country: str | None = None, birth_year: int | None = None) -> dict:
    """Build structured query for OpenSanctions /match endpoint."""
    properties = {"name": [primary_name]}

    if nationality:
        properties["nationality"] = [nationality.lower()]
    if country:
        properties["country"] = [country.lower()]
    if birth_year:
        properties["birthDate"] = [str(birth_year)]

    return {
        "queries": {
            "target_query": {
                "schema": "Person",
                "properties": properties,
            }
        }
    }


def search_opensanctions(primary_name: str, nationality: str | None = None,
                         country: str | None = None, birth_year: int | None = None,
                         name_match_fn=None) -> list[dict]:
    """Search OpenSanctions for sanctions, PEP, and wanted matches.

    Args:
        primary_name: Full name to search
        nationality: ISO country code if known
        country: ISO country code if known
        birth_year: Estimated birth year if known
        name_match_fn: Optional function(text, name) -> float for confidence

    Returns:
        List of finding dicts ready for storage.
    """
    if not primary_name or len(primary_name.strip()) < 4:
        return []

    query = build_sanctions_query(primary_name, nationality, country, birth_year)

    try:
        resp = requests.post(
            OPENSANCTIONS_URL,
            json=query,
            timeout=REQUEST_TIMEOUT,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "xposeTIP/1.0",
            },
        )

        if resp.status_code == 429:
            logger.warning("OpenSanctions: Rate limited (429), waiting 10s...")
            time.sleep(10)
            # Retry once
            resp = requests.post(
                OPENSANCTIONS_URL, json=query, timeout=REQUEST_TIMEOUT,
                headers={"Content-Type": "application/json", "User-Agent": "xposeTIP/1.0"},
            )
            if resp.status_code == 429:
                logger.warning("OpenSanctions: Still rate limited after retry")
                return []

        if resp.status_code >= 500:
            logger.warning("OpenSanctions: Server error %d", resp.status_code)
            return []
        if resp.status_code != 200:
            logger.warning("OpenSanctions: HTTP %d for '%s'", resp.status_code, primary_name)
            return []

        data = resp.json()
        responses = data.get("responses", {})
        query_result = responses.get("target_query", {})
        results = query_result.get("results", [])

        if not results:
            logger.debug("OpenSanctions: No matches for '%s'", primary_name)
            return []

        findings = []
        for r in results:
            os_score = r.get("score", 0)
            if os_score < MIN_OPENSANCTIONS_SCORE:
                continue

            props = r.get("properties", {})
            topics = props.get("topics", [])
            datasets = r.get("datasets", [])
            returned_names = props.get("name", [])

            # Compute our name confidence
            our_confidence = _compute_name_confidence(returned_names, primary_name)
            if name_match_fn:
                # Use external confidence function on caption
                caption_conf = name_match_fn(r.get("caption", ""), primary_name)
                our_confidence = max(our_confidence, caption_conf)

            # Final blended confidence
            final_confidence = os_score * 0.6 + our_confidence * 0.4
            if final_confidence < MIN_FINAL_CONFIDENCE:
                continue

            indicator_type = _determine_indicator_type(topics)
            subtype = _determine_subtype(topics)
            severity = _determine_severity(topics)

            caption = r.get("caption", primary_name)
            dataset_labels = _get_dataset_labels(datasets)

            findings.append({
                "title": f"{caption} — {', '.join(dataset_labels[:3])}",
                "url": f"https://opensanctions.org/entities/{r.get('id', '')}",
                "description": _first_or_none(props.get("notes")) or f"Match on {', '.join(dataset_labels[:2])}",
                "severity": severity,
                "indicator_type": indicator_type,
                "indicator_value": r.get("id", ""),
                "confidence": round(final_confidence, 3),
                "data": {
                    "scraper": "opensanctions_search",
                    "entity_id": r.get("id", ""),
                    "caption": caption,
                    "datasets": datasets,
                    "dataset_labels": dataset_labels,
                    "opensanctions_score": round(os_score, 3),
                    "match_confidence": round(final_confidence, 3),
                    "match_type": "potential",
                    "source_type": "name_search",
                    "topics": topics,
                    "listed_reason": _first_or_none(props.get("notes")),
                    "source_urls": props.get("sourceUrl", []),
                    "birth_date": _first_or_none(props.get("birthDate")),
                    "nationality": props.get("nationality", []),
                    "aliases": returned_names[:5],
                    "subtype": subtype,
                },
            })

        logger.info("OpenSanctions: Found %d matches for '%s' (from %d results)",
                     len(findings), primary_name, len(results))
        return findings

    except requests.exceptions.Timeout:
        logger.warning("OpenSanctions: Timeout for '%s'", primary_name)
        return []
    except requests.exceptions.RequestException as e:
        logger.warning("OpenSanctions: Request error for '%s': %s", primary_name, e)
        return []
    except Exception:
        logger.exception("OpenSanctions: Unexpected error for '%s'", primary_name)
        return []
