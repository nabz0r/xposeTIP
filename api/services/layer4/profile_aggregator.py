"""Profile Aggregator — merge findings into a unified person profile."""
import logging
import re
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.finding import Finding
from api.models.identity import Identity
from api.models.target import Target
from api.services.layer4.source_scoring import get_source_reliability as _get_src_rel_mod
from api.services.layer4.username_validator import is_valid_username

logger = logging.getLogger(__name__)

# Avatar URL blacklist — platform logos, default images, not real profile photos
AVATAR_BLACKLIST_PATTERNS = [
    "telesco.pe",
    "cdn1.telesco.pe",
    "cdn2.telesco.pe",
    "cdn3.telesco.pe",
    "cdn4.telesco.pe",
    "telegram.org",
    "t.me/i/",
    "static.xx.fbcdn",
    "default_profile",
    "gravatar.com/avatar/00000000",
    "/default.",
    "placeholder",
    "no-avatar",
    "no_avatar",
    "anonymous",
]

# Bio blacklist — platform slogans extracted as user bios
BIO_BLACKLIST = [
    "fast. secure. powerful.",
    "a new era of messaging",
    "join the conversation",
    "share and stay in touch",
    "connect with friends",
    "see what's happening",
    "instant messaging",
    "cloud-based mobile",
    "linktree",
    "discover and stream music",
    "your next favorite track",
    # Telegram platform descriptions
    "telegram is a cloud-based",
    "telegram messenger",
    "pure instant messaging",
    "simple, fast, secure",
    "synced across all your devices",
    "sending messages",
    "telegram lets you",
    "powerful, fast, and secure",
]


def _is_valid_avatar(url):
    """Check if avatar URL is a real profile photo, not a platform logo."""
    if not url:
        return False
    url_lower = url.lower()
    return not any(pattern in url_lower for pattern in AVATAR_BLACKLIST_PATTERNS)


def _is_valid_bio(bio):
    """Check if bio is user-written, not a platform slogan."""
    if not bio:
        return False
    bio_lower = bio.strip().lower()
    return not any(bl in bio_lower for bl in BIO_BLACKLIST)


def _load_blacklist(session):
    """Load name blacklist from DB. Returns list of dicts."""
    try:
        from api.models.name_blacklist import NameBlacklist
        entries = session.execute(select(NameBlacklist)).scalars().all()
        return [{"pattern": e.pattern, "type": e.type} for e in entries]
    except Exception:
        logger.debug("Could not load name blacklist from DB, using hardcoded fallback")
        return []


def _is_valid_name_db(name_val, blacklist):
    """Validate name against DB blacklist."""
    if not name_val or len(name_val.strip()) < 3:
        return False
    val = name_val.strip()
    val_lower = val.lower()

    # Reject single-letter initials like "J.", "A Smith", or "J Smith"
    parts = val.split()
    if parts and (len(parts[0]) == 1 or (len(parts[0]) == 2 and parts[0].endswith("."))):
        return False
    # Reject single-letter last name initials like "Steffen H.", "John D."
    if len(parts) >= 2 and len(parts[-1].rstrip(".")) <= 1:
        return False

    for entry in blacklist:
        pattern = entry["pattern"].lower()
        rule_type = entry["type"]

        if rule_type == "exact" and val_lower == pattern:
            return False
        elif rule_type == "contains" and pattern in val_lower:
            return False
        elif rule_type == "regex":
            try:
                if re.match(entry["pattern"], val, re.IGNORECASE):
                    return False
            except re.error:
                pass

    return True


