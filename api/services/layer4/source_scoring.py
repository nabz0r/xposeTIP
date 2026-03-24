"""Source scoring and finding confidence computation.

Each scanner module has a reliability weight based on data quality.
Each finding gets a confidence score based on source reliability,
verification status, and cross-referencing with other findings.
"""
import logging
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.finding import Finding

logger = logging.getLogger(__name__)

# Each module has a reliability weight based on data quality
SOURCE_RELIABILITY = {
    # High reliability — direct API data, verified
    "hibp": 0.95,              # Official breach database
    "dns_deep": 0.95,          # DNS records are facts
    "email_validator": 0.90,   # MX/DNS checks are deterministic

    # Medium-high — structured APIs, mostly accurate
    "emailrep": 0.85,          # Aggregated reputation, generally accurate
    "fullcontact": 0.80,       # Person enrichment, can be outdated
    "github_deep": 0.85,       # GitHub API is authoritative for GH data
    "gravatar": 0.80,          # User-controlled profile, may be outdated

    # Medium — heuristic-based, some false positives
    "holehe": 0.70,            # Email registration check, some sites unreliable
    "geoip": 0.65,             # IP geoloc is approximate, mail server != user
    "whois_lookup": 0.60,      # WHOIS data often redacted/outdated
    "google_profile": 0.60,    # YouTube search is fuzzy matching
    "epieos": 0.70,            # Google ID lookup, depends on availability

    # Lower — inference-based, higher false positive rate
    "username_hunter": 0.50,   # Username matching across platforms is probabilistic
    "sherlock": 0.55,          # Similar to username_hunter
    "social_enricher": 0.65,   # Depends on public profile availability
    "leaked_domains": 0.75,    # XposedOrNot is less curated than HIBP
    "maxmind_geo": 0.70,       # Local DB, accurate but mail server != user

    # Layer 2 — Premium APIs
    "virustotal": 0.90,        # VirusTotal is authoritative for domain/malware data
    "shodan": 0.90,            # Shodan is authoritative for port/service data
    "intelx": 0.80,            # Intelligence X — darkweb/paste, variable quality
    "hunter": 0.75,            # Hunter.io — email discovery, can be outdated
    "dehashed": 0.85,          # Dehashed — breach data, reliable but aggregated

    # Layer 1 — Reverse image
    "reverse_image": 0.70,     # Face matching is probabilistic

    # Layer 3 — SaaS connectors (OAuth, high reliability)
    "google_audit": 0.95,      # Direct from Google API with OAuth
    "microsoft_audit": 0.95,   # Direct from Microsoft Graph with OAuth

    # Layer 1 — Scraper engine (DB-defined scrapers)
    "scraper_engine": 0.60,    # Community/custom scrapers, variable quality

    # Layer 4 — Intelligence engine
    "intelligence": 0.90,      # Auto-generated cross-referencing, high quality
}

# Default reliability for unknown/new modules
DEFAULT_RELIABILITY = 0.50

# Per-scraper reliability overrides for scraper_engine findings
# These scrapers have higher data quality than the generic 0.60
SCRAPER_RELIABILITY_OVERRIDES = {
    "github_user_api": 0.85,      # Official API, structured JSON
    "github_scraper": 0.80,       # GitHub profile page
    "gitlab_profile": 0.75,       # GitLab profile
    "keybase_profile": 0.80,      # Keybase is identity-verified
    "mailcheck_email": 0.85,      # Email validation API
    "dns_txt_saas": 0.90,         # DNS records are facts
    "rdap_domain": 0.90,          # RDAP is authoritative
    "dns_dmarc_check": 0.90,      # DNS records are facts
    "leakcheck_public": 0.80,     # Breach data
    "emailrep_breaches": 0.80,    # Breach aggregator
    "gdelt_news": 0.65,           # GDELT news search — free API, variable relevance
}


def get_source_reliability(module_id: str, scraper_name: str | None = None) -> float:
    """Get the reliability weight for a scanner module.

    For scraper_engine findings, pass scraper_name to get per-scraper overrides.
    """
    if module_id == "scraper_engine" and scraper_name:
        override = SCRAPER_RELIABILITY_OVERRIDES.get(scraper_name)
        if override:
            return override
    return SOURCE_RELIABILITY.get(module_id, DEFAULT_RELIABILITY)


def compute_finding_confidence(finding) -> float:
    """Compute confidence score for a single finding.

    Confidence = source_reliability * verification_multiplier

    verification_multiplier:
    - finding.verified = True -> 1.0
    - finding.verified = False but has URL -> 0.8
    - finding.verified = False, no URL -> 0.6
    - category is 'metadata' (DNS, email validation) -> always 1.0
    """
    source_rel = get_source_reliability(finding.module)

    # Metadata category findings are deterministic (DNS records, email validation)
    if finding.category == "metadata":
        return min(1.0, source_rel * 1.0)

    # Verification multiplier
    if finding.verified:
        verification_mult = 1.0
    elif finding.url:
        verification_mult = 0.8
    else:
        verification_mult = 0.6

    return round(min(1.0, source_rel * verification_mult), 3)


