"""Pass 2 — Public Exposure Enricher.

After Pass 1 resolves a primary_name, this service runs name-based scrapers
in a specific order: GDELT (deep archive) -> GNews (recent, curated) ->
Google News RSS (free fallback, freshest).

Cross-scraper deduplication ensures no duplicate findings are stored.
Max 15 media_mention findings per target across all 3 scrapers.
"""
import logging
import re
import time
from datetime import date, datetime
from urllib.parse import urlparse, urlunparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.finding import Finding
from api.models.target import Target

logger = logging.getLogger(__name__)

# Common first names for name validation
COMMON_FIRST_NAMES = {
    "james", "john", "robert", "michael", "david", "william", "richard",
    "joseph", "thomas", "charles", "christopher", "daniel", "matthew",
    "anthony", "mark", "donald", "steven", "paul", "andrew", "joshua",
    "mary", "patricia", "jennifer", "linda", "barbara", "elizabeth",
    "susan", "jessica", "sarah", "karen", "lisa", "nancy", "betty",
    "margaret", "sandra", "ashley", "dorothy", "kimberly", "emily",
    "donna", "michelle", "carol", "amanda", "melissa", "deborah",
    # French
    "jean", "pierre", "nicolas", "benjamin", "mickael", "laurent",
    "philippe", "stephane", "christophe", "nathalie", "sophie", "marie",
    "isabelle", "catherine", "valerie", "sylvie", "sandrine", "caroline",
    "kamel", "nabil", "youssef", "rachid", "fatima",
    # German
    "hans", "klaus", "peter", "stefan", "andreas", "thomas", "markus",
    "martin", "steffen", "matthias", "sabine", "petra", "monika",
    # Spanish
    "carlos", "miguel", "jose", "antonio", "francisco", "pedro",
    "pablo", "luis", "jorge", "maria", "carmen", "rosa",
}

# Email TLD -> language mapping for language-aware search
TLD_LANG_MAP = {
    ".lu": "fr", ".fr": "fr", ".be": "fr", ".mc": "fr",
    ".de": "de", ".at": "de", ".ch": "de",
    ".es": "es", ".mx": "es", ".ar": "es", ".co": "es",
    ".it": "it", ".pt": "pt", ".br": "pt", ".nl": "nl",
}

# Country -> language mapping
COUNTRY_LANG_MAP = {
    "LU": "fr", "FR": "fr", "BE": "fr", "MC": "fr",
    "DE": "de", "AT": "de", "CH": "de",
    "ES": "es", "MX": "es", "AR": "es", "CO": "es",
    "IT": "it", "PT": "pt", "BR": "pt", "NL": "nl",
}

# Scraper priority for dedup (higher = better metadata, keep this one)
SCRAPER_PRIORITY = {
    "gnews_news": 3,
    "gdelt_news": 2,
    "google_news_rss": 1,
}

MAX_FINDINGS_PER_TARGET = 15
GNEWS_DAILY_QUOTA = 80  # Leave 20 req buffer from 100/day limit


def _is_real_name(name: str) -> bool:
    """Check if a name looks like a real human name (not a username)."""
    if not name or len(name.strip()) < 4:
        return False
    name = name.strip()
    if " " not in name:
        return False
    if "_" in name:
        return False
    parts = name.split()
    if len(parts) < 2:
        return False
    if any(len(p) < 2 for p in parts):
        return False
    first = parts[0]
    if not first[0].isupper() and first.lower() not in COMMON_FIRST_NAMES:
        return False
    return True


def compute_name_match_confidence(article_text: str, target_name: str) -> float:
    """Compute how likely an article mention matches our target."""
    if not article_text or not target_name:
        return 0.0

    text_lower = article_text.lower()
    name_lower = target_name.lower()
    parts = target_name.split()

    if name_lower in text_lower:
        return 0.95
    all_parts_found = all(p.lower() in text_lower for p in parts)
    if all_parts_found:
        return 0.80
    if len(parts) >= 2:
        last = parts[-1].lower()
        first_initial = parts[0][0].lower()
        if last in text_lower and f"{first_initial}." in text_lower:
            return 0.65
    if len(parts) >= 2 and parts[-1].lower() in text_lower:
        return 0.40
    return 0.0


# ---------------------------------------------------------------------------
# URL / Headline Normalization for Dedup
# ---------------------------------------------------------------------------

