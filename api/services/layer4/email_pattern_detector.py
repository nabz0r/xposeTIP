"""Corporate email pattern detection.

Analyzes targets sharing the same email domain to detect naming patterns:
  {f}{last}       → stheis, ewray, lpopa
  {first}.{last}  → benjamin.lavault, nicolas.huynen
  {first}_{last}  → mickael_tabart
  {f}.{last}      → n.huynen

Once a pattern is confirmed (50%+ match on 3+ known names), it's used to
decompose unknown email prefixes into (first_initial, surname) or
(first_name, surname).
"""
import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Free/personal providers — never have corporate naming patterns
FREE_PROVIDERS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "msn.com", "yahoo.com", "yahoo.fr", "yahoo.co.uk", "aol.com",
    "protonmail.com", "proton.me", "tutanota.com", "zoho.com",
    "icloud.com", "me.com", "mac.com", "mail.com", "gmx.com", "gmx.de",
    "yandex.com", "yandex.ru", "mail.ru", "inbox.com", "fastmail.com",
    "pm.me", "hey.com", "cock.li", "riseup.net", "disroot.org",
}


def _test_f_last(name, prefix):
    parts = name.split()
    if len(parts) < 2:
        return False
    return prefix.lower() == parts[0][0].lower() + parts[-1].lower().replace(" ", "")


def _test_first_dot_last(name, prefix):
    parts = name.split()
    if len(parts) < 2 or "." not in prefix:
        return False
    return prefix.lower() == parts[0].lower() + "." + parts[-1].lower()


def _test_first_under_last(name, prefix):
    parts = name.split()
    if len(parts) < 2 or "_" not in prefix:
        return False
    return prefix.lower() == parts[0].lower() + "_" + parts[-1].lower()


def _test_f_dot_last(name, prefix):
    parts = name.split()
    if len(parts) < 2:
        return False
    return prefix.lower() == parts[0][0].lower() + "." + parts[-1].lower()


def _extract_f_last(prefix, m):
    return {"first_initial": m.group(1), "surname": m.group(2)}


def _extract_two_part(prefix, m):
    return {"first_name": m.group(1), "surname": m.group(2)}


def _extract_f_dot_last(prefix, m):
    return {"first_initial": m.group(1), "surname": m.group(2)}


# Known pattern templates
PATTERNS = {
    "f_last": {
        "regex": r"^([a-z])([a-z]+)$",
        "description": "{first_initial}{lastname}",
        "extract": _extract_f_last,
        "test": _test_f_last,
    },
    "first_dot_last": {
        "regex": r"^([a-z]+)\.([a-z]+)$",
        "description": "{firstname}.{lastname}",
        "extract": _extract_two_part,
        "test": _test_first_dot_last,
    },
    "first_under_last": {
        "regex": r"^([a-z]+)_([a-z]+)$",
        "description": "{firstname}_{lastname}",
        "extract": _extract_two_part,
        "test": _test_first_under_last,
    },
    "f_dot_last": {
        "regex": r"^([a-z])\.([a-z]+)$",
        "description": "{f}.{lastname}",
        "extract": _extract_f_dot_last,
        "test": _test_f_dot_last,
    },
}


