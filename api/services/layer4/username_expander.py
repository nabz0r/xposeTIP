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
from api.services.layer4.username_validator import is_valid_username

logger = logging.getLogger(__name__)


class _SafeFormatDict(dict):
    """Dict that returns '{key}' for missing keys, avoiding KeyError in .format_map()."""
    def __missing__(self, key):
        return f"{{{key}}}"


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
            with session.no_autoflush:
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
                            try:
                                session.rollback()
                            except Exception:
                                pass
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
    """Select top N usernames from findings AND identity graph.

    Primary source: Finding records (indicator_type='username') — most usernames
    land here. Secondary source: Identity nodes (type='username').
    Criteria: appears on 2+ platforms, not the email prefix,
    sorted by (platform_count × avg_confidence) descending.
    """
    # Email prefix to exclude (trivial match)
    email_prefix = email.split("@")[0].lower() if email and "@" in email else None

    # Group by username value
    groups = {}

    def _add_to_group(val_raw, platform, confidence):
        """Add a username occurrence to the groups dict."""
        val = val_raw.strip().lower()
        if not val or len(val) < 2:
            return
        if val in SKIP_USERNAMES:
            return
        if email_prefix and val == email_prefix:
            return
        if "@" in val:
            return
        if not is_valid_username(val_raw.strip()):
            return

        if val not in groups:
            groups[val] = {"value": val_raw.strip(), "platforms": set(), "confidences": []}
        groups[val]["platforms"].add(platform or "unknown")
        groups[val]["confidences"].append(confidence or 0.5)

    # Source 1: Findings (primary — most usernames live here)
    username_findings = session.execute(
        select(Finding).where(
            Finding.target_id == target_id,
            Finding.indicator_type == "username",
        )
    ).scalars().all()

    for f in username_findings:
        if not f.indicator_value:
            continue
        # Extract platform from module name (e.g. "scraper_github_profile" → "github")
        platform = (f.module or "").replace("scraper_", "").split("_")[0]
        if not platform and f.data and isinstance(f.data, dict):
            platform = f.data.get("platform", "unknown")
        _add_to_group(f.indicator_value, platform, f.confidence)

    # Source 2: Identity nodes (secondary enrichment)
    identities = session.execute(
        select(Identity).where(
            Identity.target_id == target_id,
            Identity.workspace_id == workspace_id,
            Identity.type == "username",
        )
    ).scalars().all()

    for ident in identities:
        if not ident.value:
            continue
        _add_to_group(ident.value, ident.platform, ident.confidence)

    if not groups:
        return []

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
        # Use a defaultdict-like SafeDict so unknown {placeholders} survive
        # without raising KeyError or "got multiple values" from .format()
        fmt_kwargs = _SafeFormatDict({
            "username": username,
            "email": username,  # Some templates use {email}
            "input": username,
            "domain": "",
            "first_name": username,
            "fullname": username,
            "fullname_encoded": username,
            "email_md5": hashlib.md5(username.encode()).hexdigest(),
            "name": username,
        })

        url = scraper["url_template"].format_map(fmt_kwargs)
        headers = {**{"User-Agent": USER_AGENT}, **(scraper.get("headers") or {})}

        t0 = time.time()
        if (scraper.get("method") or "GET").upper() == "POST":
            body = (scraper.get("body_template") or "").format_map(fmt_kwargs)
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


