"""GLEIF LEI scraper — global legal-entity reference data (S268, AR-1 Round 0).

Endpoint: GET https://api.gleif.org/api/v1/lei-records?filter[entity.legalName]=<name>
Free, no authentication, no API key. Data licensed CC0 (public domain). 3.3M+ entities.

Returns legal name, LEI, jurisdiction, legal form, registration status, registered
address, and a link to the relationship records (legal parent/ultimate-parent
ownership graph) — corporate FACTS only, no personal/UBO data (RGPD-safe).

Coverage skews to financial/regulated entities: an unregistered startup may have no
LEI → [] (honest false-negative, not an error). A null result is the data saying
"the national register (RESA/RCS) is the next connector", not a bug.

Jurisdiction co-occurrence guard: GLEIF's legalName filter is exact-ish; a same-name
entity in the WRONG country is the costly false-positive direction. When a
jurisdiction hint is given and the record's jurisdiction differs, the finding is
down-weighted (not asserted at full confidence) — same discipline as AR-0's
company-co-occurrence gate.
"""
import logging

import requests

logger = logging.getLogger(__name__)

GLEIF_URL = "https://api.gleif.org/api/v1/lei-records"
REQUEST_TIMEOUT = 15
MAX_RESULTS = 5
MIN_NAME_LEN = 3


def search_gleif(company_name: str, jurisdiction_hint: str | None = None) -> list[dict]:
    if not company_name or len(company_name.strip()) < MIN_NAME_LEN:
        return []
    params = {
        "filter[entity.legalName]": company_name.strip(),
        "page[size]": MAX_RESULTS,
    }
    if jurisdiction_hint:
        # Hint, not a hard server-side filter — multinationals register elsewhere;
        # we soften confidence client-side instead of dropping (see below).
        pass
    hint = (jurisdiction_hint or "").upper() or None
    try:
        r = requests.get(
            GLEIF_URL, params=params,
            headers={"Accept": "application/vnd.api+json"}, timeout=REQUEST_TIMEOUT,
        )
        if r.status_code != 200:
            logger.warning("gleif: HTTP %d for %s", r.status_code, company_name[:60])
            return []
        records = (r.json() or {}).get("data", []) or []
    except Exception as e:
        logger.warning("gleif failed for %s: %s", company_name[:60], e)
        return []

    out = []
    for rec in records:
        attr = rec.get("attributes", {}) or {}
        ent = attr.get("entity", {}) or {}
        reg = attr.get("registration", {}) or {}
        lei = attr.get("lei") or rec.get("id")
        legal_name = (ent.get("legalName") or {}).get("name", "") or ""
        if not legal_name or not lei:
            continue
        juris = ent.get("jurisdiction")

        # Jurisdiction co-occurrence guard — false-positive is the costly direction.
        conf = 0.95
        juris_mismatch = bool(hint and juris and juris.upper() != hint)
        if juris_mismatch:
            conf = 0.50  # same name, different country → likely a different entity

        addr = ent.get("legalAddress") or {}
        out.append({
            "indicator_type": "company",           # store block maps → category 'corporate' (entity tier)
            "indicator_value": legal_name,
            "title": f"Legal entity: {legal_name} ({juris or '?'})",
            "description": f"GLEIF LEI {lei} — {(ent.get('status') or '?')}, registration {(reg.get('status') or '?')}",
            "url": f"https://search.gleif.org/#/record/{lei}",
            "severity": "info",
            "confidence": conf,
            "data": {
                "scraper": "gleif_search",         # store block uses this as module name
                "lei": lei,
                "legal_name": legal_name,
                "jurisdiction": juris,
                "legal_form": (ent.get("legalForm") or {}).get("id"),
                "status": ent.get("status"),                 # ACTIVE / INACTIVE
                "is_active": (ent.get("status") == "ACTIVE"),
                "registration_status": reg.get("status"),    # ISSUED / LAPSED / ...
                "registered_city": addr.get("city"),
                "registered_country": addr.get("country"),
                "jurisdiction_hint": hint,
                "jurisdiction_mismatch": juris_mismatch,
                "relationship_records_url": f"{GLEIF_URL}/{lei}/relationship-records",
                "lei_record_url": f"https://search.gleif.org/#/record/{lei}",
            },
        })
    return out
