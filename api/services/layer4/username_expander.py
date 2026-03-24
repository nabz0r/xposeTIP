"""Pass 1.5 — Username Expansion Scan.

After Pass 1 discovers usernames via email-based scrapers, this service
selects the top N usernames (by platform count × confidence) and re-scans
them across all {username}-capable scrapers.

Multiplies account discovery 2-3× with zero additional API keys.
Runs in the sync Celery worker context (httpx.Client, not AsyncClient).
"""
import hashlib
import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from api.models.finding import Finding
from api.models.identity import Identity, IdentityLink
from api.models.scraper import Scraper

logger = logging.getLogger(__name__)

# Config
MAX_USERNAMES = 3
MIN_PLATFORMS = 2         # Username must appear on 2+ platforms
MAX_SCRAPERS = 50         # Cap scrapers per username
RATE_LIMIT_DELAY = 0.5    # Seconds between calls
TOTAL_TIMEOUT = 120       # Total expansion budget in seconds
HTTP_TIMEOUT = 12         # Per-request timeout

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Usernames to skip (generic, email-derived noise)
SKIP_USERNAMES = {
    "info", "contact", "admin", "support", "noreply", "test",
    "hello", "mail", "office", "sales", "help", "service",
}


def expand_usernames(target_id, workspace_id, session: Session,
                     scan_id=None, email=None) -> dict:
    """Run Pass 1.5 username expansion. Returns summary dict."""
    t0 = time.time()
    result = {
        "usernames_selected": [],
        "scrapers_run": 0,
        "findings_created": 0,
        "identities_created": 0,
        "errors": [],
    }

    try:
        # 1. Discover top usernames from identity graph
        usernames = _select_usernames(target_id, workspace_id, session, email)
        if not usernames:
            logger.info("Pass 1.5: No qualifying usernames for target %s", target_id)
            return result
        result["usernames_selected"] = [u["value"] for u in usernames]
        logger.info("Pass 1.5: Selected %d usernames for expansion: %s",
                     len(usernames), result["usernames_selected"])

        # 2. Load username-capable scrapers
        scrapers = _load_username_scrapers(session)
        if not scrapers:
            return result

        # 3. Get existing findings for dedup
        existing = _get_existing_indicators(target_id, session)

        # 4. Execute expansion
        client = httpx.Client(
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )

        health = _get_health()

        try:
            for uinfo in usernames:
                username = uinfo["value"]
                for scraper in scrapers[:MAX_SCRAPERS]:
                    # Budget check
                    if time.time() - t0 > TOTAL_TIMEOUT:
                        logger.warning("Pass 1.5: Timeout reached after %ds", TOTAL_TIMEOUT)
                        result["errors"].append("timeout")
                        return result

                    # Skip if we already have a finding for this scraper+username
                    dedup_key = f"{scraper['name']}:{username}"
                    if dedup_key in existing:
                        continue

                    try:
                        found_data = _execute_scraper(client, scraper, username, health)
                        result["scrapers_run"] += 1

                        if found_data and found_data.get("found"):
                            # Create finding + identity + edge
                            created = _store_result(
                                session, target_id, workspace_id, scan_id,
                                scraper, username, found_data, uinfo,
                            )
                            if created:
                                result["findings_created"] += created.get("findings", 0)
                                result["identities_created"] += created.get("identities", 0)
                                existing.add(dedup_key)

                        time.sleep(RATE_LIMIT_DELAY)

                    except Exception as e:
                        logger.debug("Pass 1.5: Scraper %s failed for %s: %s",
                                     scraper["name"], username, e)
                        result["errors"].append(f"{scraper['name']}:{e}")
        finally:
            client.close()

        # Commit all at once
        if result["findings_created"] > 0:
            session.commit()

        elapsed = time.time() - t0
        logger.info(
            "Pass 1.5 complete for target %s: %d usernames, %d scrapers, "
            "%d findings, %d identities in %.1fs",
            target_id, len(usernames), result["scrapers_run"],
            result["findings_created"], result["identities_created"], elapsed,
        )

    except Exception:
        logger.exception("Pass 1.5 failed for target %s", target_id)

    return result