def normalize_url(url: str) -> str:
    """Normalize URL for comparison: strip params, fragment, www, trailing slash."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().lstrip("www.")
        path = parsed.path.rstrip("/")
        scheme = "https"
        return urlunparse((scheme, domain, path, "", "", ""))
    except Exception:
        return url.lower().strip().rstrip("/")


def normalize_headline(title: str) -> str:
    """Normalize headline for fuzzy matching."""
    if not title:
        return ""
    title = title.lower().strip()
    # Remove " - Source Name" suffix (Google News RSS format)
    if " - " in title:
        title = title.rsplit(" - ", 1)[0].strip()
    # Remove non-alphanumeric except spaces
    title = re.sub(r'[^a-z0-9\s]', '', title)
    # Collapse multiple spaces
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def deduplicate_media_findings(new_findings: list, existing_findings: list) -> list:
    """Remove duplicates across news scrapers.

    Match criteria (any ONE is enough):
    1. Exact URL match (after normalization)
    2. Same headline (normalized) + same source domain
    3. Same headline (normalized) + published within 24h
    """
    if not new_findings:
        return []

    # Build lookup sets from existing findings
    existing_urls = set()
    existing_headlines = {}  # headline_norm -> list of (source_domain, pub_date, scraper_priority)
    for f in existing_findings:
        url_norm = normalize_url(f.get("url", ""))
        if url_norm:
            existing_urls.add(url_norm)

        headline_norm = normalize_headline(f.get("title", ""))
        if headline_norm:
            src = (f.get("data", {}) or {}).get("source_domain", "")
            pub = (f.get("data", {}) or {}).get("pub_date", "")
            scraper = (f.get("data", {}) or {}).get("scraper", "")
            existing_headlines.setdefault(headline_norm, []).append({
                "source": src,
                "pub_date": pub,
                "priority": SCRAPER_PRIORITY.get(scraper, 0),
            })

    unique = []
    for f in new_findings:
        # Check 1: URL match
        url_norm = normalize_url(f.get("url", ""))
        if url_norm and url_norm in existing_urls:
            continue

        # Check 2+3: Headline match
        headline_norm = normalize_headline(f.get("title", ""))
        if headline_norm and headline_norm in existing_headlines:
            is_dup = False
            fdata = f.get("data", {}) or {}
            f_source = fdata.get("source_domain", "")
            f_pub = fdata.get("pub_date", "")

            for existing in existing_headlines[headline_norm]:
                # Same headline + same source domain
                if f_source and existing["source"] and f_source == existing["source"]:
                    is_dup = True
                    break
                # Same headline + within 24h
                if f_pub and existing["pub_date"]:
                    try:
                        t1 = datetime.fromisoformat(f_pub.replace("Z", "+00:00"))
                        t2 = datetime.fromisoformat(existing["pub_date"].replace("Z", "+00:00"))
                        if abs((t1 - t2).total_seconds()) < 86400:
                            is_dup = True
                            break
                    except (ValueError, TypeError):
                        pass

            if is_dup:
                continue

        # Not a duplicate — add it
        unique.append(f)
        # Update lookup sets for subsequent dedup within same batch
        if url_norm:
            existing_urls.add(url_norm)
        if headline_norm:
            fdata = f.get("data", {}) or {}
            existing_headlines.setdefault(headline_norm, []).append({
                "source": fdata.get("source_domain", ""),
                "pub_date": fdata.get("pub_date", ""),
                "priority": SCRAPER_PRIORITY.get(fdata.get("scraper", ""), 0),
            })

    return unique


def select_top_findings(findings: list, max_count: int = MAX_FINDINGS_PER_TARGET) -> list:
    """If more than max_count findings, keep the best ones.

    Sort by: match_confidence DESC, then reliability DESC, then date DESC.
    """
    if len(findings) <= max_count:
        return findings

    def sort_key(f):
        conf = f.get("confidence", 0)
        data = f.get("data", {}) or {}
        scraper = data.get("scraper", "")
        priority = SCRAPER_PRIORITY.get(scraper, 0)
        pub_date = data.get("pub_date", "") or ""
        return (-conf, -priority, pub_date)  # Negative for DESC

    findings.sort(key=sort_key)
    return findings[:max_count]


# ---------------------------------------------------------------------------
# Language-Aware Search
# ---------------------------------------------------------------------------

def get_search_languages(target) -> list[str]:
    """Determine search languages based on target context. Max 2."""
    langs = ["en"]

    # Check target email domain TLD
    email = getattr(target, "value", "") or ""
    if "@" in email:
        domain = email.split("@")[1].lower()
        for tld, lang in TLD_LANG_MAP.items():
            if domain.endswith(tld):
                if lang not in langs:
                    langs.append(lang)
                break

    # Check target country from profile
    if len(langs) < 2:
        profile = getattr(target, "profile_data", None) or {}
        locations = profile.get("user_locations", []) or profile.get("geo_locations", [])
        if locations and isinstance(locations, list):
            for loc in locations:
                country = ""
                if isinstance(loc, dict):
                    country = loc.get("country_code", "") or loc.get("country", "")
                elif isinstance(loc, str):
                    country = loc
                country = country.upper().strip()
                if country in COUNTRY_LANG_MAP:
                    lang = COUNTRY_LANG_MAP[country]
                    if lang not in langs:
                        langs.append(lang)
                        break

    return langs[:2]


# ---------------------------------------------------------------------------
# GNews Quota Management
# ---------------------------------------------------------------------------

def _get_gnews_daily_usage() -> int:
    """Get current GNews daily usage from Redis."""
    try:
        from api.services.cache import CacheService
        cache = CacheService()
        if cache.redis:
            key = f"gnews:daily_count:{date.today().isoformat()}"
            val = cache.redis.get(key)
            return int(val) if val else 0
    except Exception:
        pass
    return 0


def _increment_gnews_usage(count: int = 1):
    """Increment GNews daily usage counter in Redis."""
    try:
        from api.services.cache import CacheService
        cache = CacheService()
        if cache.redis:
            key = f"gnews:daily_count:{date.today().isoformat()}"
            pipe = cache.redis.pipeline()
            pipe.incrby(key, count)
            pipe.expire(key, 86400)
            pipe.execute()
    except Exception:
        pass


def _get_gnews_api_key(session: Session, workspace_id) -> str | None:
    """Retrieve GNews API key from workspace settings."""
    try:
        from api.models.workspace import Workspace
        ws = session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        ).scalar_one_or_none()
        if not ws:
            return None

        settings = ws.settings or {}
        # Check custom_api_keys first, then api_keys
        for store in ("custom_api_keys", "api_keys"):
            entry = settings.get(store, {}).get("gnews_api_key")
            if entry and isinstance(entry, dict) and entry.get("encrypted"):
                try:
                    from api.routers.settings import _get_fernet
                    return _get_fernet().decrypt(entry["encrypted"].encode()).decode()
                except Exception:
                    logger.warning("PASS2: Failed to decrypt GNews API key")
                    return None
            elif entry and isinstance(entry, str):
                return entry
    except Exception:
        logger.debug("PASS2: Could not retrieve GNews API key")
    return None


def should_run_gnews(gdelt_results_count: int) -> bool:
    """Only run GNews if target appears newsworthy and quota available."""
    if gdelt_results_count == 0:
        return False
    if _get_gnews_daily_usage() >= GNEWS_DAILY_QUOTA:
        logger.info("PASS2: GNews daily quota exhausted (%d/%d)", _get_gnews_daily_usage(), GNEWS_DAILY_QUOTA)
        return False
    return True


# ---------------------------------------------------------------------------
# Main Enrichment Pipeline
# ---------------------------------------------------------------------------

def enrich_public_exposure(target_id, session: Session) -> dict:
    """Pass 2 enrichment: run news scrapers in order with cross-dedup.

    Order: GDELT (deep) -> GNews (recent, if newsworthy) -> Google News RSS (fallback)
    Max 15 findings stored per target.
    """
    result = {"scrapers_run": 0, "findings_created": 0, "skipped_reason": None}

    target = session.execute(
        select(Target).where(Target.id == target_id)
    ).scalar_one_or_none()

    if not target:
        result["skipped_reason"] = "target_not_found"
        return result

    profile = target.profile_data or {}
    primary_name = profile.get("primary_name")

    if not primary_name:
        result["skipped_reason"] = "no_primary_name"
        logger.debug("PASS2: Skipping %s — no primary_name", target_id)
        return result

    if not _is_real_name(primary_name):
        result["skipped_reason"] = "username_like_name"
        logger.debug("PASS2: Skipping %s — name '%s' looks like username", target_id, primary_name)
        return result

    logger.info("PASS2: Running public exposure enrichment for '%s' (target %s)", primary_name, target_id)

    # Determine search languages
    search_langs = get_search_languages(target)
    logger.info("PASS2: Search languages for '%s': %s", primary_name, search_langs)

    # Extract email domain for context
    email = getattr(target, "value", "") or ""
    email_domain = email.split("@")[1] if "@" in email else None

    all_findings = []

    # --- 1. GDELT (free, deep archive, broad net) ---
    try:
        from api.scrapers.gdelt_news import search_gdelt_news

        for lang in search_langs:
            gdelt_results = search_gdelt_news(primary_name, domain=email_domain)
            if gdelt_results:
                for r in gdelt_results:
                    r.setdefault("data", {})["scraper"] = "gdelt_news"
                    r["confidence"] = compute_name_match_confidence(
                        r.get("description", "") or r.get("title", ""),
                        primary_name,
                    )
                # Filter by confidence
                gdelt_results = [r for r in gdelt_results if r.get("confidence", 0) >= 0.60]
                all_findings.extend(gdelt_results)
                logger.info("PASS2: GDELT found %d articles (lang=%s)", len(gdelt_results), lang)
            # GDELT doesn't have lang param — only run once
            break

        result["scrapers_run"] += 1
        time.sleep(1.0)
    except Exception:
        logger.exception("PASS2: GDELT scraper failed")

    # --- 2. GNews (if newsworthy + quota available + API key exists) ---
    gnews_api_key = _get_gnews_api_key(session, target.workspace_id)
    if gnews_api_key and should_run_gnews(len(all_findings)):
        try:
            from api.scrapers.gnews_news import search_gnews

            gnews_all = []
            for lang in search_langs:
                gnews_results = search_gnews(primary_name, api_key=gnews_api_key, lang=lang)
                _increment_gnews_usage(1)

                if gnews_results:
                    for r in gnews_results:
                        r.setdefault("data", {})["scraper"] = "gnews_news"
                        r["confidence"] = compute_name_match_confidence(
                            r.get("description", "") or r.get("title", ""),
                            primary_name,
                        )
                    gnews_results = [r for r in gnews_results if r.get("confidence", 0) >= 0.60]
                    gnews_all.extend(gnews_results)
                    logger.info("PASS2: GNews found %d articles (lang=%s)", len(gnews_results), lang)

                time.sleep(1.5)

            # Dedup against GDELT
            gnews_unique = deduplicate_media_findings(gnews_all, all_findings)
            all_findings.extend(gnews_unique)
            result["scrapers_run"] += 1
        except Exception:
            logger.exception("PASS2: GNews scraper failed")
    elif not gnews_api_key:
        logger.debug("PASS2: GNews skipped — no API key configured")
    else:
        logger.debug("PASS2: GNews skipped — not newsworthy or quota exhausted")

    # --- 3. Google News RSS (free fallback, freshest) ---
    try:
        from api.scrapers.google_news_rss import search_google_news_rss

        rss_all = []
        for lang in search_langs:
            rss_results = search_google_news_rss(primary_name, lang=lang)
            if rss_results:
                for r in rss_results:
                    r.setdefault("data", {})["scraper"] = "google_news_rss"
                    r["confidence"] = compute_name_match_confidence(
                        r.get("description", "") or r.get("title", ""),
                        primary_name,
                    )
                rss_results = [r for r in rss_results if r.get("confidence", 0) >= 0.60]
                rss_all.extend(rss_results)
                logger.info("PASS2: Google News RSS found %d articles (lang=%s)", len(rss_results), lang)

            time.sleep(3.0)

        # Dedup against GDELT + GNews
        rss_unique = deduplicate_media_findings(rss_all, all_findings)
        all_findings.extend(rss_unique)
        result["scrapers_run"] += 1
    except Exception:
        logger.exception("PASS2: Google News RSS scraper failed")

    # --- 4. Apply global cap on media findings ---
    all_findings = select_top_findings(all_findings, MAX_FINDINGS_PER_TARGET)

    # === COMPLIANCE LAYER (Sprint 63) ===
    sanctions_findings = []

    # --- 5. OpenSanctions (sanctions + PEP + wanted) ---
    try:
        from api.scrapers.opensanctions_search import search_opensanctions

        # Extract target context for better matching
        nationality = _get_target_nationality(profile)
        target_country = _get_target_country(target, profile)
        birth_year = _get_estimated_birth_year(profile)

        os_results = search_opensanctions(
            primary_name,
            nationality=nationality,
            country=target_country,
            birth_year=birth_year,
            name_match_fn=compute_name_match_confidence,
        )
        if os_results:
            sanctions_findings.extend(os_results)
            logger.info("PASS2: OpenSanctions found %d matches", len(os_results))

        result["scrapers_run"] += 1
        time.sleep(1.5)
    except Exception:
        logger.exception("PASS2: OpenSanctions scraper failed")

    # --- 6. Interpol direct (only if OpenSanctions didn't already find Interpol) ---
    has_interpol_from_os = any(
        "interpol" in str(f.get("data", {}).get("datasets", [])).lower()
        for f in sanctions_findings
    )
    if not has_interpol_from_os:
        try:
            from api.scrapers.interpol_red_notices import search_interpol_red_notices

            target_country = _get_target_country(target, profile)
            birth_year = _get_estimated_birth_year(profile)

            interpol_results = search_interpol_red_notices(
                primary_name,
                target_country=target_country,
                target_birth_year=birth_year,
            )
            if interpol_results:
                sanctions_findings.extend(interpol_results)
                logger.info("PASS2: Interpol found %d red notices", len(interpol_results))

            result["scrapers_run"] += 1
            time.sleep(2.0)
        except Exception:
            logger.exception("PASS2: Interpol scraper failed")
    else:
        logger.debug("PASS2: Interpol skipped — already found via OpenSanctions")

    # === STORE ALL FINDINGS ===
    all_to_store = all_findings + sanctions_findings

    if all_to_store:
        created = 0
        for fd in all_to_store:
            try:
                # Determine indicator_type: sanctions findings have their own, media uses default
                ind_type = fd.get("indicator_type", "media_mention")
                category = "public_exposure"
                if ind_type in ("sanctions_match", "pep_match"):
                    category = "compliance"

                finding = Finding(
                    workspace_id=target.workspace_id,
                    scan_id=None,
                    target_id=target_id,
                    module="scraper_engine",
                    layer=4,
                    category=category,
                    severity=fd.get("severity", "info"),
                    title=fd.get("title", f"Media mention: {primary_name}")[:255],
                    description=fd.get("description"),
                    data=fd.get("data", {}),
                    url=fd.get("url"),
                    indicator_value=(fd.get("indicator_value") or fd.get("url") or fd.get("title", ""))[:500],
                    indicator_type=ind_type,
                    verified=False,
                    confidence=round(fd.get("confidence", 0.60), 3),
                )
                session.add(finding)
                created += 1
            except Exception:
                logger.exception("PASS2: Failed to create finding: %s", fd.get("title", "")[:80])

        if created > 0:
            session.commit()
            result["findings_created"] = created

    logger.info(
        "PASS2: Completed for target %s — %d scrapers, %d findings stored (%d media + %d sanctions)",
        target_id, result["scrapers_run"], result["findings_created"],
        len(all_findings), len(sanctions_findings),
    )
    return result


# ---------------------------------------------------------------------------
# Target Context Helpers (for sanctions matching)
# ---------------------------------------------------------------------------

def _get_target_nationality(profile: dict) -> str | None:
    """Extract nationality from profile identity_estimation."""
    est = profile.get("identity_estimation", {})
    nats = est.get("nationalities", [])
    if nats and isinstance(nats, list):
        for n in nats:
            if isinstance(n, dict) and n.get("probability", 0) >= 0.20:
                return n.get("country_id", "")
    return None


def _get_target_country(target, profile: dict) -> str | None:
    """Extract country from target locations or email TLD."""
    locations = profile.get("user_locations", []) or profile.get("geo_locations", [])
    if locations and isinstance(locations, list):
        for loc in locations:
            if isinstance(loc, dict):
                country = loc.get("country_code", "") or loc.get("country", "")
                if country:
                    return country.upper()

    # Fallback: email TLD
    email = getattr(target, "value", "") or ""
    if "@" in email:
        domain = email.split("@")[1].lower()
        tld_map = {".lu": "LU", ".fr": "FR", ".de": "DE", ".be": "BE", ".ch": "CH",
                   ".it": "IT", ".es": "ES", ".nl": "NL", ".at": "AT", ".pt": "PT"}
        for tld, code in tld_map.items():
            if domain.endswith(tld):
                return code
    return None


def _get_estimated_birth_year(profile: dict) -> int | None:
    """Extract estimated birth year from Agify result."""
    est = profile.get("identity_estimation", {})
    age = est.get("age")
    if age and isinstance(age, (int, float)) and 10 < age < 120:
        from datetime import date as date_cls
        return date_cls.today().year - int(age)
    return None
