"""Discovery Engine pipeline — orchestrates query → search → fetch → extract.

Phase C of the xposeTIP scan pipeline. Connects:
- QueryGenerator (Sprint C) → search queries from profile
- SearchClient (Sprint D) → Google results via SerpAPI
- PageFetcher (Sprint D) → download + extract pages
- Extractors (Sprint B) → extract leads from pages
- QualityGate (Sprint D) → filter known identifiers
- DB storage → discovery_leads table (Sprint A)
"""
import logging
import os
import time
import uuid

from .query_generator import QueryGenerator, DiscoveryBudget
from .search_client import get_search_client
from .page_fetcher import PageFetcher
from .quality_gate import QualityGate
from .extractors import extract_all

logger = logging.getLogger(__name__)


_JUNK_KEYWORDS = {"fashion", "outfit", "recipe", "lyrics", "download", "free",
                   "buy", "shop", "a new era", "official", "cookie policy",
                   "terms of service", "privacy policy",
                   "wiki", "wikipedia", "bulbapedia", "fandom",
                   "encyclopedia", "dictionary", "community-driven", "the free",
                   "pinterest", "tumblr"}

_JUNK_USERNAME_SET = {
    "articles", "article", "news", "home", "about", "contact",
    "search", "login", "signup", "register", "help", "support",
    "blog", "posts", "tags", "categories", "page", "pages",
    "index", "main", "default", "admin", "user", "users",
    "share", "follow", "subscribe", "comments", "status",
    "explore", "trending", "popular", "latest", "new",
    "privacy", "terms", "policy", "cookies", "settings",
    "null", "undefined", "none", "true", "false",
}

MAX_ROUNDS = 3
ROUND1_MAX_QUERIES = 8


def _is_junk_lead(lead_type: str, lead_value: str) -> bool:
    """Filter obvious false positives (page titles as names, generic usernames)."""
    if lead_type == "name":
        if len(lead_value) > 80:
            return True
        if lead_value.count("|") >= 1 or " | " in lead_value:
            return True
        if lead_value.count(",") >= 3:
            return True
        if " - " in lead_value or " \u2014 " in lead_value:
            return True
        val_lower = lead_value.lower()
        return any(kw in val_lower for kw in _JUNK_KEYWORDS)
    if lead_type == "username":
        return lead_value.lower().strip() in _JUNK_USERNAME_SET
    return False