# --- Static geocoding tables (zero API calls) ---
COUNTRY_COORDS = {
    "germany": {"lat": 51.1657, "lon": 10.4515, "country": "Germany"},
    "france": {"lat": 46.2276, "lon": 2.2137, "country": "France"},
    "luxembourg": {"lat": 49.8153, "lon": 6.1296, "country": "Luxembourg"},
    "united states": {"lat": 37.0902, "lon": -95.7129, "country": "United States"},
    "united kingdom": {"lat": 55.3781, "lon": -3.4360, "country": "United Kingdom"},
    "canada": {"lat": 56.1304, "lon": -106.3468, "country": "Canada"},
    "india": {"lat": 20.5937, "lon": 78.9629, "country": "India"},
    "russia": {"lat": 61.5240, "lon": 105.3188, "country": "Russia"},
    "philippines": {"lat": 12.8797, "lon": 121.7740, "country": "Philippines"},
    "japan": {"lat": 36.2048, "lon": 138.2529, "country": "Japan"},
    "australia": {"lat": -25.2744, "lon": 133.7751, "country": "Australia"},
    "brazil": {"lat": -14.2350, "lon": -51.9253, "country": "Brazil"},
    "netherlands": {"lat": 52.1326, "lon": 5.2913, "country": "Netherlands"},
    "belgium": {"lat": 50.5039, "lon": 4.4699, "country": "Belgium"},
    "switzerland": {"lat": 46.8182, "lon": 8.2275, "country": "Switzerland"},
    "spain": {"lat": 40.4637, "lon": -3.7492, "country": "Spain"},
    "italy": {"lat": 41.8719, "lon": 12.5674, "country": "Italy"},
    "portugal": {"lat": 39.3999, "lon": -8.2245, "country": "Portugal"},
    "poland": {"lat": 51.9194, "lon": 19.1451, "country": "Poland"},
    "sweden": {"lat": 60.1282, "lon": 18.6435, "country": "Sweden"},
    "norway": {"lat": 60.4720, "lon": 8.4689, "country": "Norway"},
    "denmark": {"lat": 56.2639, "lon": 9.5018, "country": "Denmark"},
    "finland": {"lat": 61.9241, "lon": 25.7482, "country": "Finland"},
    "ireland": {"lat": 53.1424, "lon": -7.6921, "country": "Ireland"},
    "austria": {"lat": 47.5162, "lon": 14.5501, "country": "Austria"},
    "china": {"lat": 35.8617, "lon": 104.1954, "country": "China"},
    "south korea": {"lat": 35.9078, "lon": 127.7669, "country": "South Korea"},
    "singapore": {"lat": 1.3521, "lon": 103.8198, "country": "Singapore"},
    "lithuania": {"lat": 55.1694, "lon": 23.8813, "country": "Lithuania"},
    "romania": {"lat": 45.9432, "lon": 24.9668, "country": "Romania"},
}

CITY_COORDS = {
    "san francisco": {"lat": 37.7749, "lon": -122.4194, "city": "San Francisco", "country": "United States"},
    "new york": {"lat": 40.7128, "lon": -74.0060, "city": "New York", "country": "United States"},
    "london": {"lat": 51.5074, "lon": -0.1278, "city": "London", "country": "United Kingdom"},
    "paris": {"lat": 48.8566, "lon": 2.3522, "city": "Paris", "country": "France"},
    "berlin": {"lat": 52.5200, "lon": 13.4050, "city": "Berlin", "country": "Germany"},
    "munich": {"lat": 48.1351, "lon": 11.5820, "city": "Munich", "country": "Germany"},
    "frankfurt": {"lat": 50.1109, "lon": 8.6821, "city": "Frankfurt", "country": "Germany"},
    "mountain view": {"lat": 37.3861, "lon": -122.0839, "city": "Mountain View", "country": "United States"},
    "luxembourg": {"lat": 49.6117, "lon": 6.1300, "city": "Luxembourg", "country": "Luxembourg"},
    "brighton": {"lat": 50.8225, "lon": -0.1372, "city": "Brighton", "country": "United Kingdom"},
    "moscow": {"lat": 55.7558, "lon": 37.6173, "city": "Moscow", "country": "Russia"},
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "city": "Mumbai", "country": "India"},
    "montreal": {"lat": 45.5017, "lon": -73.5673, "city": "Montreal", "country": "Canada"},
    "toronto": {"lat": 43.6532, "lon": -79.3832, "city": "Toronto", "country": "Canada"},
    "minneapolis": {"lat": 44.9778, "lon": -93.2650, "city": "Minneapolis", "country": "United States"},
    "los angeles": {"lat": 34.0522, "lon": -118.2437, "city": "Los Angeles", "country": "United States"},
    "cedar rapids": {"lat": 41.9779, "lon": -91.6656, "city": "Cedar Rapids", "country": "United States"},
    "amsterdam": {"lat": 52.3676, "lon": 4.9041, "city": "Amsterdam", "country": "Netherlands"},
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "city": "Tokyo", "country": "Japan"},
    "sydney": {"lat": -33.8688, "lon": 151.2093, "city": "Sydney", "country": "Australia"},
}

