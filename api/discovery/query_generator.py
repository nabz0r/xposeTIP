"""Query generator for the Discovery Engine.

Turns a target profile into prioritized Google search queries,
driven by fingerprint axes and behavioral signals.
"""
import json
import logging
import os
import time

from .variant_generator import generate_username_variants, generate_name_variants

logger = logging.getLogger(__name__)

_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_json(filename):
    path = os.path.join(_DIR, filename)
    with open(path) as f:
        return json.load(f)


class DiscoveryBudget:
    """Tracks query/page/time budget for a discovery session."""

    def __init__(self, max_queries=20, max_pages=50, max_seconds=60):
        self.max_queries = max_queries
        self.max_pages = max_pages
        self.queries_used = 0
        self.pages_used = 0
        self.deadline = time.time() + max_seconds

    def can_query(self) -> bool:
        return self.queries_used < self.max_queries and time.time() < self.deadline

    def can_fetch(self) -> bool:
        return self.pages_used < self.max_pages and time.time() < self.deadline

    def use_query(self):
        self.queries_used += 1

    def use_page(self):
        self.pages_used += 1

    @property
    def time_remaining(self) -> float:
        return max(0, self.deadline - time.time())

    def summary(self) -> dict:
        return {
            "queries": f"{self.queries_used}/{self.max_queries}",
            "pages": f"{self.pages_used}/{self.max_pages}",
            "time_remaining": f"{self.time_remaining:.0f}s",
        }


class QueryGenerator:
    """Generate prioritized search queries from a target profile.

    Input profile dict:
        identifiers: list of {type: "username"|"email", value: "..."}
        resolved_name: str or None
        axes: dict of fingerprint axis scores (0.0-1.0)
        geo_country: str (ISO 2-letter) or None
        platforms_found: list of platform domain strings
    """

    def __init__(self):
        self.templates = _load_json("query_templates.json")
        self.local_domains = _load_json("local_domains.json")

    def generate(self, profile: dict, max_queries: int = 20) -> list[dict]:
        """Generate prioritized query list from profile snapshot."""
        queries = []

        for tmpl in self.templates:
            if not self._check_requires(tmpl.get("requires", {}), profile):
                continue
            expanded = self._expand_template(tmpl, profile)
            queries.extend(expanded)

        # Sort by priority (ascending = highest priority first)
        queries.sort(key=lambda q: q["priority"])

        # Cap at budget
        return queries[:max_queries]

    def _check_requires(self, requires: dict, profile: dict) -> bool:
        """Check if template requirements are met by profile."""
        for key, condition in requires.items():
            if key.startswith("axes."):
                axis_name = key.split(".", 1)[1]
                axis_val = (profile.get("axes") or {}).get(axis_name, 0)
                if isinstance(condition, str) and condition.startswith(">"):
                    threshold = float(condition[1:])
                    if axis_val <= threshold:
                        return False
                elif condition is True and not axis_val:
                    return False
            elif key == "resolved_name":
                if condition is True and not profile.get("resolved_name"):
                    return False
            elif key == "geo_country":
                if condition is True and not profile.get("geo_country"):
                    return False
            else:
                if condition is True and not profile.get(key):
                    return False
        return True

    def _expand_template(self, tmpl: dict, profile: dict) -> list[dict]:
        """Expand a single template into concrete queries."""
        results = []
        template_str = tmpl["template"]
        id_types = tmpl.get("identifier_types", [])
        priority = tmpl.get("priority", 10)
        reason = tmpl.get("reason", "")
        template_id = tmpl.get("id", "unknown")

        identifiers = profile.get("identifiers") or []
        resolved_name = profile.get("resolved_name") or ""
        platforms = profile.get("platforms_found") or []
        geo_country = (profile.get("geo_country") or "").upper()

        exclusions = self._build_exclusions(platforms)

        # Variant-type templates
        if "variant" in id_types:
            usernames = [i["value"] for i in identifiers if i.get("type") == "username"]
            for username in usernames[:3]:
                for variant in generate_username_variants(username):
                    query = template_str.replace("{variant}", variant)
                    results.append({
                        "query": query,
                        "priority": priority,
                        "reason": reason.replace("{variant}", variant),
                        "template_id": template_id,
                    })
            return results

        if "name_variant" in id_types:
            if resolved_name and " " in resolved_name:
                parts = resolved_name.strip().split()
                first, last = parts[0], parts[-1]
                for variant in generate_name_variants(first, last):
                    query = template_str.replace("{name_variant}", variant)
                    results.append({
                        "query": query,
                        "priority": priority,
                        "reason": reason.replace("{name_variant}", variant),
                        "template_id": template_id,
                    })
            return results

        # Identifier-expansion templates
        if id_types:
            matching = [i for i in identifiers if i.get("type") in id_types]
            for ident in matching[:3]:
                query = template_str.replace("{identifier}", ident["value"])
                query = query.replace("{exclusions}", exclusions)
                query = query.replace("{resolved_name}", resolved_name)

                # Local domains
                if "{local_domains}" in query:
                    local = self.local_domains.get(geo_country, "")
                    if not local:
                        continue
                    query = query.replace("{local_domains}", local)

                # Axis value in reason — use the specific axis from requires
                r = reason
                requires = tmpl.get("requires", {})
                for req_key in requires:
                    if req_key.startswith("axes."):
                        axis_name = req_key.split(".", 1)[1]
                        val = (profile.get("axes") or {}).get(axis_name, 0)
                        r = r.replace("{axis_value}", f"{val:.2f}")
                        break
                r = r.replace("{axis_value}", "")

                results.append({
                    "query": query.strip(),
                    "priority": priority,
                    "reason": r,
                    "template_id": template_id,
                })
        else:
            # Non-identifier templates (name-based, local news)
            query = template_str.replace("{resolved_name}", resolved_name)
            query = query.replace("{exclusions}", exclusions)
            query = query.replace("{identifier}", resolved_name)

            if "{local_domains}" in query:
                local = self.local_domains.get(geo_country, "")
                if not local:
                    return results
                query = query.replace("{local_domains}", local)

            r = reason.replace("{geo_country}", geo_country)

            results.append({
                "query": query.strip(),
                "priority": priority,
                "reason": r,
                "template_id": template_id,
            })

        return results

    def _build_exclusions(self, platforms: list[str]) -> str:
        """Generate -site:xxx.com clauses from known platforms."""
        if not platforms:
            return ""
        # Cap at 10 to stay under Google query length limits
        exclusions = [f"-site:{p}" for p in platforms[:10]]
        return " ".join(exclusions)
