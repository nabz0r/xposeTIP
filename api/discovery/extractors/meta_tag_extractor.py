from .base import BaseExtractor, RawLead


class MetaTagExtractor(BaseExtractor):
    name = "meta_tag"
    reliability = 0.8

    def extract(self, url: str, text: str, html: str) -> list[RawLead]:
        leads = []
        seen = set()

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            return leads

        # author meta tag
        for selector in [
            {"name": "author"},
            {"property": "og:author"},
            {"property": "article:author"},
        ]:
            tag = soup.find("meta", attrs=selector)
            if tag and tag.get("content"):
                val = tag["content"].strip()
                if not val or len(val) < 3:
                    continue
                key = val.lower()
                if key in seen:
                    continue
                seen.add(key)

                # If it looks like a URL, store as URL lead
                if val.startswith("http"):
                    leads.append(RawLead(
                        lead_type="url",
                        value=val,
                        extractor_type=self.name,
                        confidence=self.reliability,
                        context=f'meta {list(selector.values())[0]}',
                    ))
                else:
                    leads.append(RawLead(
                        lead_type="name",
                        value=val,
                        extractor_type=self.name,
                        confidence=self.reliability,
                        context=f'meta {list(selector.values())[0]}',
                    ))

        # twitter:creator
        tag = soup.find("meta", attrs={"name": "twitter:creator"})
        if tag and tag.get("content"):
            val = tag["content"].strip().lstrip("@")
            if val and len(val) >= 3 and val.lower() not in seen:
                seen.add(val.lower())
                leads.append(RawLead(
                    lead_type="username",
                    value=val,
                    extractor_type=self.name,
                    confidence=self.reliability,
                    context="meta twitter:creator",
                ))

        return leads