_COUNTRY_CODE_MAP = {
    "us": "united states", "gb": "united kingdom", "uk": "united kingdom",
    "de": "germany", "fr": "france", "lu": "luxembourg", "ca": "canada",
    "in": "india", "ru": "russia", "jp": "japan", "au": "australia",
    "nl": "netherlands", "be": "belgium", "ch": "switzerland",
    "es": "spain", "it": "italy", "lt": "lithuania", "ro": "romania",
    "ph": "philippines", "cn": "china", "kr": "south korea", "sg": "singapore",
    "br": "brazil", "pt": "portugal", "pl": "poland", "se": "sweden",
    "no": "norway", "dk": "denmark", "fi": "finland", "ie": "ireland",
    "at": "austria",
}


def _geocode_location(loc_string):
    """Static geocoding — no API calls. Returns dict with lat/lon or None."""
    loc = loc_string.lower().strip()

    # Try city match first (more specific)
    for city_key, coords in CITY_COORDS.items():
        if city_key in loc:
            return dict(coords)

    # Try country match
    for country_key, coords in COUNTRY_COORDS.items():
        if country_key in loc:
            return dict(coords)

    # Try 2-letter country code
    if len(loc) == 2:
        country = _COUNTRY_CODE_MAP.get(loc)
        if country and country in COUNTRY_COORDS:
            return dict(COUNTRY_COORDS[country])

    return None


# Platform names that holehe/scrapers return as "name" — never real human names
_PLATFORM_NAMES_SET = {
    "spotify", "amazon", "reddit", "steam", "keybase", "github", "twitter",
    "facebook", "instagram", "tiktok", "freelancer", "replit", "eventbrite",
    "xvideos", "medium", "hackernews", "devto", "gitlab", "pinterest",
    "snapchat", "linkedin", "tumblr", "flickr", "twitch", "discord",
    "telegram", "whatsapp", "signal", "youtube", "netflix", "hulu",
    "apple", "google", "microsoft", "yahoo", "outlook", "protonmail",
    "gravatar", "wordpress", "blogger", "bitbucket", "stackoverflow",
    "lastpass", "1password", "bitwarden", "dashlane", "nordpass", "keepass",
    "office365", "office", "tutanota", "zoho", "mailchimp", "sendgrid",
    "proton", "icloud", "hotmail", "live", "msn", "aol", "gmx",
    "fiverr", "upwork", "toptal", "guru", "peopleperhour",
    "imgur", "disqus", "mastodon", "linktree", "aboutme", "about.me",
    "unknown", "user", "admin", "test", "null", "none", "default",
    "anonymous", "noreply", "info", "support", "contact", "hello",
    "webmaster", "postmaster", "root", "system", "bot", "service",
    "booking", "firefox", "chrome", "safari", "opera", "edge",
}

_TELEGRAM_SLOGANS = [
    "a new era of messaging", "fast. secure. powerful",
    "pure instant messaging", "cloud-based", "simple, fast, secure",
    "synced across all your devices", "sending messages",
    "telegram lets you", "powerful, fast, and secure",
    "telegram messenger", "telegram is a cloud-based",
]


def _clean_name_value(raw_name):
    """Clean a name before storing. Returns cleaned name or None if garbage."""
    if not raw_name or not isinstance(raw_name, str):
        return None

    name = raw_name.strip()

    # Strip emojis
    name = re.sub(r'[\U0001F000-\U0001FFFF\u200D\uFE0F]', '', name).strip()

    # Remove "on about.me", "on Snapchat", etc.
    name = re.sub(r'\s+on\s+\w+\.?\w*$', '', name, flags=re.IGNORECASE).strip()

    # Reject @xxx | Linktree, @xxx | Platform
    if name.startswith('@') or '|' in name:
        return None

    # Reject anything starting with "Telegram"
    if name.lower().startswith('telegram'):
        return None

    # Reject Telegram slogans
    if any(s in name.lower() for s in _TELEGRAM_SLOGANS):
        return None

    # Reject Cyrillic/CJK-only strings (likely wrong profile match)
    if re.match(r'^[\u0400-\u04FF\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]+$', name):
        return None

    # Reject very short
    if len(name) < 3:
        return None

    # Reject code/technical artifacts
    if re.match(r'^[a-z_]+$', name) and len(name) < 15:
        return None  # lowercase-only single word = username, not a name

    # Reject platform names
    if name.strip().lower() in _PLATFORM_NAMES_SET:
        return None

    # Reject "Contact @xxx" patterns
    if re.match(r'^contact\s+@', name, re.IGNORECASE):
        return None

    # Reject "xxx's profile" patterns (e.g. "stheis's profile" from letterboxd)
    if re.search(r"'s\s+profile$", name, re.IGNORECASE):
        return None

    return name


