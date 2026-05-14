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


def _sanitize_for_json(obj):
    """Recursively convert non-JSON-serializable types for JSONB storage."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, set):
        return list(obj)
    elif hasattr(obj, '__str__') and not isinstance(obj, (str, int, float, bool, type(None))):
        return str(obj)
    return obj

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


def _get_primary_name(target) -> str | None:
    """Get the best name to use for Pass 2 searches.
    Priority: operator assertion > auto-resolved from profile."""
    user_first = getattr(target, 'user_first_name', None)
    user_last = getattr(target, 'user_last_name', None)
    if user_first or user_last:
        return ' '.join(p for p in [user_first, user_last] if p)
    profile = getattr(target, 'profile_data', None) or {}
    return profile.get('primary_name')


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
    """Determine search languages based on target context. Max 2.

    Priority: ground truth country_code > email TLD > profile locations.
    """
    langs = ["en"]

    # Priority 1: ground truth country_code
    country_code = getattr(target, "country_code", None)
    if country_code:
        lang = COUNTRY_LANG_MAP.get(country_code.upper())
        if lang and lang not in langs:
            langs.append(lang)

    # Priority 2: email domain TLD
    if len(langs) < 2:
        email = getattr(target, "email", "") or ""
        if "@" in email:
            domain = email.split("@")[1].lower()
            for tld, lang in TLD_LANG_MAP.items():
                if domain.endswith(tld):
                    if lang not in langs:
                        langs.append(lang)
                    break

    # Priority 3: profile locations
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

def enrich_public_exposure(target_id, session: Session, scan_id=None) -> dict:
    """Pass 2 enrichment: run name-based scrapers with layer isolation.

    Each layer (media, compliance, corporate) is independently wrapped.
    Each scraper within a layer is independently wrapped.
    An error in one scraper NEVER prevents other scrapers from running.
    """
    results = {
        "media": [], "sanctions": [], "corporate": [], "legal": [],
        "errors": [], "scrapers_run": 0, "findings_created": 0,
        "skipped_reason": None,
    }

    target = session.execute(
        select(Target).where(Target.id == target_id)
    ).scalar_one_or_none()

    if not target:
        results["skipped_reason"] = "target_not_found"
        return results

    profile = target.profile_data or {}

    # Operator-asserted name takes priority for Pass 2 searches
    primary_name = _get_primary_name(target)

    if not primary_name:
        results["skipped_reason"] = "no_primary_name"
        logger.debug("PASS2: Skipping %s — no primary_name", target_id)
        return results

    if not _is_real_name(primary_name):
        results["skipped_reason"] = "username_like_name"
        logger.debug("PASS2: Skipping %s — name '%s' looks like username", target_id, primary_name)
        return results

    logger.info("PASS2: Running public exposure enrichment for '%s' (target %s)", primary_name, target_id)

    # Determine search languages (ground truth country_code takes priority)
    search_langs = get_search_languages(target)
    logger.info("PASS2: Search languages for '%s': %s", primary_name, search_langs)

    # Extract email domain for context
    email = getattr(target, "email", "") or ""
    email_domain = email.split("@")[1] if "@" in email else None

    # Build search context from email domain + profile location
    _FREEMAIL = {"gmail", "yahoo", "hotmail", "outlook", "protonmail", "icloud",
                 "aol", "live", "mail", "email", "ymail", "rocketmail", "gmx",
                 "zoho", "fastmail", "tutanota", "hey", "pm", "posteo", "mailbox",
                 "free", "orange", "wanadoo", "sfr", "laposte", "bbox", "web"}
    search_context = None
    if email_domain and "." in email_domain:
        company = email_domain.split(".")[0]
        if len(company) > 3 and company.lower() not in _FREEMAIL:
            search_context = company

    # Enrich with city if available
    _profile = target.profile_data or {}
    _user_locs = _profile.get("user_locations", [])
    if isinstance(_user_locs, list):
        for _loc in _user_locs:
            if isinstance(_loc, dict):
                _city = _loc.get("city", "")
                if _city and len(_city) > 2:
                    search_context = f"{search_context} {_city}" if search_context else _city
                    break

    if search_context:
        logger.info("PASS2: Search context for '%s': %s", primary_name, search_context)

    # === MEDIA LAYER ===

    # 1. GDELT (free, deep archive)
    gdelt_findings = []
    gdelt_errored = False
    try:
        from api.scrapers.gdelt_news import search_gdelt_news

        raw = search_gdelt_news(primary_name, domain=email_domain)
        if raw:
            for r in raw:
                r.setdefault("data", {})["scraper"] = "gdelt_news"
                r["confidence"] = compute_name_match_confidence(
                    r.get("description", "") or r.get("title", ""), primary_name,
                )
            gdelt_findings = [r for r in raw if r.get("confidence", 0) >= 0.60]
            results["media"].extend(gdelt_findings)
            logger.info("PASS2: GDELT found %d articles", len(gdelt_findings))

        results["scrapers_run"] += 1
        time.sleep(1.0)
    except Exception as e:
        gdelt_errored = True
        logger.warning("PASS2: GDELT failed: %s", e)
        results["errors"].append(f"gdelt_news: {str(e)[:100]}")

    # 2. GNews (conditional: needs GDELT results OR GDELT errored)
    try:
        gnews_api_key = _get_gnews_api_key(session, target.workspace_id)
        if gnews_api_key and (len(gdelt_findings) > 0 or gdelt_errored):
            if should_run_gnews(max(len(gdelt_findings), 1) if gdelt_errored else len(gdelt_findings)):
                from api.scrapers.gnews_news import search_gnews

                gnews_all = []
                for lang in search_langs:
                    gnews_results = search_gnews(primary_name, api_key=gnews_api_key, lang=lang, context=search_context)
                    _increment_gnews_usage(1)
                    if gnews_results:
                        for r in gnews_results:
                            r.setdefault("data", {})["scraper"] = "gnews_news"
                            r["confidence"] = compute_name_match_confidence(
                                r.get("description", "") or r.get("title", ""), primary_name,
                            )
                        gnews_all.extend([r for r in gnews_results if r.get("confidence", 0) >= 0.60])
                        logger.info("PASS2: GNews found %d articles (lang=%s)", len(gnews_results), lang)
                    time.sleep(1.5)

                gnews_unique = deduplicate_media_findings(gnews_all, results["media"])
                results["media"].extend(gnews_unique)
                results["scrapers_run"] += 1
    except Exception as e:
        logger.warning("PASS2: GNews failed: %s", e)
        results["errors"].append(f"gnews_news: {str(e)[:100]}")

    # 3. Google News RSS (ALWAYS runs — free, no API key, no quota)
    try:
        from api.scrapers.google_news_rss import search_google_news_rss

        rss_all = []
        for lang in search_langs:
            rss_results = search_google_news_rss(primary_name, lang=lang, context=search_context)
            if rss_results:
                for r in rss_results:
                    r.setdefault("data", {})["scraper"] = "google_news_rss"
                    r["confidence"] = compute_name_match_confidence(
                        r.get("description", "") or r.get("title", ""), primary_name,
                    )
                rss_all.extend([r for r in rss_results if r.get("confidence", 0) >= 0.60])
                logger.info("PASS2: Google News RSS found %d articles (lang=%s)", len(rss_results), lang)
            time.sleep(3.0)

        rss_unique = deduplicate_media_findings(rss_all, results["media"])
        results["media"].extend(rss_unique)
        results["scrapers_run"] += 1
    except Exception as e:
        logger.warning("PASS2: Google News RSS failed: %s", e)
        results["errors"].append(f"google_news_rss: {str(e)[:100]}")

    # Cap media at 15
    results["media"] = select_top_findings(results["media"], MAX_FINDINGS_PER_TARGET)

    # === COMPLIANCE LAYER ===

    # Extract target context (ground truth country_code takes priority)
    nationality = _get_target_nationality(target)
    target_country = _get_target_country(target)
    birth_year = _get_estimated_birth_year(target)

    # 4. OpenSanctions
    try:
        from api.scrapers.opensanctions_search import search_opensanctions

        os_api_key = _get_opensanctions_api_key(session, target.workspace_id)
        os_results = search_opensanctions(
            primary_name, nationality=nationality, country=target_country,
            birth_year=birth_year, name_match_fn=compute_name_match_confidence,
            api_key=os_api_key,
        )
        if os_results:
            results["sanctions"].extend(os_results)
            logger.info("PASS2: OpenSanctions found %d matches", len(os_results))

        results["scrapers_run"] += 1
        time.sleep(1.5)
    except Exception as e:
        logger.warning("PASS2: OpenSanctions failed: %s", e)
        results["errors"].append(f"opensanctions_search: {str(e)[:100]}")

    # 5. Interpol (conditional on OpenSanctions results, NOT on success)
    try:
        has_interpol = any(
            "interpol" in str(f.get("data", {}).get("datasets", [])).lower()
            for f in results["sanctions"]
        )
        if not has_interpol:
            from api.scrapers.interpol_red_notices import search_interpol_red_notices

            interpol_results = search_interpol_red_notices(
                primary_name, target_country=target_country, target_birth_year=birth_year,
            )
            if interpol_results:
                results["sanctions"].extend(interpol_results)
                logger.info("PASS2: Interpol found %d red notices", len(interpol_results))

            results["scrapers_run"] += 1
            time.sleep(2.0)
        else:
            logger.debug("PASS2: Interpol skipped — already found via OpenSanctions")
    except Exception as e:
        logger.warning("PASS2: Interpol failed: %s", e)
        results["errors"].append(f"interpol_red_notices: {str(e)[:100]}")

    # 5b. Courtlistener (US federal court records — MVP: collection only, no axis math)
    try:
        from api.scrapers.courtlistener_search import search_courtlistener

        cl_api_key = _get_courtlistener_api_key(session, target.workspace_id)
        cl_results = search_courtlistener(primary_name, api_key=cl_api_key)
        if cl_results:
            results["legal"].extend(cl_results)
            logger.info("PASS2: Courtlistener found %d legal records", len(cl_results))

        results["scrapers_run"] += 1
        time.sleep(1.5)
    except Exception as e:
        logger.warning("PASS2: Courtlistener failed: %s", e)
        results["errors"].append(f"courtlistener_search: {str(e)[:100]}")

    # 5c. BODACC (FR commercial register / procédures collectives)
    try:
        from api.scrapers.bodacc_search import search_bodacc

        bodacc_results = search_bodacc(primary_name)
        if bodacc_results:
            results["legal"].extend(bodacc_results)
            logger.info("PASS2: BODACC found %d legal records", len(bodacc_results))

        results["scrapers_run"] += 1
        time.sleep(1.5)
    except Exception as e:
        logger.warning("PASS2: BODACC failed: %s", e)
        results["errors"].append(f"bodacc_search: {str(e)[:100]}")

    # 5d. UK Gazette (UK official public record / insolvency / probate)
    try:
        from api.scrapers.uk_gazette_search import search_uk_gazette

        gazette_results = search_uk_gazette(primary_name)
        if gazette_results:
            results["legal"].extend(gazette_results)
            logger.info("PASS2: UK Gazette found %d notices", len(gazette_results))

        results["scrapers_run"] += 1
        time.sleep(11)  # robots.txt mandated crawl delay
    except Exception as e:
        logger.warning("PASS2: UK Gazette failed: %s", e)
        results["errors"].append(f"uk_gazette_search: {str(e)[:100]}")

    # === CORPORATE LAYER ===

    # 6. OpenCorporates
    oc_findings = []
    try:
        from api.scrapers.opencorporates_officers import search_opencorporates

        oc_api_key = _get_opencorporates_api_key(session, target.workspace_id)
        oc_results = search_opencorporates(
            primary_name, api_key=oc_api_key, target_country=target_country,
        )
        if oc_results:
            oc_findings = oc_results
            results["corporate"].extend(oc_results)
            logger.info("PASS2: OpenCorporates found %d officer roles", len(oc_results))

        _increment_opencorporates_usage(1)
        results["scrapers_run"] += 1
        time.sleep(2.0)
    except Exception as e:
        logger.warning("PASS2: OpenCorporates failed: %s", e)
        results["errors"].append(f"opencorporates_officers: {str(e)[:100]}")

    # 7. LBR Luxembourg (conditional on country)
    try:
        if _should_run_lbr(target):
            from api.scrapers.lbr_luxembourg import search_lbr_luxembourg

            lbr_results = search_lbr_luxembourg(primary_name)
            if lbr_results:
                lbr_unique = _deduplicate_corporate_findings(lbr_results, oc_findings)
                results["corporate"].extend(lbr_unique)
                logger.info("PASS2: LBR found %d officer roles (%d unique)", len(lbr_results), len(lbr_unique))

            results["scrapers_run"] += 1
            time.sleep(3.0)
        else:
            logger.debug("PASS2: LBR skipped — target not Luxembourg-connected")
    except Exception as e:
        logger.warning("PASS2: LBR failed: %s", e)
        results["errors"].append(f"lbr_luxembourg: {str(e)[:100]}")

    # Cap corporate at 8, prioritize active roles
    results["corporate"].sort(key=lambda f: (
        -int(f.get("data", {}).get("is_active", False)),
        -f.get("confidence", 0),
    ))
    results["corporate"] = results["corporate"][:MAX_CORPORATE_FINDINGS]

    # === STORE ALL (even partial results) ===
    all_to_store = results["media"] + results["sanctions"] + results["corporate"] + results["legal"]

    if all_to_store:
        created = 0
        for fd in all_to_store:
            try:
                ind_type = fd.get("indicator_type", "media_mention")
                category = "public_exposure"
                if ind_type in ("sanctions_match", "pep_match"):
                    category = "compliance"
                elif ind_type == "corporate_officer":
                    category = "corporate"

                # Use actual scraper name from data, not generic "scraper_engine"
                scraper_name = (fd.get("data") or {}).get("scraper", "scraper_engine")

                finding = Finding(
                    workspace_id=target.workspace_id,
                    scan_id=scan_id,
                    target_id=target_id,
                    module=scraper_name[:50],
                    layer=4,
                    category=category,
                    severity=fd.get("severity", "info"),
                    title=fd.get("title", f"Media mention: {primary_name}")[:255],
                    description=(fd.get("description") or "")[:1000] or None,
                    data=_sanitize_for_json(fd.get("data", {})),
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
            try:
                session.flush()
                results["findings_created"] = created
                logger.info("PASS2: Stored %d findings (flushed)", created)
            except Exception:
                logger.exception("PASS2: Failed to flush findings")
                session.rollback()

    # === CREATE GRAPH EDGES ===
    if results["findings_created"] > 0:
        try:
            _create_pe_graph_edges(all_to_store, target, session)
        except Exception:
            logger.warning("PASS2: Graph edge creation failed", exc_info=True)

    logger.info(
        "PASS2 complete for '%s': %d media, %d sanctions, %d corporate, %d legal, %d errors",
        primary_name, len(results["media"]), len(results["sanctions"]),
        len(results["corporate"]), len(results["legal"]), len(results["errors"]),
    )
    if results["errors"]:
        logger.warning("PASS2 errors: %s", results["errors"])

    return results


# ---------------------------------------------------------------------------
# Graph Edge Creation for PE Findings
# ---------------------------------------------------------------------------

# PE edge types are WEAK — excluded from clustering, used for PageRank only
_PE_EDGE_TYPES = {
    "media_mention": "mentioned_in",
    "sanctions_match": "listed_on",
    "pep_match": "listed_on",
    "corporate_officer": "officer_of",
}


def _create_pe_graph_edges(finding_dicts: list, target, session):
    """Create identity graph edges for public exposure findings.

    Creates weak edges (excluded from clustering) between the email anchor
    and PE entity nodes.
    """
    from api.models.identity import Identity, IdentityLink

    # Get email anchor node
    email_node = session.execute(
        select(Identity).where(
            Identity.target_id == target.id,
            Identity.type == "email",
        )
    ).scalars().first()

    if not email_node:
        logger.debug("PASS2: No email anchor node — skipping PE graph edges")
        return

    edges_created = 0
    for fd in finding_dicts:
        ind_type = fd.get("indicator_type", "media_mention")
        edge_type = _PE_EDGE_TYPES.get(ind_type)
        if not edge_type:
            continue

        data = fd.get("data", {})
        display = fd.get("title", fd.get("url", ""))[:200]
        confidence = fd.get("confidence", 0.5)

        try:
            entity_node = Identity(
                target_id=target.id,
                workspace_id=target.workspace_id,
                type=ind_type,
                value=(fd.get("indicator_value") or fd.get("url") or display)[:500],
                platform=data.get("scraper", "public_exposure"),
                source_module=data.get("scraper", "public_exposure"),
                confidence=confidence,
            )
            session.add(entity_node)
            session.flush()

            link = IdentityLink(
                workspace_id=target.workspace_id,
                source_id=email_node.id,
                dest_id=entity_node.id,
                link_type=edge_type,
                confidence=confidence,
                source_module=data.get("scraper", "public_exposure"),
            )
            session.add(link)
            edges_created += 1
        except Exception:
            logger.debug("PASS2: Failed to create edge for %s", display[:60], exc_info=True)

    if edges_created > 0:
        session.flush()
        logger.info("PASS2: Created %d graph edges", edges_created)


# ---------------------------------------------------------------------------
# Target Context Helpers (for sanctions matching)
# ---------------------------------------------------------------------------

def _get_target_nationality(target) -> str | None:
    """Extract nationality from profile_data identity_estimation."""
    profile = getattr(target, "profile_data", None) or {}
    est = profile.get("identity_estimation", {})
    nats = est.get("nationalities", [])
    if nats and isinstance(nats, list):
        for n in nats:
            if isinstance(n, dict) and n.get("probability", 0) >= 0.20:
                return n.get("country_id", "")
    return None


def _get_target_country(target) -> str | None:
    """Get target country. Ground truth (country_code) takes priority."""
    # Priority 1: operator-set ground truth
    country_code = getattr(target, "country_code", None)
    if country_code:
        return country_code.upper()

    # Priority 2: profile locations
    profile = getattr(target, "profile_data", None) or {}
    locations = profile.get("user_locations", []) or profile.get("geo_locations", [])
    if locations and isinstance(locations, list):
        for loc in locations:
            if isinstance(loc, dict):
                country = loc.get("country_code", "") or loc.get("country", "")
                if country:
                    return country.upper()

    # Priority 3: email TLD
    email = getattr(target, "email", "") or ""
    if "@" in email:
        domain = email.split("@")[1].lower()
        tld_map = {".lu": "LU", ".fr": "FR", ".de": "DE", ".be": "BE", ".ch": "CH",
                   ".it": "IT", ".es": "ES", ".nl": "NL", ".at": "AT", ".pt": "PT"}
        for tld, code in tld_map.items():
            if domain.endswith(tld):
                return code
    return None


def _get_estimated_birth_year(target) -> int | None:
    """Extract estimated birth year from profile_data Agify result."""
    profile = getattr(target, "profile_data", None) or {}
    est = profile.get("identity_estimation", {})
    age = est.get("age")
    if age and isinstance(age, (int, float)) and 10 < age < 120:
        from datetime import date as date_cls
        return date_cls.today().year - int(age)
    return None


# ---------------------------------------------------------------------------
# Corporate Layer Helpers (Sprint 64)
# ---------------------------------------------------------------------------

MAX_CORPORATE_FINDINGS = 8


def _should_run_lbr(target) -> bool:
    """Only run LBR on Luxembourg-connected targets."""
    # Ground truth first
    country_code = getattr(target, "country_code", None)
    if country_code and country_code.upper() == "LU":
        return True
    # Fallback: inferred country
    country = _get_target_country(target)
    if country and country.upper() == "LU":
        return True
    # Fallback: email domain
    email = getattr(target, "email", "") or ""
    if "@" in email and email.split("@")[1].lower().endswith(".lu"):
        return True
    return False


def _get_opensanctions_api_key(session: Session, workspace_id) -> str | None:
    """Retrieve OpenSanctions API key from workspace settings."""
    try:
        from api.models.workspace import Workspace
        ws = session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        ).scalar_one_or_none()
        if not ws:
            return None
        settings = ws.settings or {}
        for store in ("custom_api_keys", "api_keys"):
            entry = settings.get(store, {}).get("opensanctions_api_key")
            if entry and isinstance(entry, dict) and entry.get("encrypted"):
                try:
                    from api.routers.settings import _get_fernet
                    return _get_fernet().decrypt(entry["encrypted"].encode()).decode()
                except Exception:
                    return None
            elif entry and isinstance(entry, str):
                return entry
    except Exception:
        pass
    return None


def _get_courtlistener_api_key(session: Session, workspace_id) -> str | None:
    """Retrieve Courtlistener API token from workspace settings."""
    try:
        from api.models.workspace import Workspace
        ws = session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        ).scalar_one_or_none()
        if not ws:
            return None
        settings = ws.settings or {}
        for store in ("custom_api_keys", "api_keys"):
            entry = settings.get(store, {}).get("courtlistener_api_key")
            if entry and isinstance(entry, dict) and entry.get("encrypted"):
                try:
                    from api.routers.settings import _get_fernet
                    return _get_fernet().decrypt(entry["encrypted"].encode()).decode()
                except Exception:
                    return None
            elif entry and isinstance(entry, str):
                return entry
    except Exception:
        pass
    return None


def _get_opencorporates_api_key(session: Session, workspace_id) -> str | None:
    """Retrieve OpenCorporates API key from workspace settings."""
    try:
        from api.models.workspace import Workspace
        ws = session.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        ).scalar_one_or_none()
        if not ws:
            return None
        settings = ws.settings or {}
        for store in ("custom_api_keys", "api_keys"):
            entry = settings.get(store, {}).get("opencorporates_api_key")
            if entry and isinstance(entry, dict) and entry.get("encrypted"):
                try:
                    from api.routers.settings import _get_fernet
                    return _get_fernet().decrypt(entry["encrypted"].encode()).decode()
                except Exception:
                    return None
            elif entry and isinstance(entry, str):
                return entry
    except Exception:
        pass
    return None


def _increment_opencorporates_usage(count: int = 1):
    """Increment OpenCorporates monthly usage counter in Redis."""
    try:
        from api.services.cache import CacheService
        cache = CacheService()
        if cache.redis:
            key = f"opencorporates:monthly_count:{date.today().strftime('%Y-%m')}"
            pipe = cache.redis.pipeline()
            pipe.incrby(key, count)
            pipe.expire(key, 86400 * 31)
            pipe.execute()
    except Exception:
        pass


def _deduplicate_corporate_findings(new_findings: list, existing_findings: list) -> list:
    """Dedup corporate findings: match by company name similarity + jurisdiction.

    Keep the one with higher source reliability (LBR > OpenCorporates for LU).
    """
    if not new_findings or not existing_findings:
        return new_findings

    from difflib import SequenceMatcher

    existing_companies = []
    for f in existing_findings:
        data = f.get("data", {}) or {}
        existing_companies.append({
            "company": (data.get("company_name") or "").lower().strip(),
            "jurisdiction": (data.get("jurisdiction") or "").lower(),
            "position": (data.get("position") or "").lower(),
            "scraper": data.get("scraper", ""),
        })

    unique = []
    for nf in new_findings:
        ndata = nf.get("data", {}) or {}
        n_company = (ndata.get("company_name") or "").lower().strip()
        n_jurisdiction = (ndata.get("jurisdiction") or "").lower()
        n_scraper = ndata.get("scraper", "")

        is_dup = False
        for ec in existing_companies:
            # Same jurisdiction
            if n_jurisdiction and ec["jurisdiction"] and n_jurisdiction != ec["jurisdiction"]:
                continue
            # Company name similarity > 0.80
            sim = SequenceMatcher(None, n_company, ec["company"]).ratio()
            if sim > 0.80:
                # It's a duplicate — keep LBR over OpenCorporates for LU
                if n_scraper == "lbr_luxembourg" and ec["scraper"] == "opencorporates_officers":
                    # Replace existing with LBR (higher reliability)
                    for i, ef in enumerate(existing_findings):
                        ef_data = ef.get("data", {}) or {}
                        if (ef_data.get("company_name") or "").lower().strip() == ec["company"]:
                            existing_findings[i] = nf
                            break
                is_dup = True
                break

        if not is_dup:
            unique.append(nf)

    return unique
