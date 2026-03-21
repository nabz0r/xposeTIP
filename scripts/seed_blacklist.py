"""Seed the name_blacklist table with default entries."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from api.models.base import Base
from api.models.name_blacklist import NameBlacklist
from api.config import settings

DEFAULT_BLACKLIST = [
    # Exact matches — platforms and services
    {"pattern": "lastpass", "type": "exact", "reason": "Password manager"},
    {"pattern": "1password", "type": "exact", "reason": "Password manager"},
    {"pattern": "bitwarden", "type": "exact", "reason": "Password manager"},
    {"pattern": "dashlane", "type": "exact", "reason": "Password manager"},
    {"pattern": "nordpass", "type": "exact", "reason": "Password manager"},
    {"pattern": "office365", "type": "exact", "reason": "Microsoft service"},
    {"pattern": "office", "type": "exact", "reason": "Generic service name"},
    {"pattern": "outlook", "type": "exact", "reason": "Email service"},
    {"pattern": "protonmail", "type": "exact", "reason": "Email service"},
    {"pattern": "proton", "type": "exact", "reason": "Email service"},
    {"pattern": "tutanota", "type": "exact", "reason": "Email service"},
    {"pattern": "freelancer", "type": "exact", "reason": "Work platform"},
    {"pattern": "fiverr", "type": "exact", "reason": "Work platform"},
    {"pattern": "upwork", "type": "exact", "reason": "Work platform"},
    {"pattern": "imgur", "type": "exact", "reason": "Image platform"},
    {"pattern": "disqus", "type": "exact", "reason": "Comment platform"},
    {"pattern": "mastodon", "type": "exact", "reason": "Social platform"},
    {"pattern": "linktree", "type": "exact", "reason": "Link platform"},
    {"pattern": "aboutme", "type": "exact", "reason": "Profile platform"},
    {"pattern": "pinterest", "type": "exact", "reason": "Social platform"},
    {"pattern": "unknown", "type": "exact", "reason": "Generic"},
    {"pattern": "user", "type": "exact", "reason": "Generic"},
    {"pattern": "admin", "type": "exact", "reason": "Generic"},
    {"pattern": "test", "type": "exact", "reason": "Generic"},
    {"pattern": "null", "type": "exact", "reason": "Generic"},
    {"pattern": "none", "type": "exact", "reason": "Generic"},
    {"pattern": "default", "type": "exact", "reason": "Generic"},
    {"pattern": "anonymous", "type": "exact", "reason": "Generic"},
    {"pattern": "noreply", "type": "exact", "reason": "Generic"},
    {"pattern": "support", "type": "exact", "reason": "Generic"},
    # Contains patterns — catch phrases that appear inside names
    {"pattern": "not configured", "type": "contains", "reason": "Error message"},
    {"pattern": "api key", "type": "contains", "reason": "Error message"},
    {"pattern": "not found", "type": "contains", "reason": "Error message"},
    {"pattern": "profile found", "type": "contains", "reason": "Finding title"},
    {"pattern": "http://", "type": "contains", "reason": "URL fragment"},
    {"pattern": "https://", "type": "contains", "reason": "URL fragment"},
    {"pattern": ".com", "type": "contains", "reason": "Domain fragment"},
    {"pattern": ".org", "type": "contains", "reason": "Domain fragment"},
    {"pattern": "scraper", "type": "contains", "reason": "Technical term"},
    {"pattern": "scanner", "type": "contains", "reason": "Technical term"},
    # Regex patterns — complex rules
    {"pattern": "^Telegram:.*", "type": "regex", "reason": "Telegram og:title prefix"},
    {"pattern": "^Contact @.*", "type": "regex", "reason": "Telegram contact prefix"},
    {"pattern": "^\\d+$", "type": "regex", "reason": "Pure numbers"},
    {"pattern": "^.{1,2}$", "type": "regex", "reason": "Too short (1-2 chars)"},
    {"pattern": "^[a-z0-9_\\-\\.]+$", "type": "regex", "reason": "Looks like a username (all lowercase+digits)"},
    {"pattern": "^@", "type": "regex", "reason": "Username with @ prefix"},
    {"pattern": "^Telegram\\b", "type": "regex", "reason": "Telegram anything"},
    {"pattern": "^WhatsApp\\b", "type": "regex", "reason": "WhatsApp anything"},
    {"pattern": "^Signal\\b", "type": "regex", "reason": "Signal anything"},
    {"pattern": "^Discord\\b", "type": "regex", "reason": "Discord anything"},
    # Exact — browsers and platforms
    {"pattern": "eventbrite", "type": "exact", "reason": "Event platform"},
    {"pattern": "firefox", "type": "exact", "reason": "Browser"},
    {"pattern": "chrome", "type": "exact", "reason": "Browser"},
    {"pattern": "safari", "type": "exact", "reason": "Browser"},
    {"pattern": "opera", "type": "exact", "reason": "Browser"},
    {"pattern": "no-reply", "type": "exact", "reason": "No-reply address"},
    {"pattern": "postmaster", "type": "exact", "reason": "System address"},
    {"pattern": "webmaster", "type": "exact", "reason": "System address"},
    {"pattern": "mailer-daemon", "type": "exact", "reason": "System address"},
    {"pattern": "info", "type": "exact", "reason": "Generic address"},
    {"pattern": "contact", "type": "exact", "reason": "Generic address"},
    {"pattern": "hello", "type": "exact", "reason": "Generic address"},
    # Contains — messaging slogans
    {"pattern": "a new era of messaging", "type": "contains", "reason": "Telegram slogan"},
    {"pattern": "fast. secure. powerful", "type": "contains", "reason": "Telegram slogan"},
    {"pattern": "\u2013 a new era", "type": "contains", "reason": "Telegram title variant"},
]


def seed_blacklist():
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    with Session(engine) as session:
        created = 0
        skipped = 0
        for entry in DEFAULT_BLACKLIST:
            existing = session.execute(
                select(NameBlacklist).where(NameBlacklist.pattern == entry["pattern"])
            ).scalar_one_or_none()
            if existing:
                skipped += 1
                continue
            session.add(NameBlacklist(
                pattern=entry["pattern"],
                type=entry["type"],
                reason=entry["reason"],
            ))
            created += 1
        session.commit()
        print(f"Name blacklist seeded: {created} created, {skipped} skipped (already exist)")


if __name__ == "__main__":
    seed_blacklist()
