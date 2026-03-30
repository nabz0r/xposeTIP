import json
import re

from .base import BaseExtractor, RawLead
from .social_link_extractor import PLATFORM_PATTERNS


class JsonLdExtractor(BaseExtractor):
    name = "jsonld"
    reliability = 0.95

    def extract(self, url: str, text: str, html: str) -> list[RawLead]:
        leads = []
        seen = set()

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            return leads

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue

            # Handle @graph arrays
            items = [data] if isinstance(data, dict) else data if isinstance(data, list) else []

            for item in items:
                if not isinstance(item, dict):
                    continue
                self._extract_from_item(item, leads, seen)

                # Check nested author
                author = item.get("author")
                if isinstance(author, dict):
                    self._extract_from_item(author, leads, seen)
                elif isinstance(author, list):
                    for a in author:
                        if isinstance(a, dict):
                            self._extract_from_item(a, leads, seen)

        return leads

    def _extract_from_item(self, item: dict, leads: list, seen: set):
        item_type = item.get("@type", "")

        # Name
        name = item.get("name") or item.get("givenName")
        if name and isinstance(name, str) and len(name) >= 3 and name.lower() not in seen:
            seen.add(name.lower())
            leads.append(RawLead(
                lead_type="name",
                value=name,
                extractor_type=self.name,
                confidence=self.reliability,
                context=f"JSON-LD @type={item_type}",
            ))

        # Email
        email = item.get("email")
        if email and isinstance(email, str) and "@" in email and email.lower() not in seen:
            seen.add(email.lower())
            leads.append(RawLead(
                lead_type="email",
                value=email.lower(),
                extractor_type=self.name,
                confidence=self.reliability,
                context=f"JSON-LD @type={item_type}",
            ))

        # sameAs — array of profile URLs
        same_as = item.get("sameAs", [])
        if isinstance(same_as, str):
            same_as = [same_as]
        if isinstance(same_as, list):
            for profile_url in same_as:
                if not isinstance(profile_url, str):
                    continue
                self._extract_profile_url(profile_url, leads, seen)

        # url field
        item_url = item.get("url")
        if item_url and isinstance(item_url, str) and "://" in item_url:
            self._extract_profile_url(item_url, leads, seen)

    def _extract_profile_url(self, profile_url: str, leads: list, seen: set):
        url_lower = profile_url.lower()
        for pattern_prefix, (lead_type, regex) in PLATFORM_PATTERNS.items():
            if pattern_prefix not in url_lower:
                continue
            if regex:
                match = regex.search(profile_url)
                if match:
                    username = match.group(1)
                    key = f"u:{username.lower()}"
                    if key not in seen:
                        seen.add(key)
                        leads.append(RawLead(
                            lead_type="username",
                            value=username,
                            extractor_type=self.name,
                            confidence=self.reliability,
                            context=f"JSON-LD sameAs → {profile_url[:60]}",
                        ))
            else:
                key = f"url:{url_lower[:100]}"
                if key not in seen:
                    seen.add(key)
                    leads.append(RawLead(
                        lead_type="url",
                        value=profile_url,
                        extractor_type=self.name,
                        confidence=self.reliability,
                        context="JSON-LD sameAs",
                    ))
            break
