"""Profile Aggregator — merge findings into a unified person profile."""
import logging
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.finding import Finding
from api.models.target import Target

logger = logging.getLogger(__name__)


def aggregate_profile(target_id, workspace_id, session: Session) -> dict:
    """Build a unified profile from all findings for a target. Sync for Celery."""
    findings = session.execute(
        select(Finding).where(
            Finding.target_id == target_id,
            Finding.workspace_id == workspace_id,
            Finding.status == "active",
        )
    ).scalars().all()

    profile = {
        "names": [],
        "avatars": [],
        "bio": None,
        "location": None,
        "company": None,
        "title": None,
        "age_range": None,
        "gender": None,
        "website": None,
        "social_profiles": [],
        "emails": [],
        "usernames": [],
        "breach_summary": {"count": 0, "sources": [], "credentials_leaked": False},
        "reputation": None,
        "email_security": {},
        "dns_provider": None,
        "email_provider": None,
        "geo_locations": [],
        "domains": [],
        "first_seen": None,
        "data_sources": [],
    }

    seen_names = set()
    seen_avatars = set()
    seen_socials = set()
    seen_emails = set()
    seen_usernames = set()
    breach_names = set()
    sources = set()

    for f in findings:
        data = f.data or {}
        source = data.get("source") or f.module
        sources.add(source)

        # --- Names ---
        for name_key in ("name", "full_name", "display_name", "displayName"):
            name = data.get(name_key, "")
            if name and name not in seen_names and len(name) > 1:
                seen_names.add(name)
                profile["names"].append({"value": name, "source": source})

        # --- Avatars ---
        for avatar_key in ("avatar_url", "photo_url", "avatar", "picture"):
            avatar = data.get(avatar_key, "")
            if avatar and avatar not in seen_avatars:
                seen_avatars.add(avatar)
                profile["avatars"].append({"url": avatar, "source": source})

        # --- Bio ---
        for bio_key in ("bio", "about", "description"):
            bio = data.get(bio_key, "")
            if bio and not profile["bio"]:
                profile["bio"] = bio[:500]

        # --- Location ---
        # ONLY use profile-sourced locations, NOT geoip (server locations)
        if f.module not in ("geoip", "maxmind_geo") and f.category != "geolocation":
            for loc_key in ("location", "currentLocation"):
                loc = data.get(loc_key, "")
                if loc and not profile["location"]:
                    profile["location"] = loc

        # --- Company/Title ---
        if data.get("company") and not profile["company"]:
            profile["company"] = data["company"]
        if data.get("organization") and not profile["company"]:
            profile["company"] = data["organization"]
        if data.get("title") and not profile["title"]:
            profile["title"] = data["title"]

        # --- Age/Gender (FullContact) ---
        if data.get("age_range") and not profile["age_range"]:
            profile["age_range"] = data["age_range"]
        if data.get("gender") and not profile["gender"]:
            profile["gender"] = data["gender"]

        # --- Website ---
        if data.get("blog") and not profile["website"]:
            profile["website"] = data["blog"]
        if data.get("website") and not profile["website"]:
            profile["website"] = data["website"]

        # --- Social profiles ---
        if f.category == "social_account":
            platform = data.get("platform") or data.get("network") or data.get("service") or ""
            url = f.url or data.get("url", "")
            username = data.get("username") or data.get("handle") or data.get("login") or ""
            key = f"{platform}:{username or url}"
            if key not in seen_socials and (platform or url):
                seen_socials.add(key)
                profile["social_profiles"].append({
                    "platform": platform,
                    "url": url,
                    "username": username,
                    "source": source,
                })

        # --- Alternate emails ---
        if data.get("alt_email"):
            alt = data["alt_email"]
            if alt not in seen_emails:
                seen_emails.add(alt)
                profile["emails"].append({"value": alt, "source": source})

        # --- Usernames ---
        for uname_key in ("username", "login", "handle", "preferredUsername"):
            uname = data.get(uname_key, "")
            if uname and uname not in seen_usernames and len(uname) >= 3:
                seen_usernames.add(uname)
                profile["usernames"].append({"value": uname, "source": source})

        # --- Breaches ---
        if f.category == "breach":
            breach_name = data.get("breach_name") or data.get("Name") or f.title
            if breach_name not in breach_names:
                breach_names.add(breach_name)
                profile["breach_summary"]["count"] += 1
                profile["breach_summary"]["sources"].append(breach_name)
            if data.get("credentials_leaked"):
                profile["breach_summary"]["credentials_leaked"] = True

        # --- Reputation (EmailRep) ---
        if data.get("reputation") and not profile["reputation"]:
            profile["reputation"] = {
                "level": data["reputation"],
                "suspicious": data.get("suspicious", False),
                "first_seen": data.get("first_seen"),
                "source": source,
            }

        # --- Email security ---
        if data.get("has_spf") is not None:
            profile["email_security"] = {
                "spf": data.get("has_spf"),
                "dmarc": data.get("has_dmarc"),
                "dkim": data.get("has_dkim"),
                "security_level": data.get("security_level", "unknown"),
                "source": source,
            }

        # --- DNS/Email provider ---
        if data.get("ns_provider") and not profile["dns_provider"]:
            profile["dns_provider"] = data["ns_provider"]
        if data.get("provider") and f.module == "dns_deep" and not profile["email_provider"]:
            profile["email_provider"] = data["provider"]

        # --- Geo locations ---
        if f.category == "geolocation":
            lat = data.get("latitude") or data.get("lat")
            lon = data.get("longitude") or data.get("lon")
            if lat and lon:
                profile["geo_locations"].append({
                    "lat": lat,
                    "lon": lon,
                    "city": data.get("city", ""),
                    "country": data.get("country", ""),
                    "source": source,
                })

        # --- First seen ---
        if data.get("first_seen") and not profile["first_seen"]:
            profile["first_seen"] = data["first_seen"]

    profile["data_sources"] = sorted(sources)
    profile["breach_summary"]["sources"] = profile["breach_summary"]["sources"][:20]

    # Pick primary name and avatar
    profile["primary_name"] = profile["names"][0]["value"] if profile["names"] else None
    profile["primary_avatar"] = profile["avatars"][0]["url"] if profile["avatars"] else None

    # Store on target
    target = session.execute(
        select(Target).where(Target.id == target_id, Target.workspace_id == workspace_id)
    ).scalar_one_or_none()
    if target:
        target.profile_data = profile
        if profile["primary_name"] and not target.display_name:
            target.display_name = profile["primary_name"]
        if profile["primary_avatar"] and not target.avatar_url:
            target.avatar_url = profile["primary_avatar"]
        session.commit()

    logger.info("Profile aggregated for target %s: %d sources, %d social profiles, %d breaches",
                target_id, len(sources), len(profile["social_profiles"]), profile["breach_summary"]["count"])
    return profile
