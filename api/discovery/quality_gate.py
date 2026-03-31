"""Quality gate for Discovery Engine.

Filters discovery leads against existing target data to prevent
re-discovering what Phase A/B already found.
"""
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Platform URL patterns → (domain_key, username_regex)
_PLATFORM_URL_PATTERNS = [
    ("github.com", re.compile(r'github\.com/([a-zA-Z0-9_\-]+)(?:/|$)')),
    ("twitter.com", re.compile(r'(?:twitter|x)\.com/([a-zA-Z0-9_]+)(?:/|$)')),
    ("linkedin.com", re.compile(r'linkedin\.com/in/([a-zA-Z0-9_\-]+)')),
    ("instagram.com", re.compile(r'instagram\.com/([a-zA-Z0-9_.]+)(?:/|$)')),
    ("reddit.com", re.compile(r'reddit\.com/(?:user|u)/([a-zA-Z0-9_\-]+)')),
    ("steam", re.compile(r'steamcommunity\.com/id/([a-zA-Z0-9_\-]+)')),
    ("gitlab.com", re.compile(r'gitlab\.com/([a-zA-Z0-9_\-]+)(?:/|$)')),
    ("medium.com", re.compile(r'medium\.com/@([a-zA-Z0-9_]+)')),
    ("dev.to", re.compile(r'dev\.to/([a-zA-Z0-9_]+)(?:/|$)')),
    ("keybase.io", re.compile(r'keybase\.io/([a-zA-Z0-9_]+)(?:/|$)')),
    ("twitch.tv", re.compile(r'twitch\.tv/([a-zA-Z0-9_]+)(?:/|$)')),
    ("youtube.com", re.compile(r'youtube\.com/@([a-zA-Z0-9_]+)')),
    ("t.me", re.compile(r't\.me/([a-zA-Z0-9_]+)(?:/|$)')),
    ("mastodon.social", re.compile(r'mastodon\.social/@([a-zA-Z0-9_]+)')),
    ("bitbucket.org", re.compile(r'bitbucket\.org/([a-zA-Z0-9_\-]+)(?:/|$)')),
]


class QualityGate:
    """Filter discovery leads against existing target data."""

    def __init__(self, target_id: str = None, db_session=None):
        self.target_id = target_id
        self.known_identifiers = set()   # lowercase emails, usernames
        self.known_platforms = {}         # platform_domain → set of usernames

        if db_session and target_id:
            self._load_existing(db_session)

    def load_from_profile(self, profile: dict):
        """Load known identifiers from a profile snapshot (for dry-run without DB)."""
        for ident in profile.get("identifiers", []):
            val = ident.get("value", "").lower().strip()
            if val:
                self.known_identifiers.add(val)

        for platform in profile.get("platforms_found", []):
            self.known_platforms.setdefault(platform.lower(), set())

        name = profile.get("resolved_name", "")
        if name:
            self.known_identifiers.add(name.lower())

    def _load_existing(self, db):
        """Load from existing target data in DB."""
        import uuid
        from sqlalchemy import select
        from api.models.target import Target
        from api.models.finding import Finding

        tid = uuid.UUID(str(self.target_id)) if isinstance(self.target_id, str) else self.target_id

        # Target email
        target = db.execute(select(Target).where(Target.id == tid)).scalar_one_or_none()
        if target:
            if target.email:
                self.known_identifiers.add(target.email.lower())
            if target.display_name:
                self.known_identifiers.add(target.display_name.lower())

        # Findings: extract usernames, emails, URLs
        findings = db.execute(
            select(Finding).where(Finding.target_id == tid)
        ).scalars().all()

        for f in findings:
            # Indicator values
            if f.indicator_value:
                self.known_identifiers.add(f.indicator_value.lower().strip())

            # URLs
            if f.url:
                pu = self._extract_platform_username(f.url)
                if pu:
                    platform, username = pu
                    self.known_platforms.setdefault(platform, set()).add(username.lower())

            # Data fields
            data = f.data if isinstance(f.data, dict) else {}
            for key in ("username", "display_name", "email", "login"):
                val = data.get(key) or (data.get("extracted") or {}).get(key)
                if val and isinstance(val, str):
                    self.known_identifiers.add(val.lower().strip())

            platform = data.get("platform", "")
            username = data.get("username") or data.get("extracted", {}).get("username", "")
            if platform and username:
                self.known_platforms.setdefault(platform.lower(), set()).add(username.lower())

        logger.info("QualityGate: loaded %d identifiers, %d platforms for target %s",
                     len(self.known_identifiers), len(self.known_platforms), self.target_id)

    def filter(self, leads: list) -> list:
        """Filter out leads that are already known. Returns only new leads."""
        result = []
        for lead in leads:
            if self._is_known(lead):
                continue
            result.append(lead)
        return result

    def _is_known(self, lead) -> bool:
        """Check if a lead matches existing data."""
        val = lead.value.lower().strip()

        # 1. Exact identifier match
        if val in self.known_identifiers:
            return True

        # 2. URL → platform+username check
        if lead.lead_type == "url":
            pu = self._extract_platform_username(lead.value)
            if pu:
                platform, username = pu
                known_users = self.known_platforms.get(platform, set())
                if username.lower() in known_users:
                    return True
                # Sub-page of known profile
                for known_user in known_users:
                    if known_user in val:
                        return True

        # 3. Username → check across platforms
        if lead.lead_type == "username":
            for platform, users in self.known_platforms.items():
                if val in users:
                    return True

        return False

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Strip protocol, www, trailing slash, lowercase."""
        u = url.lower().strip()
        u = u.replace("https://", "").replace("http://", "")
        u = u.replace("www.", "")
        return u.rstrip("/")

    @staticmethod
    def _extract_platform_username(url: str) -> tuple | None:
        """Extract (platform_domain, username) from a URL."""
        if not url:
            return None
        url_lower = url.lower()
        for platform, regex in _PLATFORM_URL_PATTERNS:
            if platform in url_lower:
                match = regex.search(url)
                if match:
                    return (platform, match.group(1))
        return None