def _find_finding_for_name(findings, name_value, source_name):
    """Find the finding that produced this name value."""
    for f in findings:
        data = f.data or {}
        # Check extracted dict
        extracted = data.get("extracted")
        if isinstance(extracted, dict):
            for k, v in extracted.items():
                if v == name_value:
                    return f
        # Check direct name fields
        for key in ("name", "full_name", "display_name", "displayName"):
            if data.get(key) == name_value:
                return f
    return None


def aggregate_profile(target_id, workspace_id, session: Session, graph_context=None) -> dict:
    """Build a unified profile from all findings for a target. Sync for Celery.

    If graph_context is provided, uses pre-computed node confidence map
    instead of querying identity nodes from DB.
    """
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
        is_email_verified = getattr(f, "indicator_type", "") == "email"
        for name_key in ("name", "full_name", "display_name", "displayName"):
            # Axe 4: holehe "name" field = platform name, not person name
            if f.module == "holehe" and name_key == "name":
                continue
            raw = data.get(name_key, "")
            name = _clean_name_value(raw)
            if name is None and raw and raw.strip():
                logger.debug("Name rejected by _clean_name_value: %r (source=%s)", raw.strip(), source)
            if name and name not in seen_names:
                seen_names.add(name)
                profile["names"].append({"value": name, "source": source, "module": f.module, "email_verified": is_email_verified})
            elif name and name in seen_names:
                # Dedup upgrade: if new source is more reliable, update the entry
                new_rel = _get_src_rel_mod(f.module, scraper_name=source)
                for existing in profile["names"]:
                    if existing["value"] == name:
                        old_rel = _get_src_rel_mod(
                            existing.get("module", "scraper_engine"),
                            scraper_name=existing.get("source", ""),
                        )
                        if new_rel > old_rel:
                            existing["source"] = source
                            existing["module"] = f.module
                            existing["email_verified"] = is_email_verified
                        break

        # --- Avatars ---
        for avatar_key in ("avatar_url", "photo_url", "avatar", "picture", "profile_image", "image_url"):
            avatar = data.get(avatar_key, "")
            if avatar and avatar not in seen_avatars and _is_valid_avatar(avatar):
                seen_avatars.add(avatar)
                profile["avatars"].append({"url": avatar, "source": source})
        # Also check nested structures (profile_data, extracted, details)
        for nested_key in ("profile_data", "extracted", "details"):
            nested = data.get(nested_key)
            if isinstance(nested, dict):
                for avatar_key in ("avatar_url", "photo_url", "avatar", "picture", "profile_image", "image_url"):
                    avatar = nested.get(avatar_key, "")
                    if avatar and avatar not in seen_avatars and _is_valid_avatar(avatar):
                        seen_avatars.add(avatar)
                        profile["avatars"].append({"url": avatar, "source": source})

        # --- Bio ---
        for bio_key in ("bio", "about", "description"):
            bio = data.get(bio_key, "")
            if bio and not profile["bio"] and _is_valid_bio(bio):
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
            if uname and uname not in seen_usernames and len(uname) >= 3 and is_valid_username(uname):
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

    # --- Harvest self-reported user locations from scraper findings ---
    user_locations = []
    seen_user_locs = set()

    for f in findings:
        source = f.module or ""
        data_raw = f.data or {}

        # Skip geoip — it's server location, not user location
        if source in ("geoip", "maxmind_geo"):
            continue

        # Check all possible location fields
        loc = None
        for key in ("location", "city", "country"):
            val = data_raw.get(key)
            if val and isinstance(val, str) and len(val.strip()) >= 2:
                loc = val.strip()
                break

        # Also check extracted dict
        if not loc:
            extracted = data_raw.get("extracted")
            if isinstance(extracted, dict):
                for key in ("location", "city", "country"):
                    val = extracted.get(key)
                    if val and isinstance(val, str) and len(val.strip()) >= 2:
                        loc = val.strip()
                        break

        if not loc:
            continue

        # Reject URLs, XML, very short codes
        if loc.startswith("http") or loc.startswith("<") or loc.startswith("]"):
            continue
        if "CDATA" in loc or "xml" in loc.lower():
            continue
        if len(loc) < 3 and loc.upper() not in _COUNTRY_CODE_MAP:
            continue

        loc_key = loc.lower().strip()
        if loc_key in seen_user_locs:
            continue
        seen_user_locs.add(loc_key)

        entry = {
            "location": loc,
            "source": source,
            "type": "self_reported",
            "confidence": _get_src_rel_mod(source),
        }
        # Static geocode
        coords = _geocode_location(loc)
        if coords:
            entry.update(coords)
        user_locations.append(entry)

    profile["user_locations"] = user_locations

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

    # Load identity nodes with propagated confidence (from PageRank)
    # Use graph_context if available, else load from DB (existing behavior)
    if graph_context:
        node_confidence_map = {
            v["value"].lower(): v["confidence"]
            for v in graph_context["node_map"].values()
            if v.get("value")
        }
    else:
        identities = session.execute(
            select(Identity).where(
                Identity.target_id == target_id,
                Identity.workspace_id == workspace_id,
            )
        ).scalars().all()
        node_confidence_map = {}
        for i in identities:
            if i.value:
                node_confidence_map[i.value.lower()] = i.confidence or 0.5

    # Load DB blacklist early (needed for field_confidence + name validation)
    db_blacklist = _load_blacklist(session)

    # --- Parse potential name from email prefix ---
    _email = session.execute(
        select(Target.email).where(Target.id == target_id, Target.workspace_id == workspace_id)
    ).scalar_one_or_none() or ""
    _prefix = _email.split("@")[0] if "@" in _email else _email
    _cleaned = re.sub(r"\d+", "", _prefix)
    _name_parts = [p for p in re.split(r"[._\-]", _cleaned) if len(p) >= 2]
    email_name_guess = {
        "first": _name_parts[0].capitalize() if len(_name_parts) >= 1 else None,
        "last": _name_parts[-1].capitalize() if len(_name_parts) >= 2 else None,
        "full": " ".join(p.capitalize() for p in _name_parts) if len(_name_parts) >= 2 else None,
    }

    # --- Per-field confidence ---
    field_confidence = {}

    # First name confidence — filter candidates through blacklist
    first_names = []
    for n in profile["names"]:
        parts = n["value"].strip().split()
        if parts:
            candidate = parts[0]
            if len(candidate) >= 2 and _is_valid_name_db(candidate, db_blacklist):
                first_names.append({"value": candidate, "source": n["source"]})

    if first_names:
        # Use propagated confidence from graph if available
        for fn in first_names:
            fn["graph_confidence"] = node_confidence_map.get(fn["value"].lower(), 0.3)

        # Boost names that appear in the top graph cluster
        if graph_context and graph_context.get("clusters"):
            top_cluster = graph_context["clusters"][0]
            top_cluster_nodes = set(top_cluster["nodes"])
            for fn in first_names:
                node_info = graph_context["node_map"].get(fn["value"].lower())
                if node_info and node_info["id"] in top_cluster_nodes:
                    fn["graph_confidence"] = fn.get("graph_confidence", 0) + 0.15

        # Best first name = highest graph confidence
        best = max(first_names, key=lambda fn: fn.get("graph_confidence", 0))
        fn_sources = set(fn["source"] for fn in first_names if fn["value"].lower() == best["value"].lower())
        match_count = sum(1 for fn in first_names if fn["value"].lower() == best["value"].lower())
        field_confidence["first_name"] = {
            "value": best["value"],
            "confidence": round(min(1.0, best["graph_confidence"] * 0.6 + len(fn_sources) * 0.15), 2),
            "sources": sorted(fn_sources),
            "source_count": len(fn_sources),
            "graph_confidence": round(best["graph_confidence"], 2),
        }
        # Boost if matches email pattern
        if email_name_guess["first"] and field_confidence["first_name"]["value"].lower() == email_name_guess["first"].lower():
            field_confidence["first_name"]["confidence"] = round(min(1.0, field_confidence["first_name"]["confidence"] + 0.20), 2)
            field_confidence["first_name"]["sources"].append("email_pattern_match")

    # Last name confidence — filter candidates through blacklist
    last_names = []
    for n in profile["names"]:
        parts = n["value"].strip().split()
        if len(parts) >= 2:
            candidate = parts[-1]
            if len(candidate) >= 2 and _is_valid_name_db(candidate, db_blacklist):
                last_names.append({"value": candidate, "source": n["source"]})

    if last_names:
        # Use propagated confidence from graph if available
        for ln in last_names:
            ln["graph_confidence"] = node_confidence_map.get(ln["value"].lower(), 0.3)

        # Boost names in top graph cluster
        if graph_context and graph_context.get("clusters"):
            top_cluster = graph_context["clusters"][0]
            top_cluster_nodes = set(top_cluster["nodes"])
            for ln in last_names:
                node_info = graph_context["node_map"].get(ln["value"].lower())
                if node_info and node_info["id"] in top_cluster_nodes:
                    ln["graph_confidence"] = ln.get("graph_confidence", 0) + 0.15

        best = max(last_names, key=lambda ln: ln.get("graph_confidence", 0))
        ln_sources = set(ln["source"] for ln in last_names if ln["value"].lower() == best["value"].lower())
        match_count = sum(1 for ln in last_names if ln["value"].lower() == best["value"].lower())
        field_confidence["last_name"] = {
            "value": best["value"],
            "confidence": round(min(1.0, best["graph_confidence"] * 0.6 + len(ln_sources) * 0.15), 2),
            "sources": sorted(ln_sources),
            "source_count": len(ln_sources),
            "graph_confidence": round(best["graph_confidence"], 2),
        }
        # Boost if matches email pattern
        if email_name_guess["last"] and field_confidence["last_name"]["value"].lower() == email_name_guess["last"].lower():
            field_confidence["last_name"]["confidence"] = round(min(1.0, field_confidence["last_name"]["confidence"] + 0.20), 2)
            field_confidence["last_name"]["sources"].append("email_pattern_match")

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
        # Telegram garbage
        "telegram", "a new era", "fast. secure", "instant messaging",
        "cloud-based", "synced across",
        # Platform descriptions
        "on about.me", "| linktree", "contact @",
        # Browsers / tools
        "firefox", "chrome", "safari", "opera", "edge",
        "booking",
    }

    def _is_valid_name(name_val):
        """Validate: must be a real human name, not a platform or finding title."""
        if not name_val or len(name_val.strip()) < 3:
            return False
        # Check DB blacklist first (if loaded)
        if db_blacklist and not _is_valid_name_db(name_val, db_blacklist):
            return False
        # Hardcoded fallback
        val = name_val.strip().lower()
        if val in PLATFORM_NAMES:
            return False
        if any(p in val for p in REJECT_PATTERNS):
            return False
        return True

    # Composite score name resolution: graph_confidence * 0.5 + source_reliability * 0.3 + count * 0.1
    _get_src_rel = _get_src_rel_mod

    # Count how many sources confirm each name
    name_counts = {}
    for n in profile["names"]:
        key = n["value"].strip().lower()
        name_counts[key] = name_counts.get(key, 0) + 1

    # Score each name candidate
    for n in profile["names"]:
        graph_conf = node_confidence_map.get(n["value"].strip().lower(), 0.3)
        name_module = n.get("module", n.get("source", ""))
        scraper_name = n.get("source", "")
        source_rel = _get_src_rel(name_module, scraper_name=scraper_name)
        count_bonus = name_counts.get(n["value"].strip().lower(), 1) * 0.1

        # Axe 3: source method penalty — username-guessed vs email-verified
        method_adj = 0.0
        src_finding = _find_finding_for_name(findings, n["value"], scraper_name)
        if src_finding:
            ind_type = getattr(src_finding, "indicator_type", None) or ""
            # Username-guessed: indicator_type is username or social_url
            if ind_type in ("username", "social_url"):
                method_adj = -0.15
            # Email-verified: indicator_type is email
            elif ind_type == "email":
                method_adj = 0.05

        n["composite_score"] = graph_conf * 0.5 + source_rel * 0.3 + count_bonus + method_adj

    # Filter through blacklist + validation, pick highest composite score
    valid_names = [n for n in profile["names"] if _is_valid_name(n["value"])]

    # Axe 2: Family name consensus — boost names whose surname matches dominant family name
    if len(valid_names) >= 3:
        surname_votes = {}
        for n in valid_names:
            parts = n["value"].strip().split()
            if len(parts) >= 2:
                surname = parts[-1].lower()
                if len(surname) >= 2:
                    surname_votes[surname] = surname_votes.get(surname, 0) + 1
        if surname_votes:
            dominant_surname = max(surname_votes, key=surname_votes.get)
            dominant_count = surname_votes[dominant_surname]
            if dominant_count >= 2:
                for n in valid_names:
                    parts = n["value"].strip().split()
                    if len(parts) >= 2 and parts[-1].lower() == dominant_surname:
                        n["composite_score"] = n.get("composite_score", 0) + 0.10

    # Email prefix first-letter bonus: "stheis@" → S matches "Sebastian" (+0.08)
    _email_prefix_lc = _prefix.lower() if _prefix else ""
    _email_first_char = _email_prefix_lc[0] if _email_prefix_lc else ""
    if _email_first_char:
        for n in valid_names:
            name_first = n["value"].strip()[0].lower() if n["value"].strip() else ""
            if name_first == _email_first_char:
                n["composite_score"] = n.get("composite_score", 0) + 0.08

    # === Email Pattern Intelligence ===
    # Detect corporate email patterns from sibling targets on the same domain
    from api.services.layer4.email_pattern_detector import (
        detect_domain_pattern, decompose_email, boost_names_with_pattern,
        detect_pattern_with_assertion,
    )

    _email_domain = _email.split("@")[-1].lower() if "@" in _email else ""
    _email_pattern_info = None
    _email_decomp = None

    if _email_domain:
        _email_pattern_info = detect_domain_pattern(_email_domain, session)
        if _email_pattern_info:
            _email_decomp = decompose_email(_email, _email_pattern_info)
            if _email_decomp:
                logger.info(
                    "EMAIL_PATTERN: %s → surname='%s' first='%s' (pattern=%s, conf=%.2f)",
                    _email, _email_decomp.get("surname", "?"),
                    _email_decomp.get("first_initial", _email_decomp.get("first_name", "?")),
                    _email_decomp.get("pattern", "?"),
                    _email_decomp.get("confidence", 0),
                )
                valid_names = boost_names_with_pattern(valid_names, _email_decomp)

    # Operator-confirmed pattern: if operator has asserted a name, confirm the pattern
    _target_for_pattern = session.execute(
        select(Target).where(Target.id == target_id, Target.workspace_id == workspace_id)
    ).scalar_one_or_none()
    if _target_for_pattern:
        _op_pattern = detect_pattern_with_assertion(
            _email,
            getattr(_target_for_pattern, 'user_first_name', None),
            getattr(_target_for_pattern, 'user_last_name', None),
        )
        if _op_pattern:
            profile["email_pattern_confirmed"] = _op_pattern

    # Store pattern info in profile for frontend display
    if _email_pattern_info:
        profile["email_pattern"] = _email_pattern_info
    if _email_decomp:
        profile["email_decomposition"] = _email_decomp
        if not any(n.get("email_pattern_match") for n in valid_names):
            # No name matched — store surname hint
            profile["email_derived_surname"] = _email_decomp.get("surname", "").title()
            profile["email_derived_first_initial"] = _email_decomp.get("first_initial", "").upper()

    # Tier separation: email-verified names vs username-guessed names
    verified_names = [n for n in valid_names if n.get("email_verified")]
    guessed_names = [n for n in valid_names if not n.get("email_verified")]

    primary_name = None
    if verified_names:
        # Prefer email-verified names — these are confirmed for this email
        best = max(verified_names, key=lambda n: n.get("composite_score", 0))
        primary_name = best["value"].strip()
    elif guessed_names:
        # Fallback: consensus by family name among username-guessed names
        family_groups = {}
        for n in guessed_names:
            parts = n["value"].strip().split()
            if len(parts) >= 2:
                family = parts[-1].lower()
                family_groups.setdefault(family, []).append(n)

        if family_groups:
            best_family = max(family_groups, key=lambda fam: len(family_groups[fam]))
            candidates = family_groups[best_family]
            best = max(candidates, key=lambda n: n.get("composite_score", 0))
            primary_name = best["value"].strip()
        else:
            best = max(guessed_names, key=lambda n: n.get("composite_score", 0))
            primary_name = best["value"].strip()
    # Fallback: use email guess if no name found from scanners
    if not primary_name and email_name_guess["full"]:
        if _is_valid_name(email_name_guess["full"]):
            primary_name = email_name_guess["full"]
            profile["names"].append({"value": email_name_guess["full"], "source": "email_pattern"})
            profile["confidence"]["overall"] = max(profile.get("confidence", {}).get("overall", 0), 0.25)
    profile["primary_name"] = primary_name

    # Save auto-resolved name BEFORE potential operator override
    profile["_auto_resolved_name"] = primary_name

    # === OPERATOR ASSERTION CHECK ===
    # If operator has asserted a name, it becomes primary with confidence=1.0
    target = session.execute(
        select(Target).where(Target.id == target_id, Target.workspace_id == workspace_id)
    ).scalar_one_or_none()
    if target:
        user_first = getattr(target, 'user_first_name', None)
        user_last = getattr(target, 'user_last_name', None)
        if user_first or user_last:
            asserted_name = ' '.join(p for p in [user_first, user_last] if p)
            profile["primary_name"] = asserted_name
            profile["primary_name_source"] = "operator"
            profile["primary_name_confidence"] = 1.0

            # Demote auto-resolved name to alias if different
            auto_name = profile.get("_auto_resolved_name")
            if auto_name and auto_name.lower() != asserted_name.lower():
                aliases = profile.get("name_aliases", [])
                if auto_name not in aliases:
                    aliases.append(auto_name)
                profile["name_aliases"] = aliases

            logger.info("Using operator-asserted name: '%s' (auto-resolved was: '%s')",
                        asserted_name, profile.get("_auto_resolved_name"))
        else:
            profile["primary_name_source"] = "auto"

    # Pick primary avatar with priority:
    # 1. Google OAuth, 2. Gravatar (non-default), 3. GitHub, 4. FullContact, 5. Others
    AVATAR_PRIORITY = ["google_audit", "gravatar", "github_deep", "social_enricher", "fullcontact", "epieos", "scraper_engine"]
    primary_avatar = None
    for source_prio in AVATAR_PRIORITY:
        for a in profile["avatars"]:
            if a.get("source") == source_prio and _is_valid_avatar(a.get("url")):
                primary_avatar = a["url"]
                break
        if primary_avatar:
            break
    if not primary_avatar and profile["avatars"]:
        for a in profile["avatars"]:
            if _is_valid_avatar(a.get("url")):
                primary_avatar = a["url"]
                break
    profile["primary_avatar"] = primary_avatar

    # Store on target
    target = session.execute(
        select(Target).where(Target.id == target_id, Target.workspace_id == workspace_id)
    ).scalar_one_or_none()
    if target:
        target.profile_data = profile
        # Operator-asserted name always wins for display_name
        has_operator_name = (getattr(target, 'user_first_name', None) or
                             getattr(target, 'user_last_name', None))
        if has_operator_name:
            # Rebuild from user fields — pipeline NEVER overwrites operator assertion
            target.display_name = ' '.join(
                p for p in [target.user_first_name, target.user_last_name] if p
            )
        elif profile.get("primary_name_source") == "operator":
            target.display_name = profile["primary_name"]
        elif profile["primary_name"]:
            # Always update display_name from auto-resolved name on rescan
            # (previous value may be stale from an earlier, less accurate scan)
            target.display_name = profile["primary_name"]
        if profile["primary_avatar"] and not target.avatar_url:
            target.avatar_url = profile["primary_avatar"]
        session.commit()

    logger.info("Profile aggregated for target %s: %d sources, %d social profiles, %d breaches",
                target_id, len(sources), len(profile["social_profiles"]), profile["breach_summary"]["count"])
    return profile
