"""Luxembourg Business Register (LBR/RCS) scraper — official register search.

Searches https://www.lbr.lu for company officers by name.
Only runs on Luxembourg-connected targets (country=LU or domain=.lu).

Official government source, reliability 0.92.
"""
import logging
import re
from difflib import SequenceMatcher

import requests

logger = logging.getLogger(__name__)

LBR_SEARCH_URL = "https://www.lbr.lu/mjrcs/jsp/webapp/static/mjrcs/fr/recherche/recherchePerson"
REQUEST_TIMEOUT = 15
MIN_CONFIDENCE = 0.60

# Luxembourg role translations
LU_ROLE_MAP = {
    "gérant": "Manager",
    "gerant": "Manager",
    "administrateur": "Director",
    "administrateur-délégué": "Managing Director",
    "administrateur-delegue": "Managing Director",
    "administrateur délégué": "Managing Director",
    "président du conseil d'administration": "Chairman",
    "president du conseil d'administration": "Chairman",
    "président": "Chairman",
    "vice-président": "Vice Chairman",
    "commissaire aux comptes": "Auditor",
    "commissaire": "Auditor",
    "associé": "Partner/Shareholder",
    "associe": "Partner/Shareholder",
    "actionnaire": "Shareholder",
    "secrétaire": "Secretary",
    "secretaire": "Secretary",
    "directeur": "Director",
    "directeur général": "CEO",
    "membre du conseil d'administration": "Board Member",
    "liquidateur": "Liquidator",
    "fondateur": "Founder",
    "représentant permanent": "Permanent Representative",
}


def _translate_role(role: str) -> str:
    """Translate Luxembourg role to English."""
    if not role:
        return "Officer"
    role_lower = role.lower().strip()
    for fr, en in LU_ROLE_MAP.items():
        if fr in role_lower:
            return en
    return role.strip()


def _split_name(full_name: str) -> tuple[str, str]:
    """Split full name into (first_name, last_name)."""
    parts = full_name.strip().split()
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    return full_name, ""


def _name_similarity(name_a: str, name_b: str) -> float:
    """Compute name similarity."""
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
    return SequenceMatcher(None, a, b).ratio()


def search_lbr_luxembourg(primary_name: str) -> list[dict]:
    """Search Luxembourg Business Register for company officer roles.

    Args:
        primary_name: Full name to search

    Returns:
        List of finding dicts ready for storage.
    """
    if not primary_name or len(primary_name.strip()) < 4:
        return []

    first_name, last_name = _split_name(primary_name)
    if not last_name:
        return []

    params = {
        "personName": last_name.upper(),
        "personFirstName": first_name.upper(),
    }

    try:
        resp = requests.get(
            LBR_SEARCH_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; xposeTIP/1.0)",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            },
        )

        if resp.status_code == 403:
            logger.warning("LBR: Access blocked (403) — may require captcha")
            return []
        if resp.status_code != 200:
            logger.warning("LBR: HTTP %d for '%s'", resp.status_code, primary_name)
            return []

        # Parse HTML
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("LBR: beautifulsoup4 not installed")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # Look for result tables
        findings = []
        seen_companies = set()

        # LBR results are in table rows with person/company data
        # Try multiple selectors for robustness
        rows = soup.select("table.resultats tr") or soup.select("table tr")
        if not rows:
            # Try finding any table with data
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                if len(rows) > 1:
                    break

        if not rows or len(rows) <= 1:
            # Check if there's a "no results" message
            page_text = soup.get_text().lower()
            if "aucun" in page_text or "no result" in page_text:
                logger.debug("LBR: No results for '%s'", primary_name)
                return []
            # Might be blocked or changed format
            logger.debug("LBR: Could not parse results for '%s'", primary_name)
            return []

        for row in rows[1:]:  # Skip header row
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            # Extract data from cells (typical format: name, role, company, RCS)
            cell_texts = [c.get_text(strip=True) for c in cells]

            # Try to identify fields
            person_name = ""
            role = ""
            company_name = ""
            rcs_number = ""

            for i, text in enumerate(cell_texts):
                if not text:
                    continue
                # RCS number pattern: letter(s) followed by digits
                if re.match(r'^[A-Z]\d+$', text) or re.match(r'^[A-Z]{1,2}\s?\d+$', text):
                    rcs_number = text
                elif any(r in text.lower() for r in ("gérant", "administrateur", "directeur",
                                                       "commissaire", "associé", "président",
                                                       "membre", "liquidateur", "fondateur",
                                                       "secretary", "director", "manager")):
                    role = text
                elif i == 0 and not person_name:
                    person_name = text
                elif not company_name and len(text) > 3:
                    company_name = text

            if not company_name:
                continue

            # Dedup
            dedup_key = company_name.lower().strip()
            if dedup_key in seen_companies:
                continue
            seen_companies.add(dedup_key)

            # Compute confidence
            name_sim = _name_similarity(person_name or primary_name, primary_name)
            # LBR is official source + jurisdiction is always LU = high base confidence
            confidence = name_sim * 0.5 + 0.3 + 0.15  # jurisdiction=LU always matches, active assumed
            confidence = min(confidence, 1.0)

            if confidence < MIN_CONFIDENCE:
                continue

            role_en = _translate_role(role)

            # Extract links if any
            link = row.find("a")
            company_url = ""
            if link and link.get("href"):
                href = link["href"]
                if href.startswith("http"):
                    company_url = href
                elif href.startswith("/"):
                    company_url = f"https://www.lbr.lu{href}"

            findings.append({
                "title": f"{role_en} at {company_name} (LU)"[:255],
                "url": company_url or "https://www.lbr.lu",
                "description": f"{person_name or primary_name} — {role_en} at {company_name} (RCS: {rcs_number})",
                "severity": "low",
                "indicator_type": "corporate_officer",
                "indicator_value": f"lu-rcs-{rcs_number}" if rcs_number else company_url,
                "confidence": round(confidence, 3),
                "data": {
                    "scraper": "lbr_luxembourg",
                    "officer_name": person_name or primary_name,
                    "position": role_en,
                    "position_original": role,
                    "company_name": company_name,
                    "rcs_number": rcs_number,
                    "jurisdiction": "lu",
                    "is_active": True,  # LBR typically shows current roles
                    "source": "Luxembourg RCS/LBR",
                    "company_url": company_url,
                    "match_confidence": round(confidence, 3),
                    "match_type": "potential",
                    "source_type": "name_search",
                },
            })

        logger.info("LBR: Found %d officer roles for '%s'", len(findings), primary_name)
        return findings[:8]

    except requests.exceptions.Timeout:
        logger.warning("LBR: Timeout for '%s'", primary_name)
        return []
    except requests.exceptions.RequestException as e:
        logger.warning("LBR: Request error for '%s': %s", primary_name, e)
        return []
    except Exception:
        logger.exception("LBR: Unexpected error for '%s'", primary_name)
        return []
