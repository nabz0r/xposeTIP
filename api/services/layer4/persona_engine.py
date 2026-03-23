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


def _is_valid_persona_name(name):
    """Reject platform names and single-letter initials."""
    if not name or len(name) < 3:
        return False
    parts = name.strip().split()
    # Reject single-letter last initial: "Steffen H.", "John D."
    if len(parts) >= 2 and len(parts[-1].rstrip(".")) <= 1:
        return False
    # Reject single-letter first initial: "J. Smith"
    if parts and (len(parts[0]) == 1 or (len(parts[0]) == 2 and parts[0].endswith("."))):
        return False
    return True


_PLATFORM_BLACKLIST = {
    "lastpass", "office365", "1password", "bitwarden", "dashlane", "keepass",
    "nordpass", "firefox", "chrome", "safari", "edge", "opera",
}


def _is_valid_extracted_username(username: str) -> bool:
    """Same validation as graph_builder — reject noisy values."""
    u = username.strip()
    if len(u) < 2:
        return False
    if "'s " in u.lower() or u.lower().endswith("'s") or "profile" in u.lower():
        return False
    parts = u.split()
    if len(parts) >= 2:
        if len(parts[-1].rstrip('.')) <= 1:
            return False
        if len(parts[0].rstrip('.')) <= 1:
            return False
    if u.count('.') >= 2:
        return False
    if '@' in u:
        return False
    # Full names → not usernames
    if ' ' in u:
        words = [p for p in u.split() if p]
        if len(words) >= 2 and all(w[0].isupper() for w in words):
            return False
    return True


def _cluster_from_graph(identities, graph_context, db_blacklist):
    """Build personas from graph clusters. Each cluster = one persona."""
    try:
        personas = []
        clusters = graph_context["clusters"]
        node_scores = graph_context["node_scores"]

        for idx, cluster in enumerate(clusters):
            cluster_nodes = set(cluster["nodes"])

            # Debug: log cluster composition
            cluster_types = defaultdict(int)
            for i in identities:
                if i.id in cluster_nodes:
                    cluster_types[i.type] += 1
            logger.info(
                "PERSONA_DEBUG: Cluster %d: %d nodes, types=%s",
                idx, len(cluster_nodes), dict(cluster_types),
            )

            # Find username nodes in this cluster
            cluster_usernames = set()
            cluster_platforms = set()
            cluster_names = set()
            for i in identities:
                if i.id in cluster_nodes:
                    if i.type == "username" and _is_valid_username(i.value or "", db_blacklist):
                        cluster_usernames.add(i.value)
                    # Collect name nodes for persona labeling
                    if i.type == "name":
                        cluster_names.add(i.value)
                    # Collect platforms from social_url nodes (e.g. "Steam", "Medium")
                    if i.type == "social_url":
                        url_plat = (i.platform or i.value or "").strip()
                        if url_plat and url_plat.lower() not in _PLATFORM_BLACKLIST:
                            cluster_platforms.add(url_plat)
                    plat = i.platform or ""
                    # Skip generic module names — not real platforms
                    if plat and plat not in ("scraper_engine", "graph_builder", "unknown"):
                        # Clean scraper suffixes
                        plat_clean = plat.replace("_profile", "").replace("_scraper", "").replace("_search", "").strip()
                        if plat_clean:
                            cluster_platforms.add(plat_clean)

            # Filter out non-platform entries (password managers, browsers)
            cluster_platforms = {p for p in cluster_platforms if p.lower() not in _PLATFORM_BLACKLIST}

            logger.info(
                "PERSONA_DEBUG: Cluster %d: usernames=%s, names=%s, platforms(%d)=%s",
                idx, sorted(cluster_usernames), sorted(cluster_names),
                len(cluster_platforms), sorted(cluster_platforms)[:10],
            )

            # Sprint 50: Accept clusters with usernames OR names (not just usernames)
            if not cluster_usernames and not cluster_names:
                continue

            # Pick best label: prefer username, then name
            if cluster_usernames:
                valid_usernames = [u for u in cluster_usernames if _is_valid_persona_name(u)]
                label_candidates = valid_usernames if valid_usernames else list(cluster_usernames)
            else:
                valid_names = [n for n in cluster_names if _is_valid_persona_name(n)]
                label_candidates = valid_names if valid_names else list(cluster_names)

            best_label = max(
                label_candidates,
                key=lambda u: node_scores.get(
                    next((i.id for i in identities if i.value == u), None), 0
                )
            )

            risk_indicators = []
            if len(cluster_usernames) > 1:
                risk_indicators.append(f"username reuse across {len(cluster_platforms)} platforms")

            variants = [u for u in cluster_usernames if u != best_label]
            if variants:
                risk_indicators.append(f"username variants detected ({', '.join(sorted(variants)[:3])})")

            all_identifiers = sorted(cluster_usernames | cluster_names)

            personas.append({
                "id": f"persona_{idx}",
                "label": best_label,
                "usernames": sorted(cluster_usernames) if cluster_usernames else sorted(cluster_names),
                "platforms": sorted(cluster_platforms),
                "accounts_count": len(cluster_platforms),
                "confidence": cluster["confidence"],
                "density": cluster["density"],
                "is_primary": idx == 0,
                "risk_indicators": risk_indicators,
                "graph_cluster_size": cluster["node_count"],
                "names": sorted(cluster_names),
            })

        logger.info("PERSONA_DEBUG: _cluster_from_graph returning %d personas", len(personas))
        return personas
    except Exception:
        logger.exception("PERSONA: graph-based clustering crashed")
        return []