def detect_domain_pattern(domain: str, session: Session) -> dict | None:
    """Detect the email naming pattern for a corporate domain.

    Returns: {
        "domain": "threatconnect.com",
        "pattern": "f_last",
        "description": "{first_initial}{lastname}",
        "confidence": 0.84,
        "sample_size": 19,
        "matches": 16,
    } or None
    """
    if domain.lower() in FREE_PROVIDERS:
        return None

    from api.models.target import Target

    targets = session.execute(
        select(Target).where(
            Target.email.ilike(f"%@{domain}")
        )
    ).scalars().all()

    if len(targets) < 3:
        return None

    # Collect (prefix, confirmed_name) pairs
    pairs = []
    for t in targets:
        profile = t.profile_data or {}
        name = profile.get("primary_name")
        if name and " " in name and len(name) > 3:
            prefix = t.email.split("@")[0].lower()
            clean_name = re.sub(r'[\U0001F000-\U0001FFFF\u200D\uFE0F]', '', name).strip()
            if len(clean_name) > 3 and " " in clean_name:
                pairs.append((prefix, clean_name))

    if len(pairs) < 3:
        return None

    # Test each pattern
    best_pattern = None
    best_score = 0.0
    best_matches = 0

    for pattern_name, pattern_def in PATTERNS.items():
        matches = 0
        for prefix, name in pairs:
            try:
                if pattern_def["test"](name, prefix):
                    matches += 1
            except Exception:
                continue

        match_rate = matches / len(pairs) if pairs else 0

        if matches >= 3 and (match_rate > best_score or
                             (match_rate == best_score and matches > best_matches)):
            best_score = match_rate
            best_matches = matches
            best_pattern = pattern_name

    if best_pattern and best_score >= 0.50:
        logger.info(
            "EMAIL_PATTERN: Detected '%s' for %s (%.0f%% match, %d/%d)",
            best_pattern, domain, best_score * 100, best_matches, len(pairs),
        )
        return {
            "domain": domain,
            "pattern": best_pattern,
            "description": PATTERNS[best_pattern]["description"],
            "confidence": round(min(0.95, best_score), 2),
            "sample_size": len(pairs),
            "matches": best_matches,
        }

    return None


def decompose_email(email: str, pattern_info: dict) -> dict | None:
    """Decompose an email prefix using a detected pattern.

    Returns: {
        "surname": "theis",
        "first_initial": "s",     # for {f}{last} patterns
        "first_name": "benjamin", # for {first}.{last} patterns
        "confidence": 0.85,
    } or None
    """
    if not pattern_info:
        return None

    prefix = email.split("@")[0].lower()
    pattern_name = pattern_info["pattern"]
    pattern_def = PATTERNS.get(pattern_name)

    if not pattern_def:
        return None

    m = re.match(pattern_def["regex"], prefix)
    if not m:
        return None

    try:
        result = pattern_def["extract"](prefix, m)
        result["confidence"] = pattern_info["confidence"]
        result["pattern"] = pattern_name
        return result
    except Exception:
        return None


def boost_names_with_pattern(names: list, email_decomp: dict) -> list:
    """Apply email pattern boost to name candidates.

    Rules:
    - Surname matches email-derived surname → +0.20
    - First char matches email-derived first_initial → +0.10
    - Full first name matches (for {first}.{last} patterns) → +0.15
    - Multi-word surname normalization ("De La Cruz" → "delacruz")

    Returns the same names list with updated composite_scores.
    """
    if not email_decomp:
        return names

    derived_surname = email_decomp.get("surname", "").lower()
    derived_first = email_decomp.get("first_initial", "").lower()
    derived_firstname = email_decomp.get("first_name", "").lower()
    conf = email_decomp.get("confidence", 0.7)

    for n in names:
        name_val = n.get("value", "").strip()
        parts = name_val.split()
        if len(parts) < 2:
            continue

        name_surname = parts[-1].lower()
        # Normalize multi-word surnames: "De La Cruz" → "delacruz"
        name_surname_normalized = re.sub(r'[\s-]+', '', ' '.join(parts[1:])).lower()
        name_first_char = parts[0][0].lower() if parts[0] else ""
        name_firstname = parts[0].lower()

        bonus = 0.0
        match_reasons = []

        # Surname match — high value (try exact then normalized)
        if derived_surname:
            if name_surname == derived_surname or name_surname_normalized == derived_surname:
                bonus += 0.20 * conf
                match_reasons.append("surname")

        # First initial match
        if derived_first and name_first_char == derived_first:
            bonus += 0.10 * conf
            match_reasons.append("first_initial")

        # Full first name match (for {first}.{last} patterns)
        if derived_firstname and name_firstname == derived_firstname:
            bonus += 0.15 * conf
            match_reasons.append("first_name")

        if bonus > 0:
            n["composite_score"] = n.get("composite_score", 0) + bonus
            n["email_pattern_match"] = True
            n["email_pattern_reasons"] = match_reasons
            logger.debug(
                "EMAIL_PATTERN_BOOST: '%s' +%.3f (%s)",
                name_val, bonus, ", ".join(match_reasons),
            )

    return names
