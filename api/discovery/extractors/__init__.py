import re

from .rel_me_extractor import RelMeExtractor
from .jsonld_extractor import JsonLdExtractor
from .social_link_extractor import SocialLinkExtractor
from .email_extractor import EmailExtractor
from .meta_tag_extractor import MetaTagExtractor
from .username_extractor import UsernameExtractor
from .person_extractor import PersonExtractor
from .base import RawLead

# Ordered by reliability (highest first)
ALL_EXTRACTORS = [
    RelMeExtractor(),
    JsonLdExtractor(),
    SocialLinkExtractor(),
    EmailExtractor(),
    MetaTagExtractor(),
    PersonExtractor(),
    UsernameExtractor(),
]

MIN_CONFIDENCE = 0.3

# Free-mail / generic domains carry no employer signal → no company anchor (AR-0).
_GENERIC_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "protonmail.com",
    "icloud.com", "live.com", "aol.com", "mail.com", "ymail.com", "gmx.com",
    "zoho.com", "fastmail.com", "tutanota.com", "hey.com", "pm.me", "posteo.de",
    "free.fr", "orange.fr", "wanadoo.fr", "sfr.fr", "laposte.net",
    "web.de", "t-online.de", "yahoo.fr", "hotmail.fr",
}


def _norm_company(s: str) -> str:
    """Lowercase + strip non-alphanumeric. 'Pluton Technologies' →
    'plutontechnologies' (== email domain label). 'Genii' → 'genii' (no match)."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# A WELL-FORMED email — guards against collision junk that contains "@" but is not
# an email (e.g. "telegram: contact @eric", "eric@s twitter") poisoning the token.
_EMAIL_RE = re.compile(r"^[^@\s]+@[a-z0-9.-]+\.[a-z]{2,}$", re.I)


def _company_token_from_identifiers(known: set) -> str | None:
    """Corporate anchor token from the seed email's domain label. None for
    free-mail / no corporate email → AR-0 corporate_person leads do not fire.

    Only WELL-FORMED emails count — known_identifiers is polluted with collision
    handles like 'telegram: contact @eric', and picking the first '@'-containing
    string yielded token 'eric' instead of 'plutontechnologies' (the co-occurrence
    then failed and Eric Lox was dropped). Sorted for determinism across the set."""
    for ident in sorted(known or ()):
        if not _EMAIL_RE.match(ident.strip()):
            continue
        domain = ident.split("@", 1)[1].strip().lower()
        if domain and domain not in _GENERIC_EMAIL_DOMAINS:
            return _norm_company(domain.split(".")[0])
    return None


def _company_matches(caption_company: str, token: str) -> bool:
    """Co-occurrence: caption company == target token (normalized), or contains it
    (len-guarded). Keeps Eric Lox (Pluton) in, keeps Eric Lux (Genii) out."""
    c = _norm_company(caption_company)
    if not c or not token:
        return False
    if c == token:
        return True
    return len(token) >= 5 and (token in c or c in token)

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


def _company_token_from_email(seed_email: str) -> str | None:
    """Company anchor token from the SEED email's domain label. None for free-mail.
    S264-0g — must be the SEED email, not any email in known_identifiers: that set
    is polluted with discovered alt-emails (blog@feedspot.com) that sort ahead of
    the seed and yielded token 'feedspot' instead of 'plutontechnologies'."""
    e = (seed_email or "").strip().lower()
    if not _EMAIL_RE.match(e):
        return None
    domain = e.split("@", 1)[1]
    if domain in _GENERIC_EMAIL_DOMAINS:
        return None
    return _norm_company(domain.split(".")[0])


def extract_all(url: str, text: str, html: str,
                known_identifiers: set = None,
                resolved_name: str = None,
                target_geo: str = None,
                seed_email: str = None) -> list:
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

    # S264-0 — corporate_person leads anchor on company CO-OCCURRENCE, not on
    # known-identifier/name overlap (the whole point is the name is NEW). Keep only
    # those whose caption company matches the seed email's company token; their
    # relevance IS that match, so they bypass score_relevance. No corporate email
    # (free-mail / none) → token is None → all corporate_person dropped (AR-0 off).
    # Prefer the explicit SEED email (the employer anchor); fall back to scanning
    # known_identifiers only when the caller didn't pass it.
    company_token = _company_token_from_email(seed_email) if seed_email else _company_token_from_identifiers(known)
    person_leads = []
    other_leads = []
    for lead in deduped:
        if lead.lead_type == "corporate_person":
            if company_token and _company_matches(lead.context, company_token):
                person_leads.append(lead)
            # else: dropped (wrong company → e.g. Eric Lux / Genii — or no anchor)
        else:
            other_leads.append(lead)

    # Relevance scoring (non-person leads)
    scored = []
    for lead in other_leads:
        relevance = score_relevance(lead, known, resolved_name)
        if relevance == 0.0:
            continue
        lead.confidence = round(lead.confidence * relevance, 3)
        # Geo penalty for emails from wrong country
        lead.confidence = round(lead.confidence * _geo_penalty(lead, target_geo), 3)
        scored.append(lead)

    scored.extend(person_leads)  # already company-anchored at extractor confidence

    # Minimum confidence cutoff
    return [l for l in scored if l.confidence >= MIN_CONFIDENCE]
