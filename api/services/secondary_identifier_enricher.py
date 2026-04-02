"""Run scrapers for phone and crypto_wallet input types.

Step A1.6 in finalize_scan. Uses sync httpx (same pattern as username_expander).
"""
import hashlib
import logging
import time
import uuid

import httpx
from sqlalchemy import select

from api.models.scraper import Scraper
from api.models.finding import Finding

logger = logging.getLogger(__name__)

SECONDARY_INPUT_TYPES = ["phone", "crypto_wallet"]
HTTP_TIMEOUT = 12
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def enrich_secondary_identifiers(target, scan, session):
    """Load phone/crypto scrapers, run them against extracted identifiers."""
    profile_data = target.profile_data or {}
    phones = profile_data.get("phones", [])
    wallets = profile_data.get("crypto_wallets", [])

    if not phones and not wallets:
        return

    scrapers = session.execute(
        select(Scraper).where(
            Scraper.input_type.in_(SECONDARY_INPUT_TYPES),
            Scraper.enabled == True,
        )
    ).scalars().all()

    if not scrapers:
        logger.info("A1.6: No phone/crypto scrapers enabled")
        return

    client = httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True,
                          headers={"User-Agent": USER_AGENT})

    try:
        phone_scrapers = [s for s in scrapers if s.input_type == "phone"]
        crypto_scrapers = [s for s in scrapers if s.input_type == "crypto_wallet"]

        created = 0
        if phone_scrapers and phones:
            for phone in phones[:3]:
                for scraper in phone_scrapers:
                    try:
                        if _run_scraper(client, scraper.to_dict(), phone, target, scan, session):
                            created += 1
                    except Exception as e:
                        logger.debug("A1.6: %s failed for %s: %s", scraper.name, phone, e)
                    time.sleep(0.5)

        if crypto_scrapers and wallets:
            for wallet in wallets[:3]:
                for scraper in crypto_scrapers:
                    try:
                        if _run_scraper(client, scraper.to_dict(), wallet["address"], target, scan, session):
                            created += 1
                    except Exception as e:
                        logger.debug("A1.6: %s failed for %s: %s", scraper.name, wallet["address"][:20], e)
                    time.sleep(0.5)

        if created:
            session.commit()
            logger.info("A1.6: Created %d findings from secondary identifier scrapers", created)
    finally:
        client.close()


def _run_scraper(client, scraper, input_value, target, scan, session):
    """Run a single scraper synchronously. Returns True if finding created."""
    import re
    from urllib.parse import quote as url_quote

    phone_clean = input_value.replace("+", "") if input_value.startswith("+") else input_value
    username = target.email.split("@")[0] if target.email and "@" in target.email else ""
    domain = target.email.split("@")[-1] if target.email and "@" in target.email else ""

    fmt_kwargs = {
        "phone": input_value,
        "phone_clean": phone_clean,
        "crypto_address": input_value,
        "input": input_value,
        "email": target.email or "",
        "username": username,
        "domain": domain,
        "first_name": username,
        "fullname": username,
        "fullname_encoded": url_quote(username),
        "email_md5": hashlib.md5((target.email or "").lower().encode()).hexdigest(),
    }

    try:
        url = scraper["url_template"].format(**fmt_kwargs)
    except (KeyError, IndexError):
        return False

    headers = {**{"User-Agent": USER_AGENT}, **(scraper.get("headers") or {})}

    try:
        if (scraper.get("method") or "GET").upper() == "POST":
            body = (scraper.get("body_template") or "").format(**fmt_kwargs)
            response = client.post(url, content=body, headers=headers)
        else:
            response = client.get(url, headers=headers)
    except Exception:
        return False

    if response.status_code in (404, 410, 429, 403):
        return False

    content = response.text
    success = scraper.get("success_indicator")
    not_found = scraper.get("not_found_indicators") or []

    found = False
    if success and re.search(success, content, re.IGNORECASE):
        found = True
        for nf in not_found:
            if nf.lower() in content.lower():
                found = False
                break
    elif response.status_code == 200 and not any(nf.lower() in content.lower() for nf in not_found):
        found = True

    if not found:
        return False

    # Extract data
    extracted = {}
    for rule in scraper.get("extraction_rules") or []:
        val = _extract(content, rule)
        if val is not None:
            extracted[rule["field"]] = val

    # Build title
    try:
        title = (scraper.get("finding_title_template") or "{input}").format(
            input=input_value, **{k: v for k, v in extracted.items() if v is not None}
        )
    except (KeyError, IndexError):
        title = f"{scraper.get('display_name', scraper.get('name'))}: {input_value}"

    # Create finding
    finding = Finding(
        id=uuid.uuid4(),
        workspace_id=target.workspace_id,
        scan_id=scan.id if scan else None,
        target_id=target.id,
        module=scraper.get("name", "secondary_enricher"),
        layer=2,
        category=scraper.get("finding_category", "identity"),
        severity=scraper.get("finding_severity", "info"),
        title=title[:255],
        description=f"Secondary identifier enrichment: {input_value}",
        data={"extracted": extracted, "url": url, "input_value": input_value,
              "input_type": scraper.get("input_type"), "pass": "A1.6"},
        url=url[:1024] if url else None,
        indicator_value=input_value[:500],
        indicator_type=scraper.get("input_type", "phone"),
        confidence=0.6,
        verified=False,
    )
    session.add(finding)
    session.flush()
    return True


def _extract(content, rule):
    """Extract a field from response content (same as scraper_engine)."""
    import re
    import json

    rule_type = rule.get("type", "regex")
    pattern = rule.get("pattern", "")

    try:
        if rule_type == "regex":
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(rule.get("group", 1))
        elif rule_type in ("json_key", "jsonpath"):
            data = json.loads(content)
            keys = pattern.split(".")
            for key in keys:
                if isinstance(data, dict):
                    data = data.get(key)
                elif isinstance(data, list) and key.isdigit():
                    idx = int(key)
                    data = data[idx] if idx < len(data) else None
                else:
                    return rule.get("default")
                if data is None:
                    return rule.get("default")
            return str(data) if data is not None else rule.get("default")
    except Exception:
        pass
    return rule.get("default")
