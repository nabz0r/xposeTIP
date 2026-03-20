"""Username Permutations scanner — generate username variants and check platforms."""
import logging
import re

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)

# Platforms with predictable profile URL patterns (no auth needed)
PLATFORM_CHECKS = [
    {"name": "Reddit", "url": "https://www.reddit.com/user/{}/about.json", "check": "json", "json_key": "data"},
    {"name": "Steam", "url": "https://steamcommunity.com/id/{}", "check": "status"},
    {"name": "Keybase", "url": "https://keybase.io/_/api/1.0/user/lookup.json?usernames={}", "check": "json", "json_key": "them"},
    {"name": "GitLab", "url": "https://gitlab.com/api/v4/users?username={}", "check": "json_array"},
    {"name": "HackerNews", "url": "https://hacker-news.firebaseio.com/v0/user/{}.json", "check": "json", "json_key": "id"},
    {"name": "Dev.to", "url": "https://dev.to/api/users/by_username?url={}", "check": "json", "json_key": "id"},
    {"name": "Medium", "url": "https://medium.com/@{}?format=json", "check": "status"},
]


def generate_usernames(email: str) -> list[str]:
    """Generate username permutations from email local part."""
    local = email.split("@")[0].lower()
    usernames = set()

    # Base username
    usernames.add(local)

    # Remove common separators
    clean = re.sub(r'[._\-+]', '', local)
    if clean != local:
        usernames.add(clean)

    # Split on separators
    parts = re.split(r'[._\-+]', local)
    if len(parts) >= 2:
        usernames.add(parts[0])
        usernames.add("".join(parts))
        usernames.add("_".join(parts))
        usernames.add(".".join(parts))
        # FirstLast / LastFirst
        if len(parts) == 2:
            usernames.add(f"{parts[1]}{parts[0]}")
            usernames.add(f"{parts[0][0]}{parts[1]}")  # jdoe
            usernames.add(f"{parts[0]}{parts[1][0]}")  # johnd

    # Remove numbers-only and too short
    usernames = {u for u in usernames if len(u) >= 3 and not u.isdigit()}

    # Strip trailing numbers for a clean variant
    no_nums = re.sub(r'\d+$', '', local)
    if no_nums and len(no_nums) >= 3 and no_nums != local:
        usernames.add(no_nums)

    return list(usernames)[:8]  # Cap at 8 to respect rate limits


class UsernameScannerPlugin(BaseScanner):
    MODULE_ID = "username_hunter"
    LAYER = 1
    CATEGORY = "social_account"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        usernames = generate_usernames(email)
        if not usernames:
            return []

        results = []

        # Username permutations finding
        results.append(ScanResult(
            module=self.MODULE_ID,
            layer=self.LAYER,
            category="metadata",
            severity="info",
            title=f"Username permutations: {len(usernames)} generated",
            description=f"Generated from {email}: {', '.join(usernames)}",
            data={"usernames": usernames, "email": email, "source": "username_hunter"},
            indicator_value=email,
            indicator_type="email",
            verified=True,
        ))

        async with httpx.AsyncClient(
            timeout=10,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; xpose-tip/1.0)"},
        ) as client:
            for username in usernames:
                for platform in PLATFORM_CHECKS:
                    url = platform["url"].format(username)
                    try:
                        resp = await client.get(url)

                        found = False
                        profile_data = {}

                        if platform["check"] == "status":
                            found = resp.status_code == 200
                        elif platform["check"] == "json":
                            if resp.status_code == 200:
                                data = resp.json()
                                if isinstance(data, dict) and data.get(platform.get("json_key", "")):
                                    found = True
                                    profile_data = data
                        elif platform["check"] == "json_array":
                            if resp.status_code == 200:
                                data = resp.json()
                                if isinstance(data, list) and len(data) > 0:
                                    found = True
                                    profile_data = data[0] if data else {}

                        if found:
                            # Build profile URL for display
                            display_url = url
                            if platform["name"] == "Reddit":
                                display_url = f"https://www.reddit.com/user/{username}"
                            elif platform["name"] == "Keybase":
                                display_url = f"https://keybase.io/{username}"
                            elif platform["name"] == "GitLab":
                                display_url = f"https://gitlab.com/{username}"
                            elif platform["name"] == "HackerNews":
                                display_url = f"https://news.ycombinator.com/user?id={username}"
                            elif platform["name"] == "Dev.to":
                                display_url = f"https://dev.to/{username}"
                            elif platform["name"] == "Medium":
                                display_url = f"https://medium.com/@{username}"

                            results.append(ScanResult(
                                module=self.MODULE_ID,
                                layer=self.LAYER,
                                category="social_account",
                                severity="low",
                                title=f"Username '{username}' found on {platform['name']}",
                                description=(
                                    f"Username '{username}' (derived from {email}) exists on {platform['name']}"
                                ),
                                data={
                                    "username": username,
                                    "platform": platform["name"],
                                    "url": display_url,
                                    "profile_data": {k: v for k, v in profile_data.items() if k in (
                                        "name", "title", "bio", "description", "karma", "created",
                                        "username", "display_name", "avatar_url",
                                    )} if isinstance(profile_data, dict) else {},
                                    "source": "username_hunter",
                                },
                                url=display_url,
                                indicator_value=display_url,
                                indicator_type="social_url",
                                verified=False,  # Username match, not email verified
                            ))

                    except Exception:
                        logger.debug("Username check failed: %s on %s", username, platform["name"])
                        continue

        logger.info("Username Hunter scan for %s: %d findings, %d usernames checked", email, len(results), len(usernames))
        return results

    async def health_check(self, **kwargs) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get("https://www.reddit.com/user/spez/about.json",
                                        headers={"User-Agent": "xpose-tip"})
                return resp.status_code == 200
        except Exception:
            return False