def _select_usernames(target_id, workspace_id, session: Session, email=None) -> list:
    """Select top N usernames from the identity graph.

    Criteria: type='username', appears on 2+ platforms, not the email prefix,
    sorted by (platform_count × avg_confidence) descending.
    """
    identities = session.execute(
        select(Identity).where(
            Identity.target_id == target_id,
            Identity.workspace_id == workspace_id,
            Identity.type == "username",
        )
    ).scalars().all()

    if not identities:
        return []

    # Email prefix to exclude (trivial match)
    email_prefix = email.split("@")[0].lower() if email and "@" in email else None

    # Group by username value
    groups = {}
    for ident in identities:
        val = ident.value.strip().lower()
        if not val or len(val) < 2:
            continue
        if val in SKIP_USERNAMES:
            continue
        if email_prefix and val == email_prefix:
            continue
        # Skip if it looks like an email
        if "@" in val:
            continue

        if val not in groups:
            groups[val] = {"value": ident.value, "platforms": set(), "confidences": [], "ids": []}
        groups[val]["platforms"].add(ident.platform or "unknown")
        groups[val]["confidences"].append(ident.confidence or 0.5)
        groups[val]["ids"].append(ident.id)

    # Filter: must appear on 2+ platforms
    candidates = [g for g in groups.values() if len(g["platforms"]) >= MIN_PLATFORMS]

    if not candidates:
        # Relax: allow single-platform usernames with high confidence
        candidates = [
            g for g in groups.values()
            if max(g["confidences"]) >= 0.8
        ]

    # Score: platform_count × avg_confidence
    for c in candidates:
        c["score"] = len(c["platforms"]) * (sum(c["confidences"]) / len(c["confidences"]))

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:MAX_USERNAMES]


def _load_username_scrapers(session: Session) -> list:
    """Load all enabled scrapers with input_type='username'."""
    scrapers = session.execute(
        select(Scraper).where(
            Scraper.input_type == "username",
            Scraper.enabled == True,
        )
    ).scalars().all()

    return [s.to_dict() for s in scrapers]


def _get_existing_indicators(target_id, session: Session) -> set:
    """Get existing finding dedup keys: 'module:indicator_value'."""
    findings = session.execute(
        select(Finding.module, Finding.indicator_value).where(
            Finding.target_id == target_id,
        )
    ).all()

    return {f"{mod}:{val}" for mod, val in findings if mod and val}


def _execute_scraper(client: httpx.Client, scraper: dict, username: str,
                     health=None) -> dict:
    """Execute a single scraper against a username. Sync version."""
    url = ""
    try:
        fmt_kwargs = {
            "username": username,
            "email": username,  # Some templates use {email}
            "input": username,
            "domain": "",
            "first_name": username,
            "fullname": username,
            "fullname_encoded": username,
            "email_md5": hashlib.md5(username.encode()).hexdigest(),
        }

        url = scraper["url_template"].format(**fmt_kwargs)
        headers = {**{"User-Agent": USER_AGENT}, **(scraper.get("headers") or {})}

        t0 = time.time()
        if (scraper.get("method") or "GET").upper() == "POST":
            body = (scraper.get("body_template") or "").format(**fmt_kwargs)
            response = client.post(url, content=body, headers=headers)
        else:
            response = client.get(url, headers=headers)
        elapsed_ms = int((time.time() - t0) * 1000)

        # Record health
        if health:
            health.record(scraper.get("name", "unknown"), response.status_code, elapsed_ms)

        content = response.text
        found = _check_found(content, response.status_code, scraper)

        if not found:
            return {"found": False, "url": url, "status_code": response.status_code}

        # Extract data
        extracted = {}
        for rule in scraper.get("extraction_rules") or []:
            value = _extract(content, rule)
            if value is not None:
                extracted[rule["field"]] = value

        return {
            "found": True,
            "extracted": extracted,
            "url": url,
            "status_code": response.status_code,
        }

    except httpx.TimeoutException:
        return {"found": False, "error": "timeout", "url": url}
    except Exception as e:
        logger.debug("Scraper %s failed: %s", scraper.get("name"), e)
        return {"found": False, "error": str(e), "url": url}


