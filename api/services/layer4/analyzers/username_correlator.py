"""Username Correlator — cross-reference usernames across platforms.

Detects username reuse, variations, and account proliferation.
"""
import logging

logger = logging.getLogger(__name__)


class UsernameCorrelator:
    def analyze(self, findings: list, identities: list) -> list:
        results = []

        # 1. Collect all usernames and their platforms
        usernames = {}  # username → list of platforms
        for f in findings:
            if not f.data:
                continue
            if f.category == "social_account" or f.module in ("holehe", "sherlock", "username_hunter"):
                username = (
                    f.data.get("username")
                    or f.data.get("handle")
                    or f.data.get("login")
                    or ""
                )
                platform = (
                    f.data.get("platform")
                    or f.data.get("network")
                    or f.data.get("service")
                    or f.module
                )
                if username and len(username) >= 2:
                    usernames.setdefault(username.lower(), []).append(platform)

        if not usernames:
            return results

        # 2. Detect username reuse (same username, multiple platforms)
        for username, platforms in usernames.items():
            unique_platforms = list(set(platforms))
            if len(unique_platforms) > 1:
                results.append({
                    "title": f"Username '{username}' reused across {len(unique_platforms)} platforms",
                    "description": (
                        f"Found on: {', '.join(sorted(unique_platforms))}. "
                        "Username reuse increases attack surface — compromise of one "
                        "account aids credential stuffing on others."
                    ),
                    "category": "intelligence",
                    "severity": "medium",
                    "data": {
                        "analyzer": "username_correlator",
                        "username": username,
                        "platforms": sorted(unique_platforms),
                        "platform_count": len(unique_platforms),
                        "risk": "credential_stuffing",
                    },
                    "indicator_value": username,
                    "indicator_type": "username",
                })

        # 3. Detect username variations (likely same person)
        all_usernames = list(usernames.keys())
        seen_pairs = set()
        for i, u1 in enumerate(all_usernames):
            for u2 in all_usernames[i + 1:]:
                pair = tuple(sorted([u1, u2]))
                if pair in seen_pairs:
                    continue
                if self._likely_same_person(u1, u2):
                    seen_pairs.add(pair)
                    combined = sorted(set(usernames[u1] + usernames[u2]))
                    results.append({
                        "title": f"Username correlation: '{u1}' and '{u2}'",
                        "description": (
                            f"These usernames appear to belong to the same person "
                            f"(similar pattern). Combined platforms: {', '.join(combined)}"
                        ),
                        "category": "intelligence",
                        "severity": "low",
                        "data": {
                            "analyzer": "username_correlator",
                            "usernames": [u1, u2],
                            "combined_platforms": combined,
                            "match_type": "variation",
                        },
                        "indicator_value": u1,
                        "indicator_type": "username",
                    })

        # 4. Account proliferation assessment
        total_accounts = sum(len(set(p)) for p in usernames.values())
        unique_platforms = set()
        for platforms in usernames.values():
            unique_platforms.update(platforms)

        if total_accounts > 5:
            severity = "high" if total_accounts > 15 else "medium" if total_accounts > 10 else "low"
            results.append({
                "title": f"Account proliferation: {total_accounts} accounts, {len(usernames)} usernames",
                "description": (
                    f"Found {total_accounts} accounts across {len(unique_platforms)} platforms "
                    f"using {len(usernames)} usernames. Large digital footprint increases "
                    "exposure to credential stuffing, social engineering, and data broker profiling."
                ),
                "category": "intelligence",
                "severity": severity,
                "data": {
                    "analyzer": "username_correlator",
                    "total_accounts": total_accounts,
                    "unique_usernames": len(usernames),
                    "unique_platforms": len(unique_platforms),
                    "platforms": sorted(unique_platforms),
                    "usernames": sorted(usernames.keys()),
                },
            })

        return results

    def _likely_same_person(self, u1: str, u2: str) -> bool:
        """Check if two usernames are variations of the same person."""
        if u1 == u2:
            return False

        # Strip trailing numbers/special chars
        base1 = u1.rstrip("0123456789_-.")
        base2 = u2.rstrip("0123456789_-.")
        if base1 and base2 and base1 == base2:
            return True

        # One contains the other (min length 4 to avoid false positives)
        if len(u1) >= 4 and len(u2) >= 4:
            if u1 in u2 or u2 in u1:
                return True

        return False
