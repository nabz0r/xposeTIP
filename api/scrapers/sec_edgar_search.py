"""SEC EDGAR scraper — searches US securities filings (insider transactions, beneficial ownership).

Endpoint: GET https://efts.sec.gov/LATEST/search-index?q=<phrase>&forms=<list>

Targets Forms 3/4/5 (insider transactions), 144 (restricted stock sales),
13D/G (beneficial ownership >5%), DEF 14A (proxy). High-value for DD on
US-listed company executives, directors, and major shareholders.

Public US gov data. No API key. Mandatory User-Agent header per SEC fair
access policy (must include contact email).

Rate limit: 10 req/sec per SEC policy. We apply 1s minimum spacing
(handled by dispatcher's time.sleep after the call).
"""
import logging
from difflib import SequenceMatcher

import requests

logger = logging.getLogger(__name__)

SEC_EDGAR_URL = "https://efts.sec.gov/LATEST/search-index"
REQUEST_TIMEOUT = 12
MAX_RESULTS = 15
MIN_CONFIDENCE = 0.70
# SEC fair access policy requires identifying User-Agent with contact email.
# Use a generic project identifier; not workspace-specific.
USER_AGENT = "xposeTIP-research/1.0 contact@xpose-tip.io"

# Default form set for individuals (insider/ownership filings)
DEFAULT_FORMS = "3,4,5,144,13D,13G,DEF 14A"


def _name_similarity(name_a: str, name_b: str) -> float:
    """Compute name similarity (mirrors opencorporates_officers pattern)."""
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
    # Partial overlap — at least 2 name parts in common
    common = parts_a & parts_b
    if len(common) >= 2:
        return max(0.80, SequenceMatcher(None, a, b).ratio())
    return SequenceMatcher(None, a, b).ratio()


def _extract_individual_name(display_name: str) -> str:
    """
    SEC display_names format: 'Musk Elon  (CIK 0001494730)'.
    Strip the CIK suffix to get the bare name.
    Some entries are corporate, e.g. 'Tesla, Inc.  (CIK 0001318605)' — return as-is.
    """
    if not display_name:
        return ""
    idx = display_name.find("(CIK")
    if idx > 0:
        return display_name[:idx].strip()
    return display_name.strip()


def _build_filing_url(adsh: str, ciks: list) -> str:
    """Construct the SEC filing index URL from accession number + CIK."""
    if not adsh or not ciks:
        return ""
    # SEC URL: /Archives/edgar/data/{cik}/{accession_no_dashes_removed}/{accession_no}-index.htm
    primary_cik = str(ciks[0]).lstrip("0") if ciks else ""
    adsh_clean = adsh.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{primary_cik}/{adsh_clean}/{adsh}-index.htm"


def search_sec_edgar(primary_name: str, api_key: str | None = None) -> list[dict]:
    """
    Search SEC EDGAR for filings matching a person's name.
    `api_key` is unused (SEC requires no key) but kept in signature for
    dispatcher uniformity.
    Returns list of finding-shaped dicts.
    """
    if not primary_name or len(primary_name.strip()) < 4:
        return []

    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    params = {"q": f'"{primary_name}"', "forms": DEFAULT_FORMS}

    try:
        resp = requests.get(
            SEC_EDGAR_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT
        )
        if resp.status_code != 200:
            logger.warning("SEC EDGAR: HTTP %d for '%s'", resp.status_code, primary_name)
            return []

        data = resp.json()
        hits = (data.get("hits") or {}).get("hits") or []
        if not hits:
            return []

        findings = []
        for hit in hits[:MAX_RESULTS]:
            source = hit.get("_source") or {}
            display_names = source.get("display_names") or []
            if not display_names:
                continue

            # SEC filings often list multiple parties (filer + reporting company).
            # Match against any display_name; take the best confidence.
            best_match_name = ""
            best_confidence = 0.0
            for dn in display_names:
                bare = _extract_individual_name(dn)
                conf = _name_similarity(bare, primary_name)
                if conf > best_confidence:
                    best_confidence = conf
                    best_match_name = bare

            if best_confidence < MIN_CONFIDENCE:
                continue

            form = source.get("form") or (source.get("root_forms") or [""])[0]
            file_date = source.get("file_date") or ""
            adsh = source.get("adsh") or ""
            ciks = source.get("ciks") or []
            biz_states = source.get("biz_states") or []
            biz_locations = [loc for loc in (source.get("biz_locations") or []) if loc]

            findings.append({
                "title": f"SEC filing Form {form}: {best_match_name}" if form else f"SEC filing: {best_match_name}",
                "url": _build_filing_url(adsh, ciks),
                "description": f"Form {form} filed {file_date}" if file_date else f"Form {form}",
                "severity": "medium",
                "indicator_type": "legal_record",
                "indicator_value": adsh,
                "confidence": round(best_confidence, 3),
                "data": {
                    "scraper": "sec_edgar_search",
                    "form": form,
                    "file_date": file_date,
                    "accession": adsh,
                    "ciks": [str(c) for c in ciks],
                    "display_names": display_names,
                    "biz_states": biz_states,
                    "biz_locations": biz_locations,
                    "matched_name": best_match_name,
                    "match_confidence": round(best_confidence, 3),
                    "jurisdiction": "US federal (SEC)",
                    "source_type": "legal_record",
                },
            })

        logger.info(
            "SEC EDGAR: found %d filings for '%s' (from %d hits)",
            len(findings), primary_name, len(hits),
        )
        return findings

    except requests.exceptions.Timeout:
        logger.warning("SEC EDGAR: timeout for '%s'", primary_name)
        return []
    except requests.exceptions.RequestException as e:
        logger.warning("SEC EDGAR: request error for '%s': %s", primary_name, e)
        return []
    except (ValueError, KeyError) as e:
        logger.warning("SEC EDGAR: parse error for '%s': %s", primary_name, e)
        return []
