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


def score_relevance(lead: RawLead, known_identifiers: set, resolved_name: str = None) -> float:
    """Score how relevant a lead is to the target. Returns 0.0-1.0 multiplier."""
    value = lead.value.lower().strip()

    # Already known → filter completely
    if value in known_identifiers:
        return 0.0

    # Substring overlap with any known identifier
    for identifier in known_identifiers:
        ident = identifier.lower()
        if len(ident) < 3:
            continue
        if ident in value or value in ident:
            return 1.0
        # Partial: first 3+ chars match
        if len(value) >= 3 and (value[:3] == ident[:3] or value[-3:] == ident[-3:]):
            return 0.9

    # Check resolved name parts
    if resolved_name:
        name_parts = [p.lower() for p in resolved_name.split() if len(p) >= 3]
        for part in name_parts:
            if part in value or value in part:
                return 0.8

    # No relationship — likely noise
    return 0.3


def extract_all(url: str, text: str, html: str,
                known_identifiers: set = None,
                resolved_name: str = None) -> list:
    """Run all extractors, apply relevance scoring, deduplicate.

    Leads with relevance 0.0 are filtered (already known).
    Leads with relevance < 1.0 get confidence penalized.
    """
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

    # Apply relevance scoring
    scored = []
    for lead in seen_values.values():
        relevance = score_relevance(lead, known, resolved_name)
        if relevance == 0.0:
            continue
        lead.confidence = round(lead.confidence * relevance, 3)
        scored.append(lead)

    return scored