def _sanitize_for_json(obj):
    """Recursively convert non-JSON-serializable types for JSONB storage."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    elif isinstance(obj, (datetime,)):
        return obj.isoformat()
    elif isinstance(obj, set):
        return list(obj)
    return obj


def _store_result(session: Session, target_id, workspace_id, scan_id,
                  scraper: dict, username: str, found_data: dict,
                  username_info: dict, indicator_type: str = "username") -> dict:
    """Store a found account as Finding + Identity + IdentityLink."""
    counts = {"findings": 0, "identities": 0}
    scraper_name = scraper.get("name", "unknown")
    platform = scraper_name.replace("scraper_", "").split("_")[0]
    extracted = found_data.get("extracted", {})

    # Create Finding
    title = scraper.get("finding_title_template", "Account found: {username} on {platform}")
    try:
        fmt = _SafeFormatDict({"username": username, "platform": platform})
        fmt.update(extracted)
        title = title.format_map(fmt)
    except Exception:
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
        description=f"'{username}' found on {platform} via {'deep ' + indicator_type + ' scan' if found_data.get('pass') == 'deep' else 'Pass 1.5 expansion'}",
        data=_sanitize_for_json({
            "extracted": extracted,
            "url": found_data.get("url"),
            "pass": found_data.get("pass", "1.5"),
            "source_username": username,
            "source_platforms": list(username_info.get("platforms", [])),
        }),
        url=found_data.get("url"),
        indicator_value=username,
        indicator_type=indicator_type,
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


# --- Config overrides for deep scan ---
DEEP_TOTAL_TIMEOUT = 300   # 5 min budget (operator-triggered, can afford more)
DEEP_MAX_SCRAPERS = 80     # More scrapers than auto Pass 1.5 (which caps at 50)
DEEP_RATE_LIMIT_DELAY = 0.3  # Slightly faster (operator chose this, not auto)

# --- Config for generic deep scan ---
INDICATOR_TIMEOUT = {
    "username": 300,
    "email": 180,
    "domain": 120,
    "name": 180,
    "fullname": 180,
    "first_name": 180,
}
INDICATOR_MAX_SCRAPERS = {
    "username": 80,
    "email": 30,
    "domain": 15,
    "name": 15,
    "fullname": 15,
    "first_name": 15,
}


def scan_single_username(target_id, workspace_id, session: Session,
                         username: str, scan_id=None, email=None) -> dict:
    """Backward-compatible wrapper — delegates to scan_single_indicator."""
    return scan_single_indicator(
        target_id, workspace_id, session,
        indicator_type="username", indicator_value=username,
        scan_id=scan_id, email=email,
    )


def scan_single_indicator(target_id, workspace_id, session: Session,
                          indicator_type: str, indicator_value: str,
                          scan_id=None, email=None) -> dict:
    """Deep scan a single indicator across all matching scrapers.

    Generic version of scan_single_username. Loads scrapers by input_type,
    executes them against indicator_value, stores findings tagged pass="deep".
    """
    t0 = time.time()
    result = {
        "indicator_type": indicator_type,
        "indicator_value": indicator_value,
        "scrapers_run": 0,
        "findings_created": 0,
        "identities_created": 0,
        "errors": [],
    }

    value = indicator_value.strip()
    if not value or len(value) < 2:
        result["errors"].append("invalid_value")
        return result

    # For username type, validate
    if indicator_type == "username" and not is_valid_username(value):
        result["errors"].append("invalid_username")
        return result

    # Map indicator_type to scraper input_types
    input_types = _map_indicator_to_input_types(indicator_type)
    if not input_types:
        result["errors"].append(f"no_scrapers_for_type:{indicator_type}")
        return result

    timeout = INDICATOR_TIMEOUT.get(indicator_type, 180)
    max_scrapers = INDICATOR_MAX_SCRAPERS.get(indicator_type, 30)

    try:
        scrapers = _load_scrapers_by_types(session, input_types)
        if not scrapers:
            result["errors"].append("no_enabled_scrapers")
            return result

        logger.info("Deep scan: %s '%s' across %d scrapers for target %s",
                     indicator_type, value, len(scrapers), target_id)

        client = httpx.Client(
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )
        health = _get_health()

        fmt_base = _build_format_kwargs(indicator_type, value, email)

        username_info = {
            "value": value,
            "platforms": set(),
            "confidences": [0.7],
            "score": 2.0,
        }

        try:
            with session.no_autoflush:
                for scraper in scrapers[:max_scrapers]:
                    if time.time() - t0 > timeout:
                        result["errors"].append("timeout")
                        break

                    try:
                        found_data = _execute_scraper_generic(
                            client, scraper, value, indicator_type, fmt_base, health
                        )
                        result["scrapers_run"] += 1

                        if found_data and found_data.get("found"):
                            found_data["pass"] = "deep"
                            created = _store_result(
                                session, target_id, workspace_id, scan_id,
                                scraper, value, found_data, username_info,
                                indicator_type=indicator_type,
                            )
                            if created:
                                result["findings_created"] += created.get("findings", 0)
                                result["identities_created"] += created.get("identities", 0)

                        time.sleep(DEEP_RATE_LIMIT_DELAY)

                    except Exception as e:
                        logger.debug("Deep scan: %s failed for %s: %s",
                                     scraper.get("name"), value, e)
                        result["errors"].append(f"{scraper['name']}:{e}")
                        try:
                            session.rollback()
                        except Exception:
                            pass
        finally:
            client.close()

        if result["findings_created"] > 0:
            session.commit()

        elapsed = time.time() - t0
        logger.info("Deep scan complete: %s '%s' → %d scrapers, %d findings in %.1fs",
                     indicator_type, value, result["scrapers_run"],
                     result["findings_created"], elapsed)

    except Exception:
        logger.exception("Deep scan failed for %s '%s'", indicator_type, value)

    return result


def _map_indicator_to_input_types(indicator_type: str) -> list:
    """Map a finding indicator_type to scraper input_type(s)."""
    mapping = {
        "username": ["username"],
        "email": ["email"],
        "domain": ["domain"],
        "name": ["name", "fullname", "first_name"],
        "fullname": ["name", "fullname", "first_name"],
        "media_mention": ["name", "fullname"],
        "sanctions_match": ["name", "fullname"],
        "corporate_officer": ["name", "fullname"],
        "pep_match": ["name", "fullname"],
    }
    return mapping.get(indicator_type, [])


def _load_scrapers_by_types(session: Session, input_types: list) -> list:
    """Load all enabled scrapers matching any of the given input_types."""
    from sqlalchemy import or_
    scrapers = session.execute(
        select(Scraper).where(
            Scraper.enabled == True,
            or_(*[Scraper.input_type == t for t in input_types])
        )
    ).scalars().all()
    return [s.to_dict() for s in scrapers]


def _build_format_kwargs(indicator_type: str, value: str, email: str = None) -> dict:
    """Build URL template format kwargs based on indicator type."""
    base = _SafeFormatDict({
        "username": value,
        "email": value,
        "input": value,
        "domain": "",
        "first_name": value,
        "fullname": value,
        "fullname_encoded": value.replace(" ", "+"),
        "name": value,
        "email_md5": hashlib.md5(value.encode()).hexdigest(),
    })

    if indicator_type == "email":
        parts = value.split("@")
        base["domain"] = parts[1] if len(parts) > 1 else ""
        base["username"] = parts[0] if len(parts) > 0 else value

    if indicator_type == "domain":
        base["domain"] = value

    if indicator_type in ("name", "fullname", "media_mention", "sanctions_match",
                          "corporate_officer", "pep_match"):
        parts = value.split()
        base["first_name"] = parts[0] if parts else value
        base["last_name"] = parts[-1] if len(parts) > 1 else ""
        base["fullname"] = value
        base["fullname_encoded"] = value.replace(" ", "+")

    return base


def _execute_scraper_generic(client, scraper, value, indicator_type, fmt_base, health):
    """Execute a scraper with generic format kwargs."""
    url = ""
    try:
        url = scraper.get("url_template", "").format_map(fmt_base)
        if not url or "{" in url:
            return {"found": False, "error": "template_incomplete", "url": url}

        headers = dict(scraper.get("headers") or {})
        headers.setdefault("User-Agent", USER_AGENT)

        method = (scraper.get("method") or "GET").upper()
        t0_req = time.time()

        if method == "POST":
            body = (scraper.get("body_template") or "").format_map(fmt_base)
            response = client.post(url, content=body, headers=headers)
        else:
            response = client.get(url, headers=headers)

        elapsed_ms = int((time.time() - t0_req) * 1000)

        if health:
            health.record(scraper.get("name", "unknown"), response.status_code, elapsed_ms)

        content = response.text
        found = _check_found(content, response.status_code, scraper)

        if not found:
            return {"found": False, "url": url, "status_code": response.status_code}

        extracted = {}
        for rule in scraper.get("extraction_rules") or []:
            val = _extract(content, rule)
            if val is not None:
                extracted[rule["field"]] = val

        return {
            "found": True,
            "extracted": extracted,
            "url": url,
            "status_code": response.status_code,
        }

    except httpx.TimeoutException:
        return {"found": False, "error": "timeout", "url": url}
    except Exception as e:
        logger.debug("Generic scraper %s failed: %s", scraper.get("name"), e)
        return {"found": False, "error": str(e), "url": url}