def cluster_personas(target_id, workspace_id, session: Session, graph_context=None) -> list[dict]:
    """
    Cluster identity nodes into personas.

    Uses graph clusters if graph_context is available (Markov chain integration),
    else falls back to SequenceMatcher-based clustering.

    Returns list of persona dicts.
    """
    db_blacklist = _load_username_blacklist(session)

    # Load identities (from graph_context or DB)
    if graph_context and graph_context.get("identities"):
        identities = graph_context["identities"]
    else:
        identities = session.execute(
            select(Identity).where(
                Identity.target_id == target_id,
                Identity.workspace_id == workspace_id,
            )
        ).scalars().all()

    # GRAPH-BASED clustering: use connected components
    if graph_context and graph_context.get("clusters"):
        logger.info(
            "PERSONA: graph path starting with %d clusters, %d identities",
            len(graph_context["clusters"]), len(identities),
        )
        personas = _cluster_from_graph(identities, graph_context, db_blacklist)
        logger.info(
            "PERSONA: graph path returned %d personas, falling back: %s",
            len(personas) if personas else 0, not personas,
        )
        if personas:
            # Tag identities in DB with persona ID (usernames + names)
            persona_label_map = {}
            for p in personas:
                for uname in p["usernames"]:
                    persona_label_map[uname.lower()] = p["id"]
                for nm in p.get("names", []):
                    persona_label_map[nm.lower()] = p["id"]

            for identity in identities:
                if identity.value and identity.value.lower() in persona_label_map:
                    meta = dict(identity.metadata_ or {})
                    meta["persona"] = persona_label_map[identity.value.lower()]
                    identity.metadata_ = meta

            session.commit()
            logger.info(
                "Persona clustering (graph) for target %s: %d personas from %d clusters",
                target_id, len(personas), len(graph_context["clusters"]),
            )
            return personas

    # FALLBACK: SequenceMatcher-based clustering (existing behavior)
    logger.info("PERSONA: falling back to SequenceMatcher for target %s", target_id)
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
        # Sprint 50: reject noisy usernames (profile suffixes, domain handles, full names)
        if not _is_valid_extracted_username(username):
            continue

        platform = (
            data.get("platform") or data.get("network") or
            data.get("service") or ""
        ).lower().replace("_profile", "").replace("_scraper", "").replace("_search", "").strip()

        # Scraper engine: extract actual platform from scraper name or data
        if not platform and f.module == "scraper_engine":
            scraper_name = data.get("scraper", "")
            if scraper_name:
                platform = scraper_name.replace("_profile", "").replace("_scraper", "").replace("_search", "").strip()

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

    logger.info(
        "PERSONA_FALLBACK: %d usernames after validation: %s",
        len(username_platforms), list(username_platforms.keys()),
    )

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
