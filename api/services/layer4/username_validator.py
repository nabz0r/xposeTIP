"""Username validation — reject page titles, bios, emojis, full names."""

_TITLE_PATTERNS = (
    "'s profile", "'s collection", "a new era",
    "instagram", "linktree", "bandcamp", "telegram",
    "| twitter", "| github", "| reddit", "| youtube",
    "| facebook", "| tiktok", "| medium",
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
    # Reject if 2+ words where both start with 3+ letter words → likely a name/sentence
    words = value.split()
    if len(words) >= 2 and all(len(w) >= 3 for w in words[:2]):
        return False
    # Reject common page title patterns
    lower = value.lower()
    if any(p in lower for p in _TITLE_PATTERNS):
        return False
    # Reject full domain handles (2+ dots: "seb57.bsky.social")
    if value.count(".") >= 2:
        return False
    return True
