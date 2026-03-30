import re

from .base import BaseExtractor, RawLead

_PATTERNS = [
    (re.compile(r'(?<!\w)@([a-zA-Z0-9_]{3,20})(?!\w)'), "mention"),
    (re.compile(r'/u/([a-zA-Z0-9_\-]{3,20})'), "reddit"),
    (re.compile(r'github\.com/([a-zA-Z0-9_\-]{3,30})'), "github"),
    (re.compile(r'(?:twitter|x)\.com/([a-zA-Z0-9_]{3,15})'), "twitter"),
    (re.compile(r'instagram\.com/([a-zA-Z0-9_.]{3,30})'), "instagram"),
    (re.compile(r't\.me/([a-zA-Z0-9_]{3,30})'), "telegram"),
    (re.compile(r'mastodon\.\w+/@([a-zA-Z0-9_]+)'), "mastodon"),
]

_SKIP = {
    "admin", "user", "login", "signup", "about", "help", "support",
    "contact", "null", "undefined", "none", "home", "index", "search",
    "settings", "profile", "status", "explore", "trending", "new",
}


class UsernameExtractor(BaseExtractor):
    name = "username_pattern"
    reliability = 0.6

    def extract(self, url: str, text: str, html: str) -> list[RawLead]:
        leads = []
        seen = set()

        for pattern, source in _PATTERNS:
            for match in pattern.finditer(text):
                username = match.group(1)
                if not username or username.lower() in _SKIP:
                    continue
                if username.isdigit():
                    continue
                key = username.lower()
                if key in seen:
                    continue
                seen.add(key)

                start = max(0, match.start() - 25)
                end = min(len(text), match.end() + 25)
                context = text[start:end].strip()

                leads.append(RawLead(
                    lead_type="username",
                    value=username,
                    extractor_type=self.name,
                    confidence=self.reliability,
                    context=context,
                ))

        return leads
