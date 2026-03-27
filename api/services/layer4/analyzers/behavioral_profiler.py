"""Behavioral Profiler — classify identity based on account activity patterns.

Reads enriched extraction data (followers, repos, karma, gists) from scraper
findings to build behavioral archetypes: developer, gamer, creative, professional,
social influencer, privacy-conscious, lurker.

Produces intelligence findings that enrich the persona engine.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_PLATFORM_CATEGORIES = {
    "dev": {"github", "gitlab", "stackoverflow", "hackernews", "devto",
            "npm", "pypi", "crates", "packagist", "codewars", "replit",
            "hackerrank", "kaggle", "bitbucket"},
    "gaming": {"steam", "roblox", "minecraft", "chess", "lichess",
               "speedrun", "anilist", "myanimelist"},
    "creative": {"behance", "dribbble", "flickr", "pinterest", "soundcloud",
                 "bandcamp", "mixcloud", "deviantart"},
    "social": {"reddit", "twitter", "mastodon", "bluesky", "threads",
               "telegram", "instagram", "tiktok", "snapchat"},
    "professional": {"linkedin", "crunchbase", "about_me", "linktree",
                     "gravatar", "keybase"},
}


class BehavioralProfiler:
    def analyze(self, findings: list, identities: list) -> list:
        results = []

        # 1. Collect platform presence by category
        platforms_found = {}  # platform_name -> finding data
        category_counts = {cat: 0 for cat in _PLATFORM_CATEGORIES}

        for f in findings:
            if not f.data or f.category not in ("social_account", "social_media"):
                continue
            module = (getattr(f, "module", "") or "").replace("scraper_", "").split("_")[0]
            data = f.data if isinstance(f.data, dict) else {}
            extracted = data.get("extracted", data)
            platforms_found[module] = extracted

            for cat, platforms in _PLATFORM_CATEGORIES.items():
                if module in platforms:
                    category_counts[cat] += 1

        if not platforms_found:
            return results

        # 2. Extract key metrics
        metrics = self._extract_metrics(platforms_found)

        # 3. Detect archetypes
        archetypes = []

        # Developer archetype
        if category_counts["dev"] >= 3 or metrics.get("github_repos", 0) >= 10:
            level = "senior" if metrics.get("github_repos", 0) >= 50 else \
                    "active" if metrics.get("github_repos", 0) >= 10 else "present"
            detail_parts = []
            if metrics.get("github_repos"):
                detail_parts.append(f"{metrics['github_repos']} repos")
            if metrics.get("github_followers"):
                detail_parts.append(f"{metrics['github_followers']} followers")
            if metrics.get("github_gists"):
                detail_parts.append(f"{metrics['github_gists']} gists")
            if metrics.get("hn_karma"):
                detail_parts.append(f"HN karma {metrics['hn_karma']}")
            archetypes.append({
                "tag": f"Developer ({level})",
                "platforms": category_counts["dev"],
                "detail": ", ".join(detail_parts) if detail_parts else f"{category_counts['dev']} dev platforms",
                "severity": "medium" if level == "senior" else "low",
            })

        # Gamer archetype
        if category_counts["gaming"] >= 2:
            archetypes.append({
                "tag": "Gamer",
                "platforms": category_counts["gaming"],
                "detail": f"{category_counts['gaming']} gaming platforms",
                "severity": "low",
            })

        # Creative archetype
        if category_counts["creative"] >= 2:
            archetypes.append({
                "tag": "Creative / Designer",
                "platforms": category_counts["creative"],
                "detail": f"{category_counts['creative']} creative platforms",
                "severity": "low",
            })

        # Social influencer archetype
        total_followers = (
            metrics.get("github_followers", 0) +
            metrics.get("reddit_karma", 0) // 100 +
            metrics.get("medium_followers", 0) +
            metrics.get("hn_karma", 0) // 50
        )
        if total_followers >= 50 or metrics.get("reddit_karma", 0) >= 10000:
            archetypes.append({
                "tag": "Social Influencer",
                "platforms": category_counts["social"],
                "detail": f"~{total_followers} combined reach across platforms",
                "severity": "medium",
            })

        # Privacy-conscious
        privacy_signals = sum(1 for p in platforms_found if p in ("keybase", "protonmail", "tutanota"))
        if privacy_signals >= 1:
            archetypes.append({
                "tag": "Privacy-conscious",
                "platforms": privacy_signals,
                "detail": "Uses encrypted/privacy-focused services",
                "severity": "info",
            })

        # 4. Generate findings

        # Main behavioral profile finding
        if archetypes:
            primary = max(archetypes, key=lambda a: a["platforms"])
            all_tags = [a["tag"] for a in archetypes]

            results.append({
                "title": f"Behavioral profile: {primary['tag']}",
                "description": (
                    f"Identity classified as: {', '.join(all_tags)}. "
                    f"Based on activity across {len(platforms_found)} platforms. "
                    + " \u00b7 ".join(a["detail"] for a in archetypes)
                ),
                "category": "intelligence",
                "severity": primary["severity"],
                "data": {
                    "analyzer": "behavioral_profiler",
                    "archetypes": archetypes,
                    "category_breakdown": {k: v for k, v in category_counts.items() if v > 0},
                    "metrics": metrics,
                    "total_platforms": len(platforms_found),
                },
                "indicator_type": "behavioral_profile",
                "indicator_value": primary["tag"],
            })

        # Account longevity finding
        if metrics.get("oldest_account_years", 0) >= 5:
            results.append({
                "title": f"Long-term digital presence: {metrics['oldest_account_years']:.0f}+ years",
                "description": (
                    f"Oldest discovered account is {metrics['oldest_account_years']:.0f} years old. "
                    f"Long-standing digital identity increases historical exposure surface."
                ),
                "category": "intelligence",
                "severity": "low",
                "data": {
                    "analyzer": "behavioral_profiler",
                    "oldest_account_years": metrics["oldest_account_years"],
                    "oldest_platform": metrics.get("oldest_platform", "unknown"),
                },
            })

        # High-activity finding
        if metrics.get("github_repos", 0) >= 50 or metrics.get("reddit_karma", 0) >= 50000:
            results.append({
                "title": "High-activity user \u2014 significant public data trail",
                "description": (
                    "This identity generates substantial public data. "
                    + (f"GitHub: {metrics['github_repos']} repos, {metrics.get('github_followers', 0)} followers. " if metrics.get("github_repos") else "")
                    + (f"Reddit: {metrics['reddit_karma']} karma. " if metrics.get("reddit_karma") else "")
                    + "High activity creates more data points for correlation and social engineering."
                ),
                "category": "intelligence",
                "severity": "medium",
                "data": {
                    "analyzer": "behavioral_profiler",
                    "metrics": metrics,
                },
            })

        return results

    def _extract_metrics(self, platforms: dict) -> dict:
        """Pull key numeric metrics from extracted data across platforms."""
        m = {}

        # GitHub
        gh = platforms.get("github", {})
        if gh:
            for key in ("public_repos", "followers", "following", "public_gists"):
                val = gh.get(key)
                if val is not None:
                    try:
                        m[f"github_{key.replace('public_', '')}" if "public_" in key else f"github_{key}"] = int(val)
                    except (ValueError, TypeError):
                        pass
            if gh.get("created_at"):
                m["github_created"] = gh["created_at"]
            if gh.get("hireable"):
                m["github_hireable"] = True

        # Reddit
        rd = platforms.get("reddit", {})
        if rd:
            for key in ("total_karma", "comment_karma", "link_karma"):
                val = rd.get(key)
                if val is not None:
                    try:
                        m[f"reddit_{key}"] = int(val)
                    except (ValueError, TypeError):
                        pass
            m["reddit_karma"] = m.get("reddit_total_karma", 0)
            if rd.get("is_gold"):
                m["reddit_gold"] = True

        # HackerNews
        hn = platforms.get("hackernews", {})
        if hn:
            try:
                m["hn_karma"] = int(hn.get("karma", 0))
            except (ValueError, TypeError):
                pass

        # Medium
        md = platforms.get("medium", {})
        if md:
            try:
                m["medium_followers"] = int(md.get("followers", 0))
            except (ValueError, TypeError):
                pass

        # Kaggle
        kg = platforms.get("kaggle", {})
        if kg:
            for key in ("competitions_count", "datasets_count", "notebooks_count"):
                val = kg.get(key)
                if val is not None:
                    try:
                        m[f"kaggle_{key}"] = int(val)
                    except (ValueError, TypeError):
                        pass

        # Account age (compute oldest)
        now = datetime.now()
        oldest_years = 0
        oldest_platform = None

        for platform, data in platforms.items():
            for date_field in ("created_at", "created_utc", "created", "joined_at", "member_since"):
                val = data.get(date_field)
                if not val:
                    continue
                try:
                    if isinstance(val, (int, float)) and val > 1000000000:
                        dt = datetime.fromtimestamp(val)
                    else:
                        dt = datetime.fromisoformat(str(val).replace("Z", "+00:00").replace("+00:00", ""))
                    years = (now - dt).days / 365.25
                    if years > oldest_years and years < 30:
                        oldest_years = years
                        oldest_platform = platform
                except (ValueError, TypeError, OSError):
                    pass

        if oldest_years > 0:
            m["oldest_account_years"] = round(oldest_years, 1)
            m["oldest_platform"] = oldest_platform

        return m