def cross_verify_findings(target_id, session: Session) -> int:
    """Cross-verify findings from multiple sources.

    If the same indicator appears from multiple sources, boost confidence.

    Example:
    - holehe says "account on GitHub" (confidence 0.70)
    - github_deep confirms with full profile (confidence 0.85)
    -> Both get boosted to 0.95 (cross-verified)

    - username_hunter says "found on Reddit" (confidence 0.50)
    - No other source confirms
    -> Stays at 0.50

    Returns the number of findings that were cross-verified.
    """
    findings = session.execute(
        select(Finding).where(
            Finding.target_id == target_id,
            Finding.status == "active",
        )
    ).scalars().all()

    if not findings:
        return 0

    # Group findings by indicator_value (non-null only)
    by_indicator = defaultdict(list)
    for f in findings:
        if f.indicator_value:
            by_indicator[f.indicator_value].append(f)

    # Also group by normalized title keywords for fuzzy cross-ref
    # e.g., "GitHub" appearing in both holehe and github_deep findings
    by_platform = defaultdict(list)
    platform_keywords = [
        "github", "twitter", "reddit", "linkedin", "facebook", "instagram",
        "steam", "keybase", "gitlab", "medium", "youtube", "tiktok",
        "pinterest", "tumblr", "spotify", "discord",
    ]
    for f in findings:
        title_lower = (f.title or "").lower()
        for kw in platform_keywords:
            if kw in title_lower:
                by_platform[kw].append(f)
                break

    cross_verified_count = 0
    CROSS_VERIFIED_BOOST = 0.95

    # Boost findings confirmed by multiple sources (same indicator)
    for indicator, group in by_indicator.items():
        unique_modules = set(f.module for f in group)
        if len(unique_modules) >= 2:
            for f in group:
                if f.confidence is not None and f.confidence < CROSS_VERIFIED_BOOST:
                    f.confidence = CROSS_VERIFIED_BOOST
                    cross_verified_count += 1

    # Boost findings confirmed by multiple sources (same platform)
    for platform, group in by_platform.items():
        unique_modules = set(f.module for f in group)
        if len(unique_modules) >= 2:
            for f in group:
                if f.confidence is not None and f.confidence < CROSS_VERIFIED_BOOST:
                    f.confidence = CROSS_VERIFIED_BOOST
                    cross_verified_count += 1

    if cross_verified_count > 0:
        session.commit()
        logger.info(
            "Cross-verified %d findings for target %s",
            cross_verified_count, target_id,
        )

    return cross_verified_count


def compute_source_scores(target_id, session: Session) -> dict:
    """Compute per-source scoring for a target.

    Returns:
    {
        "sources": [
            {
                "module": "dns_deep",
                "reliability": 0.95,
                "findings_count": 6,
                "verified_count": 6,
                "avg_confidence": 0.95,
                "categories_found": ["metadata"],
            },
            ...
        ],
        "overall_confidence": 0.72,
        "cross_verified_count": 3
    }
    """
    findings = session.execute(
        select(Finding).where(
            Finding.target_id == target_id,
            Finding.status == "active",
        )
    ).scalars().all()

    if not findings:
        return {"sources": [], "overall_confidence": 0.0, "cross_verified_count": 0}

    # Group by module
    by_module = defaultdict(list)
    for f in findings:
        by_module[f.module].append(f)

    sources = []
    total_confidence = 0.0
    total_count = 0
    cross_verified = 0

    for module_id, module_findings in sorted(by_module.items()):
        reliability = get_source_reliability(module_id)
        verified_count = sum(1 for f in module_findings if f.verified)
        confidences = [f.confidence for f in module_findings if f.confidence is not None]
        avg_conf = sum(confidences) / len(confidences) if confidences else reliability
        categories = list(set(f.category for f in module_findings))
        cv_count = sum(
            1 for f in module_findings
            if f.confidence is not None and f.confidence >= 0.95
            and not f.verified  # cross-verified, not natively verified
        )
        cross_verified += cv_count

        sources.append({
            "module": module_id,
            "reliability": reliability,
            "findings_count": len(module_findings),
            "verified_count": verified_count,
            "avg_confidence": round(avg_conf, 3),
            "categories_found": categories,
        })

        total_confidence += avg_conf * len(module_findings)
        total_count += len(module_findings)

    overall = round(total_confidence / total_count, 3) if total_count > 0 else 0.0

    return {
        "sources": sources,
        "overall_confidence": overall,
        "cross_verified_count": cross_verified,
    }
