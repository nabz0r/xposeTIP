"""S304a — finding freshness. valid_until = last_seen + TTL, TTL driven by data-type
volatility (NOT source reliability), overridable per scraper. Descriptive in S304a —
does not touch confidence. Consumed by S304d smart-rescan + S304e manual re-trigger."""

DAY = 86400
DEFAULT_TTL = 30 * DAY

# Volatility by finding category (score_engine EXPOSURE/THREAT category set).
TTL_BY_CATEGORY = {
    "breach": 365 * DAY, "paste": 365 * DAY,          # near-permanent records
    "compliance": 180 * DAY, "archive": 180 * DAY,
    "identity": 90 * DAY, "domain_registration": 90 * DAY, "corporate": 90 * DAY,
    "public_exposure": 60 * DAY,
    "social_account": 30 * DAY, "geolocation": 30 * DAY, "metadata": 30 * DAY,
    "intelligence": 30 * DAY,                          # derived — tracks its inputs
}


def resolve_ttl(category: str | None, scraper_ttl_override: int | None = None) -> int:
    """Per-scraper override wins; else category default; else DEFAULT_TTL."""
    if scraper_ttl_override is not None:
        return scraper_ttl_override
    return TTL_BY_CATEGORY.get(category or "", DEFAULT_TTL)
