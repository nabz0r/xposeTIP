"""Username validation — reject page titles, bios, emojis, full names."""

import re

_TITLE_PATTERNS = (
    "'s profile", "'s collection", "a new era",
    "instagram", "linktree", "bandcamp", "telegram",
    "| twitter", "| github", "| reddit", "| youtube",
    "| facebook", "| tiktok", "| medium",
    # S179: Threads scraper JSON-key bug (until S180-F fixes the source).
    # Explicit blacklist preferred over generic snake_case rule because
    # `connection_quality` is shape-indistinguishable from legit name
    # variants like `nabil_ksontini` produced by variant_generator.py.
    "connection_quality",
    # S192 Bug 9 Part A: form-label values scraped from "not found" /
    # auth pages where the scraper saw a 200 OK and extracted <title>
    # or a heading. Pre-existing rows are cleaned by S193 backfill.
    "sign up", "sign in", "log in", "log out", "register",
    "create account", "forgot password",
    "404 not found", "page not found", "user not found",
    "profile not found", "not available",
    "click here", "learn more", "get started",
)

# S179: FQDN-shaped values tagged type='username' by domain-oriented
# scrapers (dns_*, hackertarget_*, rdap_*, wayback_*, crtsh_*,
# disposable_email_check). Catches `gmail.com`, `lessentiel.lu`,
# `threatconnect.com`. Spares legitimate firstname.lastname handles
# (e.g. Steam `josephine.lespierre`, GitLab `kamel.amroune`) because
# `lespierre`/`amroune` are not in the TLD allow-list.
_DOMAIN_TLD_RE = re.compile(
    r'^[a-z0-9-]+\.(com|org|net|io|co|app|info|biz|me|tv|eu|us|ca|au|'
    r'lu|fr|de|uk|nl|be|ch|it|es|gov|edu|mil|ai|dev|xyz)$',
    re.IGNORECASE,
)


def is_valid_username(value: str) -> bool:
    """Return True if value looks like a real username, not a page title or junk."""
    if not value or len(value) > 40:
        return False
    # Reject anything with 3+ spaces (definitely a sentence/title, not a username)
    if value.count(' ') >= 3:
        return False
    # Reject regular dashes surrounded by spaces (e.g. "Telegram - a new era")
    if ' - ' in value or ' \u2013 ' in value or ' \u2014 ' in value:
        return False
    # Reject pipe (page titles like "seb57 | Instagram | Linktree")
    if "|" in value:
        return False
    # Reject en-dash / em-dash (page titles like "Telegram – a new era")
    if "\u2013" in value or "\u2014" in value:
        return False
    # Reject HTML entities
    if "&#" in value or "&amp;" in value:
        return False
    # Reject if no alphanumeric chars (only emojis/special chars)
    if not any(c.isalnum() for c in value):
        return False
    # Reject common page title patterns
    lower = value.lower()
    if any(p in lower for p in _TITLE_PATTERNS):
        return False
    # Reject full domain handles (2+ dots: "seb57.bsky.social")
    if value.count(".") >= 2:
        return False
    # S179: Reject FQDN single-dot with known TLD ("gmail.com").
    # Single-dot handles like "josephine.lespierre" are spared because
    # "lespierre" is not in the TLD allow-list.
    if _DOMAIN_TLD_RE.match(value):
        return False
    # S179: Reject paren-containing values (replit-style
    # "handle (Full Name)" page-title pattern). No major platform
    # allows parens in usernames.
    if "(" in value or ")" in value:
        return False
    return True
