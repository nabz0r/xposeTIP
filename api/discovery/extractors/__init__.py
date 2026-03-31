from .rel_me_extractor import RelMeExtractor
from .jsonld_extractor import JsonLdExtractor
from .social_link_extractor import SocialLinkExtractor
from .email_extractor import EmailExtractor
from .meta_tag_extractor import MetaTagExtractor
from .username_extractor import UsernameExtractor
from .base import RawLead

# Ordered by reliability (highest first)
ALL_EXTRACTORS = [
    RelMeExtractor(),
    JsonLdExtractor(),
    SocialLinkExtractor(),
    EmailExtractor(),
    MetaTagExtractor(),
    UsernameExtractor(),
]

MIN_CONFIDENCE = 0.3

_COUNTRY_TLDS = {
    "US": {".com", ".edu", ".org", ".us", ".gov"},
    "PT": {".pt", ".com"}, "LU": {".lu", ".com", ".eu"},
    "DE": {".de", ".com"}, "FR": {".fr", ".com"},
    "GB": {".uk", ".co.uk", ".com"}, "CA": {".ca", ".com"},
    "NL": {".nl", ".com"}, "BE": {".be", ".com"},
    "CH": {".ch", ".com"}, "IT": {".it", ".com"},
    "ES": {".es", ".com"}, "SE": {".se", ".com"},
    "JP": {".jp", ".com"}, "AU": {".au", ".com"},
    "IN": {".in", ".com"}, "BR": {".br", ".com"},
}


def _geo_penalty(lead, target_geo: str) -> float:
    """Penalize email leads with TLDs from a different country."""
    if not target_geo or lead.lead_type != "email":
        return 1.0
    email_domain = lead.value.split("@")[-1] if "@" in lead.value else ""
    tld = "." + email_domain.split(".")[-1] if email_domain else ""
    if tld == ".com":
        return 1.0
    expected = _COUNTRY_TLDS.get(target_geo.upper(), {".com"})
    if tld in expected:
        return 1.0
    if len(tld) == 3 and tld != ".com":
        return 0.3
    if tld in {".edu", ".org", ".gov"}:
        return 0.6
    return 1.0


def score_relevance(lead: RawLead, known_identifiers: set, resolved_name: str = None) -> float:
    """Score how relevant a lead is to the target. Returns 0.0-1.0 multiplier."""
    value = lead.value.lower().strip()

    if value in known_identifiers:
        return 0.0

    for identifier in known_identifiers:
        ident = identifier.lower()
        if len(ident) < 3:
            continue
        if ident in value or value in ident:
            return 1.0
        if len(value) >= 3 and (value[:3] == ident[:3] or value[-3:] == ident[-3:]):
            return 0.9

    if resolved_name:
        name_parts = [p.lower() for p in resolved_name.split() if len(p) >= 3]
        for part in name_parts:
            if part in value or value in part:
                return 0.8

    return 0.3


def _apply_source_penalties(leads: list, source_url: str,
                            known_identifiers: set, resolved_name: str = None) -> list:
    """Penalize leads from noisy sources like LinkedIn related profiles."""
    if "linkedin.com" not in source_url.lower():
        return leads

    result = []
    for lead in leads:
        is_target_related = False
        value_lower = lead.value.lower()

        for ident in known_identifiers:
            if ident.lower() in value_lower or value_lower in ident.lower():
                is_target_related = True
                break

        if resolved_name and not is_target_related:
            for part in resolved_name.lower().split():
                if len(part) >= 3 and part in value_lower:
                    is_target_related = True
                    break

        if not is_target_related:
            lead.confidence *= 0.1

        result.append(lead)
    return result


def extract_all(url: str, text: str, html: str,
                known_identifiers: set = None,
                resolved_name: str = None,
                target_geo: str = None) -> list:
    """Run all extractors, apply relevance + geo scoring, deduplicate, filter."""
    known = {k.lower() for k in (known_identifiers or set())}
    seen_values = {}

    for extractor in ALL_EXTRACTORS:
        try:
            found = extractor.extract(url, text, html)
            for lead in found:
                key = lead.value.lower()
                if key in known:
                    continue
                existing = seen_values.get(key)
                if existing is None or lead.confidence > existing.confidence:
                    seen_values[key] = lead
        except Exception:
            continue

    deduped = list(seen_values.values())

    # Source-level penalties (LinkedIn noise)
    deduped = _apply_source_penalties(deduped, url, known, resolved_name)

    # Relevance scoring
    scored = []
    for lead in deduped:
        relevance = score_relevance(lead, known, resolved_name)
        if relevance == 0.0:
            continue
        lead.confidence = round(lead.confidence * relevance, 3)
        # Geo penalty for emails from wrong country
        lead.confidence = round(lead.confidence * _geo_penalty(lead, target_geo), 3)
        scored.append(lead)

    # Minimum confidence cutoff
    return [l for l in scored if l.confidence >= MIN_CONFIDENCE]
