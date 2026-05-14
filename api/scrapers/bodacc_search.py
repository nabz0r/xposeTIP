"""BODACC scraper — French commercial register public notices.

Endpoint: GET https://bodacc-datadila.opendatasoft.com/api/records/1.0/search/?dataset=annonces-commerciales&q=<name>

Covers procédures collectives (redressement, liquidation, sauvegarde),
ventes/cessions, immatriculations, modifications, radiations published
in the French Bulletin officiel des annonces civiles et commerciales.
Person-centric (unlike Judilibre which is pseudonymized).

Free, no authentication required. Open licence v2.0.
"""
import logging
import time

import requests

logger = logging.getLogger(__name__)

REDIS_DISABLE_KEY = "bodacc:disabled"
REDIS_DISABLE_TTL = 3600

BODACC_URL = "https://bodacc-datadila.opendatasoft.com/api/records/1.0/search/"
DATASET = "annonces-commerciales"
REQUEST_TIMEOUT = 15
MIN_NAME_CONFIDENCE = 0.70
MAX_RESULTS = 25

# Severity mapping for famille_avis values
FAMILLE_SEVERITY = {
    "procedures_collectives": "high",       # redressement / liquidation
    "procedures_de_conciliation": "medium",
    "retablissements_professionnels": "medium",
    "ventes_et_cessions": "low",
    "immatriculations": "info",
    "modifications": "info",
    "radiations": "low",
    "depot_des_comptes": "info",
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
        logger.warning("BODACC disabled for %ds after upstream error", REDIS_DISABLE_TTL)
    except Exception:
        pass


def _compute_name_confidence(record_fields: dict, target_name: str) -> float:
    """Score how confidently a BODACC record matches our target name."""
    if not target_name:
        return 0.0
    target_lower = target_name.lower().strip()
    target_parts = set(target_lower.split())
    if not target_parts:
        return 0.0

    # Combine the BODACC fields that may carry person names
    haystack_pieces = []
    for key in ("commercant", "denomination", "personnes",
                "cessions_immatriculations_etablissement",
                "depot", "modifications_generales", "radiation_au_rcs",
                "listepersonnes", "personne"):
        v = record_fields.get(key)
        if v:
            haystack_pieces.append(str(v).lower())
    haystack = " | ".join(haystack_pieces)
    if not haystack:
        return 0.0

    if target_lower in haystack:
        return 0.95
    h_parts = set(
        haystack.replace(",", " ").replace(";", " ").replace(".", " ").split()
    )
    overlap = len(target_parts & h_parts)
    if overlap >= len(target_parts):
        return 0.85
    if overlap >= 1:
        return overlap / max(len(target_parts), len(h_parts)) * 0.7
    return 0.0


def search_bodacc(primary_name: str) -> list[dict]:
    """Search BODACC for legal/commercial notices mentioning a person.

    Args:
        primary_name: full name (e.g. "Jean Dupont")

    Returns:
        List of finding dicts ready for storage.
    """
    if not primary_name or len(primary_name.strip()) < 4:
        return []
    if _is_disabled():
        logger.debug("BODACC: skipping — disabled")
        return []

    headers = {"User-Agent": "xposeTIP/1.0", "Accept": "application/json"}
    params = {
        "dataset": DATASET,
        "q": primary_name,
        "rows": MAX_RESULTS,
        "sort": "-dateparution",
    }

    try:
        resp = requests.get(
            BODACC_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT,
        )

        if resp.status_code == 429:
            logger.warning("BODACC: rate limited (429), waiting 10s...")
            time.sleep(10)
            resp = requests.get(
                BODACC_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT,
            )

        if resp.status_code >= 500:
            logger.warning("BODACC: server error %d", resp.status_code)
            _set_disabled()
            return []
        if resp.status_code != 200:
            logger.warning("BODACC: HTTP %d for '%s'", resp.status_code, primary_name)
            return []

        data = resp.json()
        records = data.get("records", []) or []
        if not records:
            logger.debug("BODACC: no matches for '%s'", primary_name)
            return []

        findings = []
        for rec in records:
            fields = rec.get("fields", {}) or {}
            confidence = _compute_name_confidence(fields, primary_name)
            if confidence < MIN_NAME_CONFIDENCE:
                continue

            famille = (fields.get("familleavis_lib") or fields.get("familleavis") or "").lower().replace(" ", "_")
            severity = FAMILLE_SEVERITY.get(famille, "medium")
            type_avis = fields.get("typeavis_lib") or fields.get("typeavis") or ""
            ville = fields.get("ville") or ""
            date_parution = fields.get("dateparution") or ""
            tribunal = fields.get("tribunal") or ""
            commercant = fields.get("commercant") or fields.get("denomination") or ""

            record_id = rec.get("recordid", "")
            url = f"https://www.bodacc.fr/pages/annonces-commerciales/?refine.numeroannonce={fields.get('numeroannonce','')}" if fields.get("numeroannonce") else "https://www.bodacc.fr/"

            findings.append({
                "title": f"BODACC ({type_avis}): {commercant}" if commercant else f"BODACC: {type_avis}",
                "url": url,
                "description": f"{tribunal} — {ville}" if tribunal or ville else "",
                "severity": severity,
                "indicator_type": "legal_record",
                "indicator_value": fields.get("numeroannonce", "") or record_id,
                "confidence": round(confidence, 3),
                "data": {
                    "scraper": "bodacc_search",
                    "famille_avis": famille,
                    "type_avis": type_avis,
                    "commercant": commercant,
                    "tribunal": tribunal,
                    "ville": ville,
                    "departement": fields.get("nom_dep_min") or fields.get("numerodepartement"),
                    "date_parution": date_parution,
                    "numero_annonce": fields.get("numeroannonce"),
                    "jurisdiction": "FR",
                    "source_type": "legal_record",
                    "match_confidence": round(confidence, 3),
                },
            })

        logger.info(
            "BODACC: found %d legal records for '%s' (from %d records)",
            len(findings), primary_name, len(records),
        )
        return findings

    except requests.exceptions.Timeout:
        logger.warning("BODACC: timeout for '%s'", primary_name)
        return []
    except requests.exceptions.RequestException as e:
        logger.warning("BODACC: request error for '%s': %s", primary_name, e)
        return []
    except Exception:
        logger.exception("BODACC: unexpected error for '%s'", primary_name)
        return []
