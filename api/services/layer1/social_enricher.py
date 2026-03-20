import logging

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class SocialEnricherScanner(BaseScanner):
    MODULE_ID = "social_enricher"
    LAYER = 1
    CATEGORY = "social_account"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        results = []

        # GitHub enrichment — public API, no auth
        try:
            github_results = await self._enrich_github(email)
            results.extend(github_results)
        except Exception:
            logger.debug("GitHub enrichment failed for %s", email)

        return results

    async def _enrich_github(self, email: str) -> list[ScanResult]:
        results = []
        async with httpx.AsyncClient(timeout=10, headers={"Accept": "application/vnd.github.v3+json"}) as client:
            # Search by email
            resp = await client.get(
                "https://api.github.com/search/users",
                params={"q": f"{email} in:email"},
            )
            if resp.status_code != 200:
                return []

            data = resp.json()
            if data.get("total_count", 0) == 0:
                return []

            for item in data.get("items", [])[:3]:
                username = item.get("login", "")
                if not username:
                    continue

                # Get full profile
                user_resp = await client.get(f"https://api.github.com/users/{username}")
                if user_resp.status_code != 200:
                    continue

                profile = user_resp.json()
                name = profile.get("name", "")
                bio = profile.get("bio", "")
                location = profile.get("location", "")
                company = profile.get("company", "")
                avatar = profile.get("avatar_url", "")
                repos = profile.get("public_repos", 0)
                followers = profile.get("followers", 0)
                blog = profile.get("blog", "")

                profile_data = {
                    "username": username,
                    "name": name,
                    "bio": bio,
                    "location": location,
                    "company": company,
                    "avatar_url": avatar,
                    "public_repos": repos,
                    "followers": followers,
                    "following": profile.get("following", 0),
                    "blog": blog,
                    "created_at": profile.get("created_at", ""),
                    "source": "github_api",
                }

                desc_parts = []
                if name:
                    desc_parts.append(f"Name: {name}")
                if bio:
                    desc_parts.append(f"Bio: {bio[:150]}")
                if location:
                    desc_parts.append(f"Location: {location}")
                if company:
                    desc_parts.append(f"Company: {company}")
                desc_parts.append(f"{repos} repos, {followers} followers")

                results.append(ScanResult(
                    module=self.MODULE_ID,
                    layer=self.LAYER,
                    category="social_account",
                    severity="medium",
                    title=f"GitHub profile: {name or username}",
                    description=". ".join(desc_parts),
                    data=profile_data,
                    url=f"https://github.com/{username}",
                    indicator_value=f"https://github.com/{username}",
                    indicator_type="social_url",
                    verified=True,
                ))

        return results

    async def health_check(self, **kwargs) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get("https://api.github.com/rate_limit")
                return resp.status_code == 200
        except Exception:
            return False
