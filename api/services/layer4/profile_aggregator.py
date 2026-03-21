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
    # Deduplicate: keep latest finding per (module, title) — Python-side
    all_findings = session.execute(
        select(Finding).where(
            Finding.target_id == target_id,
            Finding.workspace_id == workspace_id,
            Finding.status == "active",
        )
    ).scalars().all()
    seen = {}
    for f in all_findings:
        key = (f.module, f.title)
        existing = seen.get(key)
        if existing is None or (f.created_at and (not existing.created_at or f.created_at > existing.created_at)):
            seen[key] = f
    findings = list(seen.values())

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
        "identity_estimation": {
            "gender": None,
            "gender_probability": None,
            "age": None,
            "age_sample_count": None,
            "nationalities": [],
        },
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
        # Scraper findings nest extracted fields under "extracted" key — flatten them
        if "extracted" in data and isinstance(data["extracted"], dict):
            for k, v in data["extracted"].items():
                if k not in data and v is not None:
                    data[k] = v
        source = data.get("source") or data.get("scraper") or f.module
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

        # --- Identity estimation (Genderize/Agify/Nationalize) ---
        if f.module == "scraper_engine":
            scraper_name = data.get("scraper", "")

            # Genderize
            if scraper_name == "genderize" and data.get("gender"):
                est = profile["identity_estimation"]
                if not est["gender"]:
                    est["gender"] = data["gender"]
                    try:
                        est["gender_probability"] = float(data.get("probability", 0))
                    except (TypeError, ValueError):
                        est["gender_probability"] = None

            # Agify
            if scraper_name == "agify" and data.get("age"):
                est = profile["identity_estimation"]
                if not est["age"]:
                    try:
                        est["age"] = int(data["age"])
                    except (TypeError, ValueError):
                        pass
                    try:
                        est["age_sample_count"] = int(data.get("sample_count", 0))
                    except (TypeError, ValueError):
                        pass

            # Nationalize
            if scraper_name == "nationalize" and data.get("top_country"):
                est = profile["identity_estimation"]
                if not est["nationalities"]:
                    nats = []
                    for prefix in ["top", "second", "third"]:
                        cc = data.get(f"{prefix}_country")
                        prob = data.get(f"{prefix}_probability")
                        if cc:
                            try:
                                nats.append({"country_code": cc, "probability": float(prob or 0)})
                            except (TypeError, ValueError):
                                nats.append({"country_code": cc, "probability": 0})
                    est["nationalities"] = nats

        # --- Website ---
        if data.get("blog") and not profile["website"]:
            profile["website"] = data["blog"]
        if data.get("website") and not profile["website"]:
            profile["website"] = data["website"]

        # --- Social profiles ---
        if f.category == "social_account":
            platform = (data.get("platform") or data.get("network") or data.get("service") or "").lower()
            url = f.url or data.get("url", "")
            username = data.get("username") or data.get("handle") or data.get("login") or ""

            # Normalize platform name
            platform_clean = platform.replace("_profile", "").replace("_scraper", "").replace("_search", "").strip()
            if not platform_clean and url:
                DOMAIN_PLATFORM = {
                    "twitter.com": "twitter", "x.com": "twitter", "instagram.com": "instagram",
                    "facebook.com": "facebook", "github.com": "github", "linkedin.com": "linkedin",
                    "pinterest.com": "pinterest", "reddit.com": "reddit", "youtube.com": "youtube",
                    "tiktok.com": "tiktok", "spotify.com": "spotify", "discord.com": "discord",
                    "steam": "steam", "keybase.io": "keybase", "medium.com": "medium",
                    "dev.to": "devto", "gitlab.com": "gitlab", "mastodon": "mastodon",
                    "stackoverflow.com": "stackoverflow", "imgur.com": "imgur",
                    "about.me": "aboutme", "linktree": "linktree", "disqus.com": "disqus",
                }
                for domain_key, pname in DOMAIN_PLATFORM.items():
                    if domain_key in url.lower():
                        platform_clean = pname
                        break

            key = platform_clean or url
            if key and key not in seen_socials:
                seen_socials.add(key)
                profile["social_profiles"].append({
                    "platform": platform_clean or platform,
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

        # --- Breaches (exclude "not configured" / "api key" info findings) ---
        if f.category == "breach":
            title_lower = (f.title or "").lower()
            if "not configured" not in title_lower and "api key" not in title_lower:
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

    # --- Profile confidence score ---
    name_sources = len(profile["names"])
    avatar_sources = len(profile["avatars"])
    total_sources = len(profile["data_sources"])

    name_confidence = min(1.0, name_sources * 0.25)
    avatar_confidence = min(1.0, avatar_sources * 0.33)
    data_confidence = min(1.0, total_sources / 10)

    name_values = [n["value"].lower().strip() for n in profile["names"]]
    most_common_count = max((name_values.count(v) for v in set(name_values)), default=0)
    cross_verified_bonus = min(0.2, most_common_count * 0.1)

    overall_confidence = min(1.0, (
        name_confidence * 0.30 +
        avatar_confidence * 0.15 +
        data_confidence * 0.40 +
        cross_verified_bonus +
        (0.15 if total_sources > 0 else 0.0)
    ))

    profile["confidence"] = {
        "overall": round(overall_confidence, 2),
        "name_sources": name_sources,
        "avatar_sources": avatar_sources,
        "total_sources": total_sources,
        "cross_verified": most_common_count > 1,
    }

    # --- Per-field confidence ---
    field_confidence = {}

    # First name confidence
    first_names = []
    for n in profile["names"]:
        parts = n["value"].strip().split()
        if parts:
            first_names.append({"value": parts[0], "source": n["source"]})

    if first_names:
        unique_first = set(fn["value"].lower() for fn in first_names)
        fn_sources = set(fn["source"] for fn in first_names)
        most_common = max(unique_first, key=lambda v: sum(1 for fn in first_names if fn["value"].lower() == v))
        match_count = sum(1 for fn in first_names if fn["value"].lower() == most_common)
        field_confidence["first_name"] = {
            "value": next(fn["value"] for fn in first_names if fn["value"].lower() == most_common),
            "confidence": round(min(1.0, match_count * 0.3 + len(fn_sources) * 0.1), 2),
            "sources": sorted(fn_sources),
            "source_count": len(fn_sources),
        }

    # Last name confidence
    last_names = []
    for n in profile["names"]:
        parts = n["value"].strip().split()
        if len(parts) >= 2:
            last_names.append({"value": parts[-1], "source": n["source"]})

    if last_names:
        unique_last = set(ln["value"].lower() for ln in last_names)
        ln_sources = set(ln["source"] for ln in last_names)
        most_common = max(unique_last, key=lambda v: sum(1 for ln in last_names if ln["value"].lower() == v))
        match_count = sum(1 for ln in last_names if ln["value"].lower() == most_common)
        field_confidence["last_name"] = {
            "value": next(ln["value"] for ln in last_names if ln["value"].lower() == most_common),
            "confidence": round(min(1.0, match_count * 0.3 + len(ln_sources) * 0.1), 2),
            "sources": sorted(ln_sources),
            "source_count": len(ln_sources),
        }

    # Gender confidence (from identity_estimation)
    est = profile.get("identity_estimation", {})
    if est.get("gender"):
        field_confidence["gender"] = {
            "value": est["gender"],
            "confidence": round(est.get("gender_probability", 0), 2),
            "sources": ["genderize.io"],
            "source_count": 1,
            "note": "Statistical estimation from first name",
        }

    # Age confidence
    if est.get("age"):
        sample = est.get("age_sample_count", 0) or 0
        field_confidence["age"] = {
            "value": f"~{est['age']}",
            "confidence": round(min(0.6, sample / 100000), 2),
            "sources": ["agify.io"],
            "source_count": 1,
            "note": f"Demographic estimate from {sample:,} samples",
        }

    # Location confidence
    if profile.get("location"):
        loc_sources = set()
        for f_item in findings:
            d = f_item.data or {}
            if "extracted" in d and isinstance(d["extracted"], dict):
                for k, v in d["extracted"].items():
                    if k not in d and v is not None:
                        d[k] = v
            for loc_key in ("location", "currentLocation"):
                if d.get(loc_key) == profile["location"]:
                    loc_sources.add(d.get("source") or d.get("scraper") or f_item.module)
        field_confidence["location"] = {
            "value": profile["location"],
            "confidence": round(min(1.0, len(loc_sources) * 0.35), 2),
            "sources": sorted(loc_sources),
            "source_count": len(loc_sources),
        }

    profile["field_confidence"] = field_confidence

    # Pick primary name with strict validation
    PLATFORM_NAMES = {
        # Social platforms
        "spotify", "amazon", "reddit", "steam", "keybase", "github", "twitter",
        "facebook", "instagram", "tiktok", "freelancer", "replit", "eventbrite",
        "xvideos", "medium", "hackernews", "devto", "gitlab", "pinterest",
        "snapchat", "linkedin", "tumblr", "flickr", "twitch", "discord",
        "telegram", "whatsapp", "signal", "youtube", "netflix", "hulu",
        "apple", "google", "microsoft", "yahoo", "outlook", "protonmail",
        "gravatar", "wordpress", "blogger", "bitbucket", "stackoverflow",
        # Password managers / security tools
        "lastpass", "1password", "bitwarden", "dashlane", "nordpass", "keepass",
        # Email services / providers
        "office365", "office", "tutanota", "zoho", "mailchimp", "sendgrid",
        "proton", "icloud", "hotmail", "live", "msn", "aol", "gmx",
        # Freelance / work platforms
        "fiverr", "upwork", "toptal", "guru", "peopleperhour",
        # New scraper platforms
        "imgur", "disqus", "mastodon", "linktree", "aboutme", "about.me",
        # Generic words that are never real names
        "unknown", "user", "admin", "test", "null", "none", "default",
        "anonymous", "noreply", "info", "support", "contact", "hello",
        "webmaster", "postmaster", "root", "system", "bot", "service",
    }
    REJECT_PATTERNS = {
        "account", "found", "not configured", "api key", "profile",
        "scraper", "scanner", "module", "error", "failed", "timeout",
        "not found", "no results", "unavailable", "blocked",
        "http://", "https://", ".com", ".org", ".net",
    }

    def _is_valid_name(name_val):
        """Validate: must be a real human name, not a platform or finding title."""
        if not name_val or len(name_val.strip()) < 3:
            return False
        val = name_val.strip().lower()
        # Reject platform names
        if val in PLATFORM_NAMES:
            return False
        # Reject finding-title patterns
        if any(p in val for p in REJECT_PATTERNS):
            return False
        # Reject single words that look like usernames (all lowercase, no spaces)
        # Real names usually have at least a first+last or a proper cased single name
        if " " not in val and val == val.lower() and len(val) < 20:
            # Check if it matches a known platform
            if val in PLATFORM_NAMES:
                return False
        return True

    NAME_PRIORITY = ["google_audit", "fullcontact", "github_deep", "social_enricher", "gravatar", "epieos", "emailrep", "scraper_engine"]
    primary_name = None
    for source_prio in NAME_PRIORITY:
        for n in profile["names"]:
            if n.get("source") == source_prio and _is_valid_name(n["value"]):
                primary_name = n["value"].strip()
                break
        if primary_name:
            break
    if not primary_name and profile["names"]:
        for n in profile["names"]:
            if _is_valid_name(n["value"]):
                primary_name = n["value"].strip()
                break
    profile["primary_name"] = primary_name

    # Pick primary avatar with priority:
    # 1. Google OAuth, 2. Gravatar (non-default), 3. GitHub, 4. FullContact, 5. Others
    AVATAR_PRIORITY = ["google_audit", "gravatar", "github_deep", "social_enricher", "fullcontact", "epieos", "scraper_engine"]
    primary_avatar = None
    for source_prio in AVATAR_PRIORITY:
        for a in profile["avatars"]:
            if a.get("source") == source_prio:
                primary_avatar = a["url"]
                break
        if primary_avatar:
            break
    if not primary_avatar and profile["avatars"]:
        primary_avatar = profile["avatars"][0]["url"]
    profile["primary_avatar"] = primary_avatar

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
