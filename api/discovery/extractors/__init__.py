from .rel_me_extractor import RelMeExtractor
from .jsonld_extractor import JsonLdExtractor
from .social_link_extractor import SocialLinkExtractor
from .email_extractor import EmailExtractor
from .meta_tag_extractor import MetaTagExtractor
from .username_extractor import UsernameExtractor

# Ordered by reliability (highest first)
ALL_EXTRACTORS = [
    RelMeExtractor(),
    JsonLdExtractor(),
    SocialLinkExtractor(),
    EmailExtractor(),
    MetaTagExtractor(),
    UsernameExtractor(),
]


def extract_all(url: str, text: str, html: str, known_identifiers: set = None) -> list:
    """Run all extractors on a fetched page.

    Deduplicates results (same value -> keep highest confidence).
    Filters out known_identifiers if provided.
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

    return list(seen_values.values())
