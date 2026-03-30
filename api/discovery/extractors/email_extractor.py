import re

from .base import BaseExtractor, RawLead

_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

_EXCLUDE_DOMAINS = {
    "example.com", "email.com", "domain.com", "test.com", "localhost",
    "sentry.io", "users.noreply.github.com", "wixpress.com", "wordpress.com",
    "w3.org", "schema.org", "xmlns.com", "purl.org", "creativecommons.org",
    "ogp.me", "placeholder.com", "yourcompany.com", "company.com",
}

_HASH_RE = re.compile(r'^[a-f0-9]{32}@')


class EmailExtractor(BaseExtractor):
    name = "email_regex"
    reliability = 0.9

    def extract(self, url: str, text: str, html: str) -> list[RawLead]:
        leads = []
        seen = set()

        for match in _EMAIL_RE.finditer(text):
            email = match.group().lower().strip().rstrip(".")
            domain = email.split("@")[1] if "@" in email else ""

            if domain in _EXCLUDE_DOMAINS:
                continue
            if _HASH_RE.match(email):
                continue
            if email in seen:
                continue
            seen.add(email)

            start = max(0, match.start() - 25)
            end = min(len(text), match.end() + 25)
            context = text[start:end].strip()

            leads.append(RawLead(
                lead_type="email",
                value=email,
                extractor_type=self.name,
                confidence=self.reliability,
                context=context,
            ))

        return leads
