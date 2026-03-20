"""GitHub Deep scanner — full profile, events, repos, gists from email."""
import logging

import httpx

from api.services.base import BaseScanner, ScanResult

logger = logging.getLogger(__name__)


class GitHubDeepScanner(BaseScanner):
    MODULE_ID = "github_deep"
    LAYER = 1
    CATEGORY = "social_account"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        results = []
        headers = {"User-Agent": "xpose-tip", "Accept": "application/vnd.github.v3+json"}
        # Use GitHub token if available (60 req/hr -> 5000 req/hr)
        api_key = kwargs.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=15) as client:
            # Search for user by email
            try:
                resp = await client.get(
                    f"https://api.github.com/search/users?q={email}+in:email",
                    headers=headers,
                )
                if resp.status_code == 403:
                    logger.warning("GitHub API rate limited")
                    return []
                if resp.status_code != 200:
                    return []

                search_data = resp.json()
                items = search_data.get("items", [])
                if not items:
                    return []

            except Exception:
                logger.exception("GitHub search failed for %s", email)
                return []

            user_login = items[0].get("login", "")
            if not user_login:
                return []

            # Fetch full profile
            try:
                resp = await client.get(
                    f"https://api.github.com/users/{user_login}",
                    headers=headers,
                )
                if resp.status_code != 200:
                    return []
                profile = resp.json()
            except Exception:
                logger.exception("GitHub profile fetch failed for %s", user_login)
                return []

            name = profile.get("name", "")
            bio = profile.get("bio", "")
            company = profile.get("company", "")
            location = profile.get("location", "")
            blog = profile.get("blog", "")
            avatar_url = profile.get("avatar_url", "")
            html_url = profile.get("html_url", "")
            public_repos = profile.get("public_repos", 0)
            public_gists = profile.get("public_gists", 0)
            followers = profile.get("followers", 0)
            following = profile.get("following", 0)
            created_at = profile.get("created_at", "")
            twitter_username = profile.get("twitter_username", "")
            hireable = profile.get("hireable")

            # Main profile finding
            desc_parts = []
            if name:
                desc_parts.append(f"Name: {name}")
            if company:
                desc_parts.append(f"Company: {company}")
            if location:
                desc_parts.append(f"Location: {location}")
            if bio:
                desc_parts.append(f"Bio: {bio[:200]}")
            desc_parts.append(f"{public_repos} repos, {followers} followers")
            if created_at:
                desc_parts.append(f"Member since: {created_at[:10]}")

            results.append(ScanResult(
                module=self.MODULE_ID,
                layer=self.LAYER,
                category="social_account",
                severity="medium",
                title=f"GitHub profile: {user_login}" + (f" ({name})" if name else ""),
                description=". ".join(desc_parts),
                data={
                    "login": user_login,
                    "name": name,
                    "bio": bio,
                    "company": company,
                    "location": location,
                    "blog": blog,
                    "avatar_url": avatar_url,
                    "html_url": html_url,
                    "public_repos": public_repos,
                    "public_gists": public_gists,
                    "followers": followers,
                    "following": following,
                    "created_at": created_at,
                    "twitter_username": twitter_username,
                    "hireable": hireable,
                    "source": "github_deep",
                },
                url=html_url,
                indicator_value=html_url,
                indicator_type="social_url",
                verified=True,
            ))

            # Fetch recent public events (commits, PRs, issues — reveals activity)
            try:
                resp = await client.get(
                    f"https://api.github.com/users/{user_login}/events/public?per_page=30",
                    headers=headers,
                )
                if resp.status_code == 200:
                    events = resp.json()
                    # Unique repos from events
                    event_repos = set()
                    commit_emails = set()
                    for event in events:
                        repo = event.get("repo", {}).get("name", "")
                        if repo:
                            event_repos.add(repo)
                        # Extract commit emails from PushEvents
                        if event.get("type") == "PushEvent":
                            for commit in event.get("payload", {}).get("commits", []):
                                author_email = commit.get("author", {}).get("email", "")
                                if author_email and author_email != email:
                                    commit_emails.add(author_email)

                    if event_repos:
                        results.append(ScanResult(
                            module=self.MODULE_ID,
                            layer=self.LAYER,
                            category="metadata",
                            severity="info",
                            title=f"GitHub activity: {len(event_repos)} active repos",
                            description=f"Recent public activity across {len(event_repos)} repositories: {', '.join(list(event_repos)[:10])}",
                            data={
                                "active_repos": list(event_repos),
                                "event_count": len(events),
                                "source": "github_deep",
                            },
                            url=html_url,
                            indicator_value=user_login,
                            indicator_type="username",
                            verified=True,
                        ))

                    # Alternate emails from commits — gold for identity linking
                    for alt_email in commit_emails:
                        if "@users.noreply.github.com" not in alt_email:
                            results.append(ScanResult(
                                module=self.MODULE_ID,
                                layer=self.LAYER,
                                category="metadata",
                                severity="medium",
                                title=f"Alternate email in commits: {alt_email}",
                                description=f"A different email address ({alt_email}) was found in Git commit history for {user_login}",
                                data={
                                    "alt_email": alt_email,
                                    "github_login": user_login,
                                    "source": "github_deep",
                                },
                                indicator_value=alt_email,
                                indicator_type="email",
                                verified=True,
                            ))

            except Exception:
                logger.debug("GitHub events fetch failed for %s", user_login)

            # Fetch public gists
            if public_gists > 0:
                try:
                    resp = await client.get(
                        f"https://api.github.com/users/{user_login}/gists?per_page=10",
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        gists = resp.json()
                        if gists:
                            gist_descs = [g.get("description", "Untitled")[:60] for g in gists[:5]]
                            results.append(ScanResult(
                                module=self.MODULE_ID,
                                layer=self.LAYER,
                                category="metadata",
                                severity="info",
                                title=f"GitHub gists: {len(gists)} public",
                                description=f"Public gists found: {', '.join(gist_descs)}",
                                data={
                                    "gist_count": public_gists,
                                    "gists": [{"id": g["id"], "description": g.get("description", ""), "url": g.get("html_url", "")} for g in gists[:10]],
                                    "source": "github_deep",
                                },
                                url=f"https://gist.github.com/{user_login}",
                                indicator_value=user_login,
                                indicator_type="username",
                                verified=True,
                            ))
                except Exception:
                    logger.debug("GitHub gists fetch failed for %s", user_login)

            # Twitter from GitHub profile
            if twitter_username:
                results.append(ScanResult(
                    module=self.MODULE_ID,
                    layer=self.LAYER,
                    category="social_account",
                    severity="low",
                    title=f"Twitter/X linked: @{twitter_username}",
                    description=f"GitHub profile links to Twitter/X account @{twitter_username}",
                    data={"twitter": twitter_username, "source": "github_deep"},
                    url=f"https://x.com/{twitter_username}",
                    indicator_value=twitter_username,
                    indicator_type="username",
                    verified=True,
                ))

            # Blog/website
            if blog:
                results.append(ScanResult(
                    module=self.MODULE_ID,
                    layer=self.LAYER,
                    category="metadata",
                    severity="info",
                    title=f"Personal website: {blog}",
                    description=f"GitHub profile links to website: {blog}",
                    data={"blog": blog, "source": "github_deep"},
                    url=blog if blog.startswith("http") else f"https://{blog}",
                    indicator_value=blog,
                    indicator_type="domain",
                    verified=True,
                ))

        logger.info("GitHub Deep scan for %s: %d findings", email, len(results))
        return results

    async def health_check(self, **kwargs) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.github.com/rate_limit",
                    headers={"User-Agent": "xpose-tip"},
                )
                return resp.status_code == 200
        except Exception:
            return False
