"""Persona Clustering Engine — groups identity nodes into behavioral personas."""

import logging
import re
from collections import defaultdict
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.finding import Finding
from api.models.identity import Identity

logger = logging.getLogger(__name__)

# Hardcoded fallback blacklist for usernames
_USERNAME_BLACKLIST = {
    "unknown", "user", "admin", "test", "null", "none", "default", "anonymous",
    "noreply", "no-reply", "support", "info", "contact", "hello", "postmaster",
    "webmaster", "mailer-daemon",
}


def _load_username_blacklist(session: Session) -> list[dict]:
    """Load name blacklist from DB for username filtering."""
    try:
        from api.models.name_blacklist import NameBlacklist
        rows = session.execute(select(NameBlacklist)).scalars().all()
        return [{"pattern": r.pattern, "type": r.type} for r in rows]
    except Exception:
        return []


def _is_valid_username(username: str, db_blacklist: list[dict]) -> bool:
    """Check username against blacklist. Returns True if valid."""
    val = username.strip().lower()
    if len(val) < 2:
        return False
    # DB blacklist
    for entry in db_blacklist:
        p = entry["pattern"].lower()
        if entry["type"] == "exact" and val == p:
            return False
        if entry["type"] == "contains" and p in val:
            return False
        if entry["type"] == "regex":
            try:
                if re.match(entry["pattern"], username, re.IGNORECASE):
                    return False
            except Exception:
                pass
    # Hardcoded fallback
    if val in _USERNAME_BLACKLIST:
        return False
    return True


def cluster_personas(target_id, workspace_id, session: Session) -> list[dict]:
    """
    Cluster identity nodes into personas based on username similarity,
    platform overlap, and temporal proximity.

    Returns list of persona dicts.
    """
    db_blacklist = _load_username_blacklist(session)

    findings = session.execute(
        select(Finding).where(
            Finding.target_id == target_id,
            Finding.workspace_id == workspace_id,
            Finding.status == "active",
        )
    ).scalars().all()

    # Extract username → platforms mapping
    username_platforms = defaultdict(set)
    username_sources = defaultdict(set)
    username_urls = defaultdict(list)

    for f in findings:
        data = f.data or {}
        if "extracted" in data and isinstance(data["extracted"], dict):
            for k, v in data["extracted"].items():
                if k not in data and v is not None:
                    data[k] = v

        username = (
            data.get("username") or data.get("handle") or
            data.get("login") or data.get("preferredUsername") or ""
        ).strip()

        # Fall back to indicator_value for username-type findings
        if not username and f.indicator_type == "username":
            username = (f.indicator_value or "").strip()

        if not username or len(username) < 2:
            continue

        # Filter through blacklist
        if not _is_valid_username(username, db_blacklist):
            continue

        platform = (
            data.get("platform") or data.get("network") or
            data.get("service") or ""
        ).lower().replace("_profile", "").replace("_scraper", "").replace("_search", "").strip()

        if not platform and f.url:
            import urllib.parse
            try:
                domain = urllib.parse.urlparse(f.url).netloc.replace("www.", "")
                platform = domain.split(".")[0]
            except Exception:
                pass

        if not platform:
            platform = f.module

        username_platforms[username].add(platform)
        username_sources[username].add(f.module)
        if f.url:
            username_urls[username].append(f.url)

    if not username_platforms:
        return []

    # Cluster similar usernames together
    usernames = list(username_platforms.keys())
    clusters = []
    assigned = set()

    for i, u1 in enumerate(usernames):
        if u1 in assigned:
            continue

        cluster = [u1]
        assigned.add(u1)

        for j, u2 in enumerate(usernames):
            if j <= i or u2 in assigned:
                continue

            similarity = SequenceMatcher(None, u1.lower(), u2.lower()).ratio()

            u1l, u2l = u1.lower(), u2.lower()
            contains = u1l in u2l or u2l in u1l

            base1 = re.sub(r'[\d_\-]+$', '', u1l)
            base2 = re.sub(r'[\d_\-]+$', '', u2l)
            same_base = base1 == base2 and len(base1) >= 2

            if similarity > 0.7 or contains or same_base:
                cluster.append(u2)
                assigned.add(u2)

        clusters.append(cluster)

    # Build persona objects
    personas = []
    for idx, cluster in enumerate(clusters):
        all_platforms = set()
        all_urls = []
        all_sources = set()

        for username in cluster:
            all_platforms.update(username_platforms[username])
            all_urls.extend(username_urls[username])
            all_sources.update(username_sources[username])

        label = max(cluster, key=lambda u: len(username_platforms[u]))

        source_diversity = min(1.0, len(all_sources) / 5)
        platform_consistency = min(1.0, len(all_platforms) / 3)
        confidence = round((source_diversity * 0.6 + platform_consistency * 0.4), 2)

        risk = []
        if len(all_platforms) >= 3:
            risk.append(f"username_reuse_across_{len(all_platforms)}_platforms")
        if len(cluster) > 1:
            risk.append(f"username_variants_detected ({', '.join(cluster)})")

        personas.append({
            "id": f"persona_{idx}",
            "label": label,
            "usernames": sorted(cluster),
            "platforms": sorted(all_platforms),
            "accounts_count": len(all_platforms),
            "urls": all_urls[:10],
            "confidence": confidence,
            "is_primary": False,
            "risk_indicators": risk,
        })

    # Mark primary persona (most platforms)
    if personas:
        personas.sort(key=lambda p: p["accounts_count"], reverse=True)
        personas[0]["is_primary"] = True

    # Tag identities in DB with persona ID
    identities = session.execute(
        select(Identity).where(
            Identity.target_id == target_id,
            Identity.workspace_id == workspace_id,
        )
    ).scalars().all()

    persona_label_map = {}
    for p in personas:
        for uname in p["usernames"]:
            persona_label_map[uname.lower()] = p["id"]

    for identity in identities:
        if identity.value and identity.value.lower() in persona_label_map:
            meta = dict(identity.metadata_ or {})
            meta["persona"] = persona_label_map[identity.value.lower()]
            identity.metadata_ = meta

    session.commit()

    logger.info(
        "Persona clustering for target %s: %d personas from %d usernames",
        target_id, len(personas), len(usernames),
    )

    return personas
