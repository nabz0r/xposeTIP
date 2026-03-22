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
        # Create identity for the indicator
        if f.indicator_value and f.indicator_type:
            platform = None
            if f.indicator_type == "email":
                platform = f.indicator_value.split("@")[1] if "@" in f.indicator_value else None

            indicator_node = get_or_create_identity(
                f.indicator_type, f.indicator_value,
                platform=platform,
                source_module=f.module,
                source_finding_id=f.id,
            )

            # Social account findings → create platform node + link
            if f.category == "social_account":
                site_name = f.title.split(" on ")[-1] if " on " in f.title else f.module
                platform_domain = None
                for domain, name in URL_PLATFORM_MAP.items():
                    if name.lower() == site_name.lower() or domain in (f.url or "").lower():
                        platform_domain = domain
                        site_name = name
                        break

                # For scraper findings, extract platform from data
                if f.module == "scraper_engine" and f.data:
                    scraper_platform = f.data.get("platform", "") or f.data.get("scraper", "")
                    if scraper_platform:
                        site_name = scraper_platform.replace("_profile", "").replace("_scraper", "").replace("_search", "").title()

                platform_node = get_or_create_identity(
                    "social_url", site_name,
                    platform=platform_domain or site_name.lower(),
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
                breach_name = f.data.get("Name", f.title) if f.data else f.title
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
        data = f.data if isinstance(f.data, dict) else {}
        if "extracted" in data and isinstance(data["extracted"], dict):
            for k, v in data["extracted"].items():
                if k not in data and v is not None:
                    data[k] = v

        for name_field in ("name", "display_name", "full_name", "realname"):
            name_val = data.get(name_field)
            if name_val and isinstance(name_val, str) and len(name_val.strip()) >= 3:
                # Lazy-load blacklist once
                if not hasattr(build_graph, '_blacklist'):
                    try:
                        from api.services.layer4.profile_aggregator import _load_blacklist, _is_valid_name_db
                        build_graph._blacklist = _load_blacklist(session)
                        build_graph._is_valid = _is_valid_name_db
                    except Exception:
                        build_graph._blacklist = []
                        build_graph._is_valid = lambda n, b: len(n.strip()) >= 3

                if build_graph._is_valid(name_val, build_graph._blacklist):
                    name_node = get_or_create_identity(
                        "name", name_val.strip(),
                        platform=f.module,
                        source_module=f.module,
                        source_finding_id=f.id,
                    )
                    if f.indicator_value and f.indicator_type:
                        get_or_create_link(
                            indicator_node.id, name_node.id,
                            "identified_as",
                            source_module=f.module,
                            evidence={"name": name_val, "finding_id": str(f.id)},
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
                if f.indicator_value and f.indicator_type:
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
    logger.info("Graph built for target %s", target_id)
