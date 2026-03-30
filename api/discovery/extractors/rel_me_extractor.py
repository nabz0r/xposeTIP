from .base import BaseExtractor, RawLead
from .social_link_extractor import PLATFORM_PATTERNS


class RelMeExtractor(BaseExtractor):
    name = "rel_me"
    reliability = 0.95

    def extract(self, url: str, text: str, html: str) -> list[RawLead]:
        leads = []
        seen = set()

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            return leads

        for tag in soup.find_all("a", rel=True):
            rel = tag.get("rel", [])
            if isinstance(rel, str):
                rel = rel.split()
            if "me" not in rel:
                continue

            href = (tag.get("href") or "").strip()
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            href_lower = href.lower()

            # Try to extract a username via platform patterns
            username_found = False
            for pattern_prefix, (lead_type, regex) in PLATFORM_PATTERNS.items():
                if pattern_prefix not in href_lower:
                    continue
                if regex:
                    match = regex.search(href)
                    if match:
                        username = match.group(1)
                        key = username.lower()
                        if key not in seen:
                            seen.add(key)
                            leads.append(RawLead(
                                lead_type="username",
                                value=username,
                                extractor_type=self.name,
                                confidence=self.reliability,
                                context=f'rel=me → {href[:60]}',
                            ))
                        username_found = True
                break

            if not username_found:
                key = href_lower[:100]
                if key not in seen:
                    seen.add(key)
                    leads.append(RawLead(
                        lead_type="url",
                        value=href,
                        extractor_type=self.name,
                        confidence=self.reliability,
                        context=f'rel=me → {tag.get_text(strip=True)[:40]}',
                    ))

        return leads
