import logging
import re
import uuid as uuid_mod

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.finding import Finding
from api.models.identity import Identity, IdentityLink
from api.services.layer4.source_scoring import get_source_reliability

logger = logging.getLogger(__name__)

# Patterns for extracting platform info from URLs
URL_PLATFORM_MAP = {
    "twitter.com": "Twitter",
    "x.com": "Twitter",
    "instagram.com": "Instagram",
    "facebook.com": "Facebook",
    "github.com": "GitHub",
    "linkedin.com": "LinkedIn",
    "pinterest.com": "Pinterest",
    "spotify.com": "Spotify",
    "reddit.com": "Reddit",
    "tiktok.com": "TikTok",
    "youtube.com": "YouTube",
    "snapchat.com": "Snapchat",
    "discord.com": "Discord",
}

# Axe 4: Non-social platforms to filter from graph nodes
_NON_SOCIAL_PLATFORMS = {
    "lastpass", "office365", "1password", "bitwarden", "dashlane", "nordpass",
    "keepass", "firefox", "chrome", "safari", "eventbrite", "booking",
}


def _is_valid_extracted_username(username: str) -> bool:
    """Reject noisy username values from finding data."""
    u = username.strip()
    if len(u) < 2:
        return False
    # Reject "X's profile" patterns
    if "'s profile" in u.lower() or u.lower().endswith(" profile"):
        return False
    # Reject single-letter initials: "Steffen H.", "J. Smith"
    parts = u.split()
    if len(parts) >= 2:
        if len(parts[-1].rstrip('.')) <= 1:
            return False
        if len(parts[0]) == 1 or (len(parts[0]) == 2 and parts[0].endswith('.')):
            return False
    # Reject domain-style handles: "user.bsky.social", "user@mastodon.social"
    if u.count('.') >= 2:
        return False
    if '@' in u:
        return False
    # Reject if it's actually a full name with spaces (names are type="name", not username)
    if ' ' in u and all(p[0].isupper() for p in u.split() if p):
        return False
    return True


def _match_url_platform(url):
    """Axe 5: Proper domain matching — check if URL host ends with a known domain."""
    if not url:
        return None, None
    url_lower = url.lower()
    # Strip protocol
    host = url_lower.split("://", 1)[-1].split("/", 1)[0].split("?", 1)[0]
    for domain, name in URL_PLATFORM_MAP.items():
        if host == domain or host.endswith("." + domain):
            return domain, name
    return None, None