class DiscoveryPipeline:
    """Orchestrate a complete Phase C discovery session."""

    def __init__(self, target_id=None, session_id=None, budget=None,
                 db_session=None, on_discovery=None, dry_run=False):
        self.target_id = target_id
        self.session_id = session_id
        self.budget = budget or DiscoveryBudget()
        self.db = db_session
        self.on_discovery = on_discovery
        self.dry_run = dry_run
        self.search_client = get_search_client()
        self.page_fetcher = PageFetcher()
        self.query_generator = QueryGenerator()
        self.quality_gate = QualityGate(target_id, db_session)  # always pass DB for reads
        self.all_leads = []
        self.filtered_count = 0
        self.seen_leads = {}  # (type, value_lower) → {lead, confidence} for cross-page dedup
        self._profile = {}

    def run(self, profile_snapshot: dict = None) -> dict:
        """Execute the full discovery pipeline with multi-round pivot loop."""
        t0 = time.time()
        self._rounds_completed = 0
        self._leads_per_round = []
        self._pivot_query_count = 0
        self._previous_queries = []

        # Build or use provided profile
        if profile_snapshot is None and self.db and self.target_id:
            profile_snapshot = self._build_profile_snapshot(self.target_id)
        if not profile_snapshot:
            return {"error": "No profile snapshot available", "leads": []}

        self._profile = profile_snapshot

        if self.dry_run:
            self.quality_gate.load_from_profile(profile_snapshot)

        # Extract email for pivot strategy
        self._email = ""
        for ident in profile_snapshot.get("identifiers", []):
            if ident.get("type") == "email":
                self._email = ident["value"]
                break

        # ═══ ROUND LOOP ═══
        round_leads = []  # leads from current round (for pivot input)

        for round_num in range(1, MAX_ROUNDS + 1):
            if not self.budget.can_query():
                break

            # Round 1: queries from profile (existing behavior)
            # Round 2+: queries from PivotStrategy
            if round_num == 1:
                queries = self.query_generator.generate(profile_snapshot, min(ROUND1_MAX_QUERIES, self.budget.max_queries))
                logger.info("Discovery R%d: %d profile queries for %s", round_num, len(queries), self.target_id)
            else:
                queries = self._generate_pivot_queries(round_leads)
                self._pivot_query_count += len(queries)
                if not queries:
                    break
                logger.info("Discovery R%d: %d pivot queries for %s", round_num, len(queries), self.target_id)

            self._emit("round_start", f"Round {round_num}: {len(queries)} queries" + (" (pivot)" if round_num > 1 else ""),
                        {"round": round_num, "queries_planned": len(queries)}, 0)

            # Execute queries
            round_leads = self._run_depth(queries, depth=0)

            # Depth 1: follow URL-type leads from this round
            url_leads = [l for l in round_leads if l.lead_type == "url"]
            if url_leads and self.budget.can_fetch():
                depth1_leads = self._run_url_depth(url_leads[:5], depth=1)
                round_leads.extend(depth1_leads)

            self._rounds_completed = round_num
            self._leads_per_round.append(len(round_leads))

            self._emit("round_end", f"Round {round_num} complete: {len(round_leads)} leads",
                        {"round": round_num, "leads_found": len(round_leads)}, 0)

        # Build final summary
        elapsed = time.time() - t0
        final_leads = sorted(self.seen_leads.values(), key=lambda x: -x["confidence"])
        summary = {
            "queries_executed": self.budget.queries_used,
            "pages_fetched": self.budget.pages_used,
            "leads_found": len(final_leads),
            "leads_filtered": self.filtered_count,
            "duration_seconds": round(elapsed, 1),
            "rounds_completed": self._rounds_completed,
            "leads_per_round": self._leads_per_round,
            "pivot_queries_generated": self._pivot_query_count,
            "leads": [
                {"type": l["type"], "value": l["value"], "confidence": l["confidence"],
                 "extractor": l["extractor"], "context": l["context"]}
                for l in final_leads
            ],
        }

        if self.dry_run:
            print(f"\n{'='*60}")
            print(f"Discovery complete: {summary['leads_found']} leads, "
                  f"{summary['rounds_completed']} rounds, "
                  f"{summary['pivot_queries_generated']} pivots, "
                  f"{summary['queries_executed']} queries, "
                  f"{summary['pages_fetched']} pages, "
                  f"{summary['duration_seconds']}s")

        return summary

    def _generate_pivot_queries(self, round_leads: list) -> list[dict]:
        """Generate pivot queries from leads using PivotStrategy."""
        try:
            from api.discovery.pivot_strategy import generate_pivots

            lead_dicts = []
            for key, lead_data in self.seen_leads.items():
                lead_dicts.append({
                    "lead_type": lead_data["type"],
                    "lead_value": lead_data["value"],
                    "confidence": lead_data["confidence"],
                    "id": None,
                })

            pivots = generate_pivots(
                leads=lead_dicts,
                profile=self._profile,
                email=self._email,
                budget_remaining=self.budget.queries_remaining,
                previous_queries=self._previous_queries,
            )

            # Convert PivotQuery objects to query_data dicts for _process_query
            return [
                {
                    "query": p.query,
                    "reason": p.reason,
                    "query_type": p.pivot_type,
                    "template_id": f"pivot_{p.pivot_type}",
                    "priority": p.priority,
                }
                for p in pivots
            ]
        except Exception as e:
            logger.warning("Pivot generation failed: %s — falling back to single round", e)
            return []

    def _run_depth(self, queries: list, depth: int) -> list:
        """Run queries at a given depth level."""
        leads = []
        for qdata in queries:
            if not self.budget.can_query():
                break
            self._previous_queries.append(qdata.get("query", ""))
            new_leads = self._process_query(qdata, depth)
            leads.extend(new_leads)
            self._update_session_counters()
        return leads

    def _run_url_depth(self, url_leads: list, depth: int) -> list:
        """Fetch URL-type leads directly (no Google query)."""
        leads = []
        for lead in url_leads[:10]:  # Cap URL follows per depth
            if not self.budget.can_fetch():
                break
            chain = [{"step": "follow", "url": lead.value, "reason": "URL lead from depth " + str(depth - 1)}]
            new_leads = self._process_page(lead.value, lead.context, depth, chain)
            leads.extend(new_leads)
        return leads

    def _process_query(self, query_data: dict, depth: int) -> list:
        """Execute one query: search → fetch results → extract leads."""
        query = query_data["query"]
        reason = query_data.get("reason", "")
        query_type = query_data.get("query_type", "identifier")

        query_id = self._emit("query", query[:80], {"reason": reason}, depth)
        self.budget.use_query()

        try:
            results = self.search_client.search(query, num_results=10)
        except Exception as e:
            logger.debug("Search failed for '%s': %s", query[:80], e)
            return []

        leads = []
        for result in results:
            if not self.budget.can_fetch():
                break
            chain = [
                {"step": "query", "value": query, "reason": reason, "query_type": query_type},
                {"step": "hit", "url": result["url"], "title": result.get("title", "")},
            ]
            hit_id = self._emit("hit", result.get("title", "")[:60], result, depth, query_id)
            new_leads = self._process_page(result["url"], result.get("title", ""), depth, chain)
            leads.extend(new_leads)

        return leads

    def _process_page(self, url: str, title: str, depth: int, chain: list) -> list:
        """Fetch one page, run extractors, quality gate, return new leads."""
        self.budget.use_page()

        page = self.page_fetcher.fetch(url)
        if not page:
            return []

        # Run all extractors with relevance + geo scoring
        known = self.quality_gate.known_identifiers
        resolved_name = self._profile.get("resolved_name")
        target_geo = self._profile.get("geo_country")
        raw_leads = extract_all(
            page["url"], page.get("text", ""), page.get("html", ""),
            known_identifiers=known, resolved_name=resolved_name,
            target_geo=target_geo,
        )

        # Quality gate filter
        filtered = self.quality_gate.filter(raw_leads)
        self.filtered_count += len(raw_leads) - len(filtered)

        # Page relevance check: if query contains the resolved name, verify page
        # actually mentions unique target identifiers (homonyme protection)
        resolved_name = self._profile.get("resolved_name", "")
        query_str = " ".join(
            step.get("value", "") for step in chain if isinstance(step, dict) and step.get("step") == "query"
        )
        is_name_query = resolved_name and resolved_name.lower() in query_str.lower()
        if is_name_query and not self._is_page_relevant(page.get("text", "")):
            if self.dry_run:
                print(f"    \u23ed\ufe0f [skip] page doesn't mention target identifiers")
            return []

        # Junk filter + JSON-LD name confidence cap
        clean = []
        for lead in filtered:
            if _is_junk_lead(lead.lead_type, lead.value):
                continue
            if lead.lead_type == "name" and lead.extractor_type == "jsonld":
                lead.confidence = min(lead.confidence, 0.60)
            clean.append(lead)

        # Store/emit each lead (cross-page dedup)
        new_leads = []
        for lead in clean:
            dedup_key = (lead.lead_type, lead.value.lower())
            existing = self.seen_leads.get(dedup_key)
            if existing and existing["confidence"] >= lead.confidence:
                continue

            lead_data = {
                "type": lead.lead_type, "value": lead.value,
                "confidence": lead.confidence, "extractor": lead.extractor_type,
                "context": lead.context,
            }
            self.seen_leads[dedup_key] = lead_data

            lead_chain = chain + [{"step": "extract", "extractor": lead.extractor_type, "value": lead.value}]
            self._store_lead(lead, url, title or page.get("title", ""), lead_chain, depth)
            self._emit("lead", f"{lead.lead_type}: {lead.value}", {
                "type": lead.lead_type, "confidence": lead.confidence,
                "extractor": lead.extractor_type,
            }, depth)
            new_leads.append(lead)

        return new_leads

    def _store_lead(self, lead, source_url, source_title, chain, depth):
        """Write lead to discovery_leads DB. Skipped in dry-run."""
        if self.dry_run:
            return

        if not self.db or not self.session_id:
            return

        try:
            from api.models.discovery import DiscoveryLead

            # Depth penalty on confidence
            depth_penalty = 0.15 * depth
            confidence = max(0.1, lead.confidence - depth_penalty)

            db_lead = DiscoveryLead(
                id=uuid.uuid4(),
                session_id=self.session_id,
                target_id=uuid.UUID(str(self.target_id)),
                workspace_id=self._workspace_id,
                lead_type=lead.lead_type,
                lead_value=lead.value,
                source_url=source_url,
                source_title=(source_title or "")[:500],
                source_snippet=(lead.context or "")[:500],
                discovery_chain=chain,
                depth=depth,
                confidence=confidence,
                extractor_type=lead.extractor_type,
                status="new",
            )
            self.db.add(db_lead)
            self.db.flush()
        except Exception as e:
            logger.debug("Failed to store lead %s: %s", lead.value, e)

    def _update_session_counters(self):
        """Update session row with current counters for live polling."""
        if self.dry_run or not self.db or not self.session_id:
            return
        try:
            from sqlalchemy import select as sa_select
            from api.models.discovery import DiscoverySession
            session_obj = self.db.execute(
                sa_select(DiscoverySession).where(DiscoverySession.id == uuid.UUID(str(self.session_id)))
            ).scalar_one_or_none()
            if session_obj:
                session_obj.queries_executed = self.budget.queries_used
                session_obj.pages_fetched = self.budget.pages_used
                session_obj.leads_found = len(self.seen_leads)
                self.db.commit()
        except Exception:
            pass

    def _is_page_relevant(self, page_text: str) -> bool:
        """Check if page mentions target's unique identifiers (not just name)."""
        text_lower = page_text.lower()
        profile = self._profile

        for ident in profile.get("identifiers", []):
            if ident.get("type") in ("username", "email"):
                if ident["value"].lower() in text_lower:
                    return True

        # Check email domain as employer marker
        for ident in profile.get("identifiers", []):
            if ident.get("type") == "email" and "@" in ident.get("value", ""):
                domain = ident["value"].split("@")[1].split(".")[0].lower()
                if len(domain) > 3 and domain in text_lower:
                    return True

        return False

    def _build_profile_snapshot(self, target_id) -> dict:
        """Build profile snapshot from existing target data in DB."""
        from sqlalchemy import select
        from api.models.target import Target
        from api.models.finding import Finding

        tid = uuid.UUID(str(target_id)) if isinstance(target_id, str) else target_id

        target = self.db.execute(select(Target).where(Target.id == tid)).scalar_one_or_none()
        if not target:
            return {}

        self._workspace_id = target.workspace_id
        profile = target.profile_data or {}
        fingerprint = profile.get("fingerprint", {})

        # Build identifiers
        identifiers = []
        if target.email:
            identifiers.append({"type": "email", "value": target.email})

        # Usernames from findings
        findings = self.db.execute(
            select(Finding).where(Finding.target_id == tid)
        ).scalars().all()

        seen_usernames = set()
        platforms_found = set()
        for f in findings:
            if f.indicator_type == "username" and f.indicator_value:
                uname = f.indicator_value.strip()
                if uname.lower() not in seen_usernames:
                    seen_usernames.add(uname.lower())
                    identifiers.append({"type": "username", "value": uname})

            # Platform domains
            data = f.data if isinstance(f.data, dict) else {}
            platform = data.get("platform", "")
            if platform:
                platforms_found.add(f"{platform}.com" if "." not in platform else platform)
            if f.url:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(f.url).netloc.lower()
                    if domain:
                        platforms_found.add(domain)
                except Exception:
                    pass

        # Resolved name
        resolved_name = profile.get("primary_name") or target.display_name

        # Axes
        axes = fingerprint.get("axes", {})

        # Geo
        geo_country = target.country_code
        if not geo_country:
            geo = profile.get("geo_consistency", {})
            if isinstance(geo, dict):
                geo_country = geo.get("primary_country")

        return {
            "identifiers": identifiers[:10],
            "resolved_name": resolved_name,
            "axes": axes,
            "geo_country": geo_country,
            "platforms_found": sorted(platforms_found)[:30],
        }

    def _emit(self, node_type: str, label: str, detail: dict, depth: int, parent_id: str = None) -> str:
        """Emit a discovery event via callback or print."""
        node_id = str(uuid.uuid4())
        node = {
            "node_id": node_id,
            "parent_id": parent_id or "root",
            "node_type": node_type,
            "label": label,
            "detail": detail,
            "depth": depth,
        }
        if self.on_discovery:
            try:
                self.on_discovery(node)
            except Exception:
                pass
        if self.dry_run:
            indent = "  " * (depth + 1)
            icon = {"query": "\U0001f50d", "hit": "\U0001f4c4", "lead": "\U0001f4a1"}.get(node_type, "\u2022")
            print(f"{indent}{icon} [{node_type}] {label}")
        return node_id
