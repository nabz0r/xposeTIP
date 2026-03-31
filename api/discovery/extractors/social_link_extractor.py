import re
from urllib.parse import urlparse, unquote

from .base import BaseExtractor, RawLead

PLATFORM_PATTERNS = {
    "github.com/": ("username", re.compile(r'github\.com/([a-zA-Z0-9_\-]+)(?:/|$)')),
    "twitter.com/": ("username", re.compile(r'twitter\.com/([a-zA-Z0-9_]+)(?:/|$)')),
    "x.com/": ("username", re.compile(r'x\.com/([a-zA-Z0-9_]+)(?:/|$)')),
    "linkedin.com/in/": ("username", re.compile(r'linkedin\.com/in/([a-zA-Z0-9_\-]+)')),
    "instagram.com/": ("username", re.compile(r'instagram\.com/([a-zA-Z0-9_.]+)(?:/|$)')),
    "mastodon.social/@": ("username", re.compile(r'mastodon\.social/@([a-zA-Z0-9_]+)')),
    "keybase.io/": ("username", re.compile(r'keybase\.io/([a-zA-Z0-9_]+)(?:/|$)')),
    "medium.com/@": ("username", re.compile(r'medium\.com/@([a-zA-Z0-9_]+)')),
    "dev.to/": ("username", re.compile(r'dev\.to/([a-zA-Z0-9_]+)(?:/|$)')),
    "reddit.com/user/": ("username", re.compile(r'reddit\.com/user/([a-zA-Z0-9_\-]+)')),
    "youtube.com/@": ("username", re.compile(r'youtube\.com/@([a-zA-Z0-9_]+)')),
    "twitch.tv/": ("username", re.compile(r'twitch\.tv/([a-zA-Z0-9_]+)(?:/|$)')),
    "gitlab.com/": ("username", re.compile(r'gitlab\.com/([a-zA-Z0-9_\-]+)(?:/|$)')),
    "bitbucket.org/": ("username", re.compile(r'bitbucket\.org/([a-zA-Z0-9_\-]+)(?:/|$)')),
    "stackoverflow.com/users/": ("url", None),
    "discord.gg/": ("url", None),
    "t.me/": ("username", re.compile(r't\.me/([a-zA-Z0-9_]+)(?:/|$)')),
}

_SKIP_PREFIXES = ("/", "#", "javascript:", "mailto:", "tel:")
_SKIP_USERNAMES = {"login", "signup", "about", "explore", "settings", "share", "intent"}


class SocialLinkExtractor(BaseExtractor):
    name = "social_link"
    reliability = 0.85

    def extract(self, url: str, text: str, html: str) -> list[RawLead]:
        leads = []
        seen = set()

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            return leads

        # Strip nav/footer/header/sidebar to focus on content area
        for tag in soup.find_all(["nav", "footer", "header", "aside"]):
            tag.decompose()
        for selector in ['[class*="nav"]', '[class*="footer"]', '[class*="sidebar"]',
                         '[class*="menu"]', '[class*="widget"]', '[class*="cookie"]',
                         '[id*="nav"]', '[id*="footer"]', '[id*="sidebar"]',
                         '[id*="menu"]', '[id*="widget"]']:
            for tag in soup.select(selector):
                tag.decompose()

        source_domain = urlparse(url).netloc.lower()

        for tag in soup.find_all("a", href=True):
            href = unquote(tag["href"].strip())

            if any(href.startswith(p) for p in _SKIP_PREFIXES):
                continue

            href_lower = href.lower()
            href_domain = urlparse(href).netloc.lower()
            if href_domain == source_domain:
                continue

            for pattern_prefix, (lead_type, regex) in PLATFORM_PATTERNS.items():
                if pattern_prefix not in href_lower:
                    continue

                if regex:
                    match = regex.search(href)
                    if match:
                        username = match.group(1)
                        if len(username) < 3:
                            continue
                        if username.lower() in _SKIP_USERNAMES:
                            continue
                        key = f"username:{username.lower()}"
                        if key in seen:
                            continue
                        seen.add(key)
                        leads.append(RawLead(
                            lead_type="username",
                            value=username,
                            extractor_type=self.name,
                            confidence=self.reliability,
                            context=href[:80],
                        ))
                else:
                    key = f"url:{href_lower[:100]}"
                    if key in seen:
                        continue
                    seen.add(key)
                    leads.append(RawLead(
                        lead_type="url",
                        value=href,
                        extractor_type=self.name,
                        confidence=self.reliability,
                        context=tag.get_text(strip=True)[:50] or href[:50],
                    ))
                break

        return leads