def _check_found(content: str, status_code: int, scraper: dict) -> bool:
    """Check if profile was found (mirrors ScraperEngine._check_found)."""
    if status_code in (404, 410, 429):
        return False

    success = scraper.get("success_indicator")
    not_found = scraper.get("not_found_indicators") or []
    content_lower = content.lower()

    if success and re.search(success, content, re.IGNORECASE):
        for indicator in not_found:
            if len(indicator) >= 10 and indicator.lower() in content_lower:
                return False
        return True

    if status_code == 403:
        return False

    for indicator in not_found:
        if indicator.lower() in content_lower:
            return False

    return status_code == 200


def _extract(content: str, rule: dict):
    """Extract a field from response content."""
    rule_type = rule.get("type", "regex")
    pattern = rule.get("pattern", "")

    try:
        if rule_type == "regex":
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                group = rule.get("group", 1)
                return match.group(group)

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


def _store_result(session: Session, target_id, workspace_id, scan_id,
                  scraper: dict, username: str, found_data: dict,
                  username_info: dict) -> dict:
    """Store a found account as Finding + Identity + IdentityLink."""
    counts = {"findings": 0, "identities": 0}
    scraper_name = scraper.get("name", "unknown")
    platform = scraper_name.replace("scraper_", "").split("_")[0]
    extracted = found_data.get("extracted", {})

    # Create Finding
    title = scraper.get("finding_title_template", "Account found: {username} on {platform}")
    try:
        title = title.format(username=username, platform=platform, **extracted)
    except (KeyError, IndexError):
        title = f"Account found: {username} on {platform}"

    finding = Finding(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        scan_id=scan_id,
        target_id=target_id,
        module=scraper_name,
        layer=1,
        category=scraper.get("finding_category", "social_media"),
        severity=scraper.get("finding_severity", "info"),
        title=title[:255],
        description=f"Username '{username}' found on {platform} via Pass 1.5 expansion",
        data={
            "extracted": extracted,
            "url": found_data.get("url"),
            "pass": "1.5",
            "source_username": username,
            "source_platforms": list(username_info.get("platforms", [])),
        },
        url=found_data.get("url"),
        indicator_value=username,
        indicator_type="username",
        confidence=min(1.0, (username_info.get("score", 0.5) / 3) + 0.3),
        verified=False,
    )
    session.add(finding)
    counts["findings"] = 1

    # Create Identity node (upsert pattern — skip if exists)
    existing_identity = session.execute(
        select(Identity).where(
            Identity.workspace_id == workspace_id,
            Identity.target_id == target_id,
            Identity.type == "username",
            Identity.value == username,
            Identity.platform == platform,
        )
    ).scalar_one_or_none()

    if not existing_identity:
        identity = Identity(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            target_id=target_id,
            type="username",
            value=username,
            platform=platform,
            source_module=scraper_name,
            confidence=finding.confidence,
        )
        session.add(identity)
        counts["identities"] = 1

        # Create edge: email_anchor → username (registered_with)
        email_anchor = session.execute(
            select(Identity).where(
                Identity.workspace_id == workspace_id,
                Identity.target_id == target_id,
                Identity.type == "email",
            )
        ).scalars().first()

        if email_anchor:
            existing_link = session.execute(
                select(IdentityLink).where(
                    IdentityLink.workspace_id == workspace_id,
                    IdentityLink.source_id == email_anchor.id,
                    IdentityLink.dest_id == identity.id,
                    IdentityLink.link_type == "registered_with",
                )
            ).scalar_one_or_none()

            if not existing_link:
                link = IdentityLink(
                    id=uuid.uuid4(),
                    workspace_id=workspace_id,
                    source_id=email_anchor.id,
                    dest_id=identity.id,
                    link_type="registered_with",
                    confidence=finding.confidence,
                    source_module=f"{scraper_name}:pass1.5",
                )
                session.add(link)

    # Flush to avoid constraint violations on next iteration
    try:
        session.flush()
    except Exception:
        session.rollback()
        logger.debug("Flush failed for %s:%s, likely duplicate", scraper_name, username)
        return None

    return counts


def _get_health():
    """Lazy-load scraper health instance."""
    try:
        from api.services.scraper_health import get_scraper_health_instance
        return get_scraper_health_instance()
    except Exception:
        return None