def build_graph(target_id, workspace_id, session: Session):
    """Build/update identity graph from findings for a target."""
    findings = session.execute(
        select(Finding).where(
            Finding.target_id == target_id,
            Finding.status == "active",
        )
    ).scalars().all()

    if not findings:
        return

    # Clean up stale identity graph data before rebuilding
    # Delete ALL existing identity links for this target so we rebuild fresh
    existing_ids = session.execute(
        select(Identity.id).where(
            Identity.target_id == target_id,
            Identity.workspace_id == workspace_id,
        )
    ).scalars().all()
    if existing_ids:
        id_set_cleanup = set(existing_ids)
        old_links = session.execute(
            select(IdentityLink).where(
                IdentityLink.workspace_id == workspace_id,
            )
        ).scalars().all()
        for lnk in old_links:
            if lnk.source_id in id_set_cleanup or lnk.dest_id in id_set_cleanup:
                session.delete(lnk)
        # Also delete identity nodes — they'll be recreated
        for iid in existing_ids:
            identity_obj = session.get(Identity, iid)
            if identity_obj:
                session.delete(identity_obj)
        session.flush()

    # Ensure the target email identity node exists
    email_finding = next(
        (f for f in findings if f.indicator_type == "email" and f.indicator_value),
        None,
    )
    email_value = email_finding.indicator_value if email_finding else None

    def get_or_create_identity(type_, value, platform=None, source_module=None, source_finding_id=None):
        existing = session.execute(
            select(Identity).where(
                Identity.workspace_id == workspace_id,
                Identity.target_id == target_id,
                Identity.type == type_,
                Identity.value == value,
            )
        ).scalar_one_or_none()

        if existing:
            # Upgrade confidence if better source
            new_conf = get_source_reliability(source_module) if source_module else 0.5
            if new_conf > existing.confidence:
                existing.confidence = new_conf
            # Upgrade platform if current is missing or generic
            if platform and (not existing.platform or existing.platform in ("unknown", "scraper_engine", "graph_builder")):
                existing.platform = platform
            return existing

        identity = Identity(
            workspace_id=workspace_id,
            target_id=target_id,
            type=type_,
            value=value,
            platform=platform,
            source_module=source_module,
            source_finding=source_finding_id,
            confidence=get_source_reliability(source_module) if source_module else 0.5,
        )
        session.add(identity)
        session.flush()
        return identity

    def get_or_create_link(source_id, dest_id, link_type, source_module=None, evidence=None):
        existing = session.execute(
            select(IdentityLink).where(
                IdentityLink.workspace_id == workspace_id,
                IdentityLink.source_id == source_id,
                IdentityLink.dest_id == dest_id,
                IdentityLink.link_type == link_type,
            )
        ).scalar_one_or_none()

        if existing:
            # Upgrade confidence if better source
            new_conf = get_source_reliability(source_module) if source_module else 0.5
            if new_conf > existing.confidence:
                existing.confidence = new_conf
                existing.source_module = source_module
            return existing

        link = IdentityLink(
            workspace_id=workspace_id,
            source_id=source_id,
            dest_id=dest_id,
            link_type=link_type,
            confidence=get_source_reliability(source_module) if source_module else 0.5,
            source_module=source_module,
            evidence=evidence,
        )
        session.add(link)
        session.flush()
        return link

    # Process each finding
    for f in findings:
        fdata = f.data if isinstance(f.data, dict) else {}
        indicator_node = None

        # Create identity for the indicator
        if f.indicator_value and f.indicator_type:
            # Axe 2: Skip URL-value indicator nodes (social_url type has URLs as values — noise)
            if f.indicator_type == "social_url":
                # Axe 1b: social_url indicators (username_hunter) → extract username + link email→platform
                extracted_username = fdata.get("username")
                extracted_platform = fdata.get("platform", "").replace("_profile", "").replace("_scraper", "").replace("_search", "").strip()

                if extracted_username and extracted_platform and _is_valid_extracted_username(extracted_username):
                    # Axe 4: Skip non-social platforms
                    if extracted_platform.lower() in _NON_SOCIAL_PLATFORMS:
                        continue

                    # Create username node
                    username_node = get_or_create_identity(
                        "username", extracted_username,
                        platform=extracted_platform,
                        source_module=f.module,
                        source_finding_id=f.id,
                    )
                    # Axe 3: Normalize social_url value with .title()
                    platform_node = get_or_create_identity(
                        "social_url", extracted_platform.title(),
                        platform=extracted_platform.lower(),
                        source_module=f.module,
                        source_finding_id=f.id,
                    )
                    # Link email → platform (registered_with)
                    if email_value:
                        email_node = get_or_create_identity(
                            "email", email_value, source_module=f.module,
                        )
                        get_or_create_link(
                            email_node.id, platform_node.id,
                            "registered_with",
                            source_module=f.module,
                            evidence={"finding_id": str(f.id), "url": f.url},
                        )
                        # Link email → username (same_person)
                        get_or_create_link(
                            email_node.id, username_node.id,
                            "same_person",
                            source_module=f.module,
                        )
                    # Link username → platform (identified_as)
                    get_or_create_link(
                        username_node.id, platform_node.id,
                        "identified_as",
                        source_module=f.module,
                        evidence={"finding_id": str(f.id), "url": f.url},
                    )
                    indicator_node = username_node
                continue

            platform = None
            if f.indicator_type == "email":
                platform = f.indicator_value.split("@")[1] if "@" in f.indicator_value else None
            elif f.indicator_type == "username":
                platform = (
                    fdata.get("platform") or
                    fdata.get("name") or  # holehe uses "name"
                    fdata.get("network") or
                    fdata.get("service") or
                    None
                )
                if platform:
                    platform = platform.replace("_profile", "").replace("_scraper", "").replace("_search", "").strip()

            indicator_node = get_or_create_identity(
                f.indicator_type, f.indicator_value,
                platform=platform,
                source_module=f.module,
                source_finding_id=f.id,
            )

            # Social account findings → create platform node + link
            if f.category == "social_account":
                site_name = f.title.split(" on ")[-1] if " on " in f.title else f.module
                # Axe 5: Proper domain matching via helper
                platform_domain, matched_name = _match_url_platform(f.url)
                if matched_name:
                    site_name = matched_name
                elif not platform_domain:
                    # Fallback: match by site_name
                    for domain, name in URL_PLATFORM_MAP.items():
                        if name.lower() == site_name.lower():
                            platform_domain = domain
                            site_name = name
                            break

                # For scraper findings, extract platform from data
                if f.module == "scraper_engine" and fdata:
                    scraper_platform = fdata.get("platform", "") or fdata.get("scraper", "")
                    if scraper_platform:
                        # Axe 4: Skip non-social platforms
                        if scraper_platform.lower().replace("_profile", "").replace("_scraper", "").strip() in _NON_SOCIAL_PLATFORMS:
                            continue
                        site_name = scraper_platform.replace("_profile", "").replace("_scraper", "").replace("_search", "").title()

                # Axe 1: Extract username from f.data for social_account findings
                data_username = fdata.get("username")
                if data_username and isinstance(data_username, str) and len(data_username.strip()) >= 2 and _is_valid_extracted_username(data_username.strip()):
                    username_node = get_or_create_identity(
                        "username", data_username.strip(),
                        platform=site_name.lower() if site_name else f.module,
                        source_module=f.module,
                        source_finding_id=f.id,
                    )
                    # Link username → name (identified_as) handled in name extraction below
                    # Link email → username (same_person)
                    if email_value:
                        email_node = get_or_create_identity(
                            "email", email_value, source_module=f.module,
                        )
                        get_or_create_link(
                            email_node.id, username_node.id,
                            "same_person",
                            source_module=f.module,
                        )

                # Axe 4: Skip non-social platforms (check site_name before node creation)
                clean_site = (site_name or "").lower().replace("_profile", "").replace("_scraper", "").strip()
                if clean_site in _NON_SOCIAL_PLATFORMS:
                    continue

                # Axe 3: Normalize social_url value with .title()
                platform_node = get_or_create_identity(
                    "social_url", site_name.title() if site_name else f.module.title(),
                    platform=platform_domain or site_name.lower() if site_name else f.module,
                    source_module=f.module,
                    source_finding_id=f.id,
                )

                # Link email → platform (for email indicator findings)
                if email_value and f.indicator_type == "email":
                    get_or_create_link(
                        indicator_node.id, platform_node.id,
                        "registered_with",
                        source_module=f.module,
                        evidence={"finding_id": str(f.id), "url": f.url},
                    )
                # Link email → platform for username-based findings (scrapers)
                elif email_value and f.indicator_type == "username":
                    email_node = get_or_create_identity(
                        "email", email_value, source_module=f.module,
                    )
                    get_or_create_link(
                        email_node.id, platform_node.id,
                        "registered_with",
                        source_module=f.module,
                        evidence={"finding_id": str(f.id), "url": f.url},
                    )

            # Breach findings → create breach node + link
            elif f.category == "breach":
                breach_name = fdata.get("Name", f.title) if fdata else f.title
                breach_node = get_or_create_identity(
                    "breach", breach_name,
                    platform="haveibeenpwned.com",
                    source_module=f.module,
                    source_finding_id=f.id,
                )
                get_or_create_link(
                    indicator_node.id, breach_node.id,
                    "exposed_in",
                    source_module=f.module,
                    evidence={"finding_id": str(f.id)},
                )

            # Username findings → link to email if we have one
            elif f.indicator_type == "username" and email_value:
                email_node = get_or_create_identity(
                    "email", email_value,
                    source_module=f.module,
                )
                get_or_create_link(
                    email_node.id, indicator_node.id,
                    "same_person",
                    source_module=f.module,
                )

        # Extract name nodes from finding data
        data = fdata.copy()
        if "extracted" in data and isinstance(data["extracted"], dict):
            for k, v in data["extracted"].items():
                if k not in data and v is not None:
                    data[k] = v

        # Name validation constants for graph nodes
        _NAME_PLATFORM_BLACKLIST = {
            "lastpass", "office365", "spotify", "eventbrite", "firefox", "telegram",
            "chrome", "safari", "1password", "bitwarden", "dashlane", "nordpass",
            "keepass", "reddit", "github", "twitter", "instagram", "facebook",
        }

        for name_field in ("name", "display_name", "full_name", "realname"):
            name_val = data.get(name_field)
            if name_val and isinstance(name_val, str) and len(name_val.strip()) >= 3:
                name_clean = name_val.strip()

                # Reject single-letter last initial: "Steffen H." → reject
                parts = name_clean.split()
                if len(parts) >= 2 and len(parts[-1].rstrip('.')) <= 1:
                    continue
                # Reject single-letter first initial: "J. Smith"
                if parts and (len(parts[0]) == 1 or (len(parts[0]) == 2 and parts[0].endswith('.'))):
                    continue
                # Reject "'s profile" patterns: "stheis's profile"
                if "'s profile" in name_clean.lower() or name_clean.lower().endswith(" profile"):
                    continue
                # Reject platform names
                if name_clean.lower() in _NAME_PLATFORM_BLACKLIST:
                    continue
                # Reject too-short single words
                if len(parts) == 1 and len(parts[0]) < 4:
                    continue

                # Lazy-load blacklist once
                if not hasattr(build_graph, '_blacklist'):
                    try:
                        from api.services.layer4.profile_aggregator import _load_blacklist, _is_valid_name_db
                        build_graph._blacklist = _load_blacklist(session)
                        build_graph._is_valid = _is_valid_name_db
                    except Exception:
                        build_graph._blacklist = []
                        build_graph._is_valid = lambda n, b: len(n.strip()) >= 3

                if build_graph._is_valid(name_clean, build_graph._blacklist):
                    name_node = get_or_create_identity(
                        "name", name_clean,
                        platform=f.module,
                        source_module=f.module,
                        source_finding_id=f.id,
                    )
                    # Link name to finding's indicator — but ONLY if indicator is a
                    # username (not email). email→name should be "associated_with".
                    if indicator_node and f.indicator_value and f.indicator_type:
                        if f.indicator_type == "username":
                            get_or_create_link(
                                indicator_node.id, name_node.id,
                                "identified_as",
                                source_module=f.module,
                                evidence={"name": name_clean, "finding_id": str(f.id)},
                            )
                        elif f.indicator_type == "email" and email_value:
                            # email→name is a weaker signal
                            get_or_create_link(
                                indicator_node.id, name_node.id,
                                "associated_with",
                                source_module=f.module,
                                evidence={"name": name_clean, "finding_id": str(f.id)},
                            )

        # Extract location nodes
        for loc_field in ("location", "country", "city"):
            loc_val = data.get(loc_field)
            if loc_val and isinstance(loc_val, str) and len(loc_val.strip()) >= 2:
                # Skip geoip module locations (mail server, not user)
                if f.module in ("geoip", "maxmind_geo"):
                    continue
                loc_node = get_or_create_identity(
                    "location", loc_val.strip(),
                    source_module=f.module,
                )
                if indicator_node and f.indicator_value and f.indicator_type:
                    get_or_create_link(
                        indicator_node.id, loc_node.id,
                        "located_in",
                        source_module=f.module,
                    )

    # --- Catch-all: ensure EVERY node links to the email anchor ---
    # This guarantees graph connectivity for PageRank propagation.
    if email_value:
        email_anchor = get_or_create_identity(
            "email", email_value, source_module="graph_builder",
        )
        all_identities = session.execute(
            select(Identity).where(
                Identity.workspace_id == workspace_id,
                Identity.target_id == target_id,
            )
        ).scalars().all()

        # Build set of nodes already linked to anything
        linked_nodes = set()
        all_links = session.execute(
            select(IdentityLink).where(
                IdentityLink.workspace_id == workspace_id,
            )
        ).scalars().all()
        id_set = {i.id for i in all_identities}
        for lnk in all_links:
            if lnk.source_id in id_set:
                linked_nodes.add(lnk.source_id)
            if lnk.dest_id in id_set:
                linked_nodes.add(lnk.dest_id)

        # Connect orphan nodes to email anchor
        for identity in all_identities:
            if identity.id == email_anchor.id:
                continue
            if identity.id not in linked_nodes:
                get_or_create_link(
                    email_anchor.id, identity.id,
                    "associated_with",
                    source_module="graph_builder",
                )

        # NOTE: username→name links are created per-finding above (identified_as)
        # Do NOT add N×N cross-linking here — it creates false persona merges

    session.commit()

    # Debug: verify links persisted after commit
    from sqlalchemy import func as sa_func
    link_count = session.execute(
        select(sa_func.count()).select_from(IdentityLink).where(
            IdentityLink.workspace_id == workspace_id,
        )
    ).scalar()
    node_count = session.execute(
        select(sa_func.count()).select_from(Identity).where(
            Identity.target_id == target_id,
            Identity.workspace_id == workspace_id,
        )
    ).scalar()
    logger.info("GRAPH_DEBUG: %d identity_links, %d identity_nodes in DB after commit for target %s",
                link_count, node_count, target_id)
