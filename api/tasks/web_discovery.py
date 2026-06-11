"""Celery task for Phase C — Web Discovery."""
import logging
import re
import uuid
from datetime import datetime, timezone

from celery.exceptions import SoftTimeLimitExceeded

from sqlalchemy import select

from api.tasks import celery_app
from api.tasks.utils import get_sync_session
from api.services.event_bus import publish_event

logger = logging.getLogger(__name__)


@celery_app.task(
    name="api.tasks.web_discovery.run_discovery",
    bind=True,
    soft_time_limit=600,
    time_limit=660,
)
def run_discovery(self, target_id: str, session_id: str, workspace_id: str,
                  triggered_by: str = None, budget_config: dict = None):
    """Run Phase C Web Discovery for a target."""
    db = get_sync_session()
    try:
        from api.models.target import Target
        from api.models.discovery import DiscoverySession
        from api.discovery.pipeline import DiscoveryPipeline
        from api.discovery.query_generator import DiscoveryBudget

        tid = uuid.UUID(target_id)
        sid = uuid.UUID(session_id)
        pipeline = None  # initialized later, accessible in timeout handler

        target = db.execute(select(Target).where(Target.id == tid)).scalar_one_or_none()
        if not target:
            logger.error("Discovery: target %s not found", target_id)
            return

        session_obj = db.execute(
            select(DiscoverySession).where(DiscoverySession.id == sid)
        ).scalar_one_or_none()
        if not session_obj:
            logger.error("Discovery: session %s not found", session_id)
            return

        publish_event("discovery.started", {
            "workspace_id": workspace_id,
            "target_id": target_id,
            "session_id": session_id,
        })

        bc = budget_config or {}
        budget = DiscoveryBudget(
            max_queries=bc.get("max_queries", session_obj.max_queries),
            max_pages=bc.get("max_pages", session_obj.max_pages),
            max_seconds=bc.get("budget_seconds", session_obj.budget_seconds),
        )

        from api.models.discovery import DiscoveryEvent
        _event_count = [0]

        def on_discovery(node):
            # Persist event to DB
            try:
                event = DiscoveryEvent(
                    session_id=sid,
                    event_type=node.get("node_type", "unknown"),
                    payload=node,
                )
                db.add(event)
                _event_count[0] += 1
                # Periodic commit every 5 events for live polling visibility
                if _event_count[0] % 5 == 0:
                    # Also update session counters
                    session_obj.queries_executed = budget.queries_used
                    session_obj.pages_fetched = budget.pages_used
                    db.commit()
            except Exception:
                pass
            # SSE event
            publish_event("discovery.node", {
                "workspace_id": workspace_id,
                "target_id": target_id,
                "session_id": session_id,
                **node,
            })

        pipeline = DiscoveryPipeline(
            target_id=target_id,
            session_id=session_id,
            budget=budget,
            db_session=db,
            on_discovery=on_discovery,
            dry_run=False,
        )
        result = pipeline.run()

        session_obj.status = "completed"
        session_obj.queries_executed = result.get("queries_executed", 0)
        session_obj.pages_fetched = result.get("pages_fetched", 0)
        session_obj.leads_found = result.get("leads_found", 0)
        session_obj.completed_at = datetime.now(timezone.utc)
        db.commit()

        publish_event("discovery.completed", {
            "workspace_id": workspace_id,
            "target_id": target_id,
            "session_id": session_id,
            "queries_executed": result.get("queries_executed", 0),
            "pages_fetched": result.get("pages_fetched", 0),
            "leads_found": result.get("leads_found", 0),
            "duration_seconds": result.get("duration_seconds", 0),
        })

        # Auto-ingest high-confidence leads (async, separate task)
        if result.get("leads_found", 0) > 0:
            auto_ingest_leads.delay(target_id, session_id, workspace_id)

        logger.info("Discovery complete for %s: %d leads in %.1fs",
                     target_id, result.get("leads_found", 0),
                     result.get("duration_seconds", 0))

    except SoftTimeLimitExceeded:
        logger.warning("Discovery soft timeout for %s — saving progress", target_id)
        try:
            db.rollback()  # S264-0j — belt-and-braces: clean session before status write
        except Exception:
            pass
        try:
            session_obj = db.execute(
                select(DiscoverySession).where(DiscoverySession.id == sid)
            ).scalar_one_or_none()
            if session_obj:
                session_obj.status = "completed"
                session_obj.queries_executed = pipeline.budget.queries_used if pipeline else 0
                session_obj.pages_fetched = pipeline.budget.pages_used if pipeline else 0
                session_obj.leads_found = len(pipeline.seen_leads) if pipeline else 0
                session_obj.completed_at = datetime.now(timezone.utc)
                session_obj.error_message = "Completed with timeout (partial results)"
                db.commit()
            if pipeline and pipeline.seen_leads:
                auto_ingest_leads.delay(target_id, session_id, workspace_id)
            publish_event("discovery.timeout", {
                "workspace_id": workspace_id, "target_id": target_id,
                "session_id": session_id,
            })
        except Exception:
            logger.exception("Failed to save discovery progress on timeout")

    except Exception as e:
        logger.exception("Discovery failed for %s: %s", target_id, e)
        # S264-0j — a DB error (e.g. CheckViolation) aborts the txn; the status
        # write below MUST run on a clean session or it silently fails ("current
        # transaction is aborted") and the session is stranded at 'running' forever.
        # Rollback first, and never swallow a failure here again (log it).
        try:
            db.rollback()
        except Exception:
            pass
        try:
            session_obj = db.execute(
                select(DiscoverySession).where(DiscoverySession.id == uuid.UUID(session_id))
            ).scalar_one_or_none()
            if session_obj:
                session_obj.status = "error"
                session_obj.error_message = str(e)[:500]
                session_obj.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            logger.exception("S264-0j: failed to mark discovery session %s as error", session_id)

        publish_event("discovery.error", {
            "workspace_id": workspace_id,
            "target_id": target_id,
            "session_id": session_id,
            "error": str(e)[:200],
        })
    finally:
        db.close()


# ═══════════════════════════════════════════════
# Auto-Ingest + Phase A.5 Targeted Rescan
# ═══════════════════════════════════════════════

AUTO_INGEST_CONFIG = {
    "max_ingest_per_session": 5,
    "rules": {
        "username":     {"min_confidence": 0.75, "trigger_rescan": True},
        "email":        {"min_confidence": 0.80, "trigger_rescan": True},
        "name":         {"min_confidence": 0.80, "trigger_rescan": False},
        "organization": {"min_confidence": 0.85, "trigger_rescan": False},
        "url":          {"min_confidence": 0.85, "trigger_rescan": False},
        "document":     {"min_confidence": 0.90, "trigger_rescan": False},
        "mention":      {"min_confidence": 0.90, "trigger_rescan": False},
        # S264-0 AR-0 — corporate person resolved from business press, company-anchored.
        "corporate_person": {"min_confidence": 0.60, "trigger_rescan": False},
    },
}

PHASE_A5_MODULES = {
    "username": ["holehe", "sherlock", "social_enricher", "username_hunter", "scraper_engine"],
    "email": ["email_validator", "emailrep", "holehe", "hibp", "gravatar", "epieos"],
}

_LEAD_TYPE_TO_CATEGORY = {
    "username": "social_account", "email": "metadata", "name": "identity",
    "organization": "identity", "url": "metadata", "document": "metadata", "mention": "metadata",
    # S264-0 — 'corporate' ∈ finding_classifier.ENTITY_CATEGORIES → entity/corroborating tier.
    "corporate_person": "corporate",
}

_LEAD_TYPE_TO_INDICATOR = {
    "username": "username", "email": "email", "name": "name",
    "organization": "organization", "url": "url", "document": "url", "mention": "text",
    "corporate_person": "name",
}


def _localpart_binds(target_id, db, resolved_name: str) -> bool:
    """S264-0 local-part binding + S264-0i typo-tolerant fallback.

    eric@ → 'eric' ∈ 'Eric Lox' (exact). ekatarina@ → 'ekatarina' ~ 'Ekaterina'
    (typo, len≥6 only). Short names stay EXACT-only: ratio cannot tell a real typo
    from a different name on short tokens (ekatarina/ekaterina = eric/erica = 0.889),
    so the LENGTH FLOOR — not the ratio — is the guard against the confident-wrong
    direction. Same first char + ratio≥0.85 on top. Thresholds are hard-coded on
    purpose (an ENV knob would invite loosening the guard)."""
    try:
        from api.models.target import Target
        from difflib import SequenceMatcher
        email = db.execute(select(Target.email).where(Target.id == target_id)).scalar_one_or_none() or ""
        local = email.split("@", 1)[0].lower()
        local_tokens = {t for t in re.split(r"[._\-]+", local) if len(t) >= 2}
        name_tokens = {t.lower() for t in (resolved_name or "").split() if len(t) >= 2}

        if local_tokens & name_tokens:                 # exact — unchanged, wins first
            return True

        for lt in local_tokens:                        # typo fallback — long tokens only
            if len(lt) < 6:
                continue
            for nt in name_tokens:
                if len(nt) < 6 or lt[0] != nt[0]:
                    continue
                if SequenceMatcher(None, lt, nt).ratio() >= 0.85:
                    return True
        return False
    except Exception:
        return False


@celery_app.task(
    name="api.tasks.web_discovery.auto_ingest_leads",
    bind=True,
    soft_time_limit=120,
    time_limit=180,
)
def auto_ingest_leads(self, target_id: str, session_id: str, workspace_id: str):
    """Auto-ingest high-confidence discovery leads as findings + Phase A.5 rescan."""
    db = get_sync_session()
    try:
        from api.models.discovery import DiscoveryLead, DiscoveryEvent
        from api.models.finding import Finding
        from api.models.scan import Scan

        sid = uuid.UUID(session_id)
        tid = uuid.UUID(target_id)
        wid = uuid.UUID(workspace_id)

        leads = db.execute(
            select(DiscoveryLead).where(
                DiscoveryLead.session_id == sid,
                DiscoveryLead.status == "new",
            ).order_by(DiscoveryLead.confidence.desc())
        ).scalars().all()

        # S264-0c — seed email domain (for anchor recognition in the aggregator).
        from api.models.target import Target as _Tgt
        _seed_email = (db.execute(select(_Tgt.email).where(_Tgt.id == tid)).scalar_one_or_none() or "").lower()
        _seed_domain = _seed_email.split("@", 1)[1] if "@" in _seed_email else ""

        # S264-0c — findings.scan_id is NOT NULL, but auto-ingest set no scan_id
        # (latent bug — discovery findings could never insert). Anchor them to the
        # target's latest scan. No scan → cannot persist findings; bail cleanly.
        _scan_id = db.execute(
            select(Scan.id).where(Scan.target_id == tid).order_by(Scan.created_at.desc()).limit(1)
        ).scalar_one_or_none()
        if not _scan_id:
            logger.warning("auto_ingest: target %s has no scan — cannot persist findings", target_id)
            db.commit()
            return {"ingested_count": 0, "rescan_targets": 0, "reason": "no_scan"}

        # S264-0 — corroboration map for corporate_person: group by normalized name,
        # count DISTINCT source domains. 1 source → entity (moderate); 2+ independent
        # → corroborating (high) in the typed-confidence layer.
        from urllib.parse import urlparse
        _person_sources = {}
        for _l in leads:
            if _l.lead_type == "corporate_person":
                nm = (_l.lead_value or "").strip().lower()
                dom = (urlparse(_l.source_url or "").netloc or "").lower().lstrip("www.")
                if nm and dom:
                    _person_sources.setdefault(nm, set()).add(dom)

        ingested = []
        rescan_targets = []

        for lead in leads:
            if len(ingested) >= AUTO_INGEST_CONFIG["max_ingest_per_session"]:
                break

            rule = AUTO_INGEST_CONFIG["rules"].get(lead.lead_type)
            if not rule or lead.confidence < rule["min_confidence"]:
                continue

            # Dedup: check if already a finding
            existing = db.execute(
                select(Finding).where(
                    Finding.target_id == tid,
                    Finding.indicator_value == lead.lead_value,
                    Finding.module == "discovery",
                )
            ).scalar_one_or_none()
            if existing:
                continue

            # Create finding
            title = f"Discovered {lead.lead_type}: {lead.lead_value}"
            data = {
                "lead_value": lead.lead_value,
                "lead_type": lead.lead_type,
                "confidence": lead.confidence,
                "source_url": lead.source_url,
                "extractor_type": lead.extractor_type,
                "discovery_chain": lead.discovery_chain,
                "auto_ingested": True,
                "session_id": session_id,
            }
            xv_count = 0
            xv_sources = None
            # S264-0 — corporate_person lands in the entity/corroborating tier.
            if lead.lead_type == "corporate_person":
                domains = sorted(_person_sources.get((lead.lead_value or "").strip().lower(), set()))
                xv_count = len(domains)
                xv_sources = [{"source": d, "kind": "press"} for d in domains]
                company = (lead.source_snippet or "").strip()  # extractor stored company in context
                data.update({
                    # S264-0c — name in data so the aggregator name-collector surfaces
                    # it (it reads data["name"], NOT indicator_value); seed_domain so
                    # anchor_corroborated recognises the bound resolution.
                    "name": lead.lead_value,
                    "company": company,
                    "match_confidence": lead.confidence,
                    "pattern": "press_caption",
                    "source_kind": "press",
                    "source_domains": domains,
                    "source_urls": [u for u in (
                        sorted({_l.source_url for _l in leads
                                if _l.lead_type == "corporate_person"
                                and (_l.lead_value or "").strip().lower() == (lead.lead_value or "").strip().lower()
                                and _l.source_url})
                    )],
                    "seed_domain": _seed_domain,
                    # local-part first-name binding (e.g. eric@ → "Eric Lox")
                    "email_pattern_match": _localpart_binds(tid, db, lead.lead_value),
                })
                title = f"Corporate identity: {lead.lead_value}" + (f" ({company})" if company else "")
            finding = Finding(
                workspace_id=wid,
                target_id=tid,
                scan_id=_scan_id,
                module="discovery",
                layer=3,
                category=_LEAD_TYPE_TO_CATEGORY.get(lead.lead_type, "metadata"),
                severity="info",
                title=title[:255],
                description=(
                    f"Auto-ingested from web discovery (confidence: {lead.confidence:.0%}). "
                    f"Source: {lead.source_url or 'unknown'}"
                ),
                data=data,
                indicator_value=lead.lead_value[:500],
                indicator_type=_LEAD_TYPE_TO_INDICATOR.get(lead.lead_type, "text"),
                cross_verification_count=xv_count,
                cross_verification_sources=xv_sources,
                verified=False,
            )
            db.add(finding)
            lead.status = "ingested"
            ingested.append(lead)

            if rule["trigger_rescan"]:
                rescan_targets.append((lead.lead_type, lead.lead_value))

            # Persist ingest event
            db.add(DiscoveryEvent(
                session_id=sid,
                event_type="auto_ingest",
                payload={
                    "lead_type": lead.lead_type, "lead_value": lead.lead_value,
                    "confidence": lead.confidence,
                    "trigger_rescan": rule["trigger_rescan"],
                },
            ))

        db.commit()

        publish_event("discovery.auto_ingest", {
            "workspace_id": workspace_id, "target_id": target_id,
            "session_id": session_id,
            "ingested_count": len(ingested), "rescan_targets": len(rescan_targets),
        })

        logger.info("Auto-ingest for %s: %d leads ingested, %d rescan targets",
                     target_id, len(ingested), len(rescan_targets))

        # Phase A.5: targeted rescan for new usernames/emails
        if rescan_targets:
            _launch_phase_a5(target_id, workspace_id, rescan_targets, db)
        elif ingested:
            # No rescan but new findings — re-finalize to update graph/scores
            from api.tasks.scan_orchestrator import _full_refinalize
            _full_refinalize(target_id, workspace_id, db)

    except Exception as e:
        logger.exception("Auto-ingest failed for %s: %s", target_id, e)
    finally:
        db.close()


def _launch_phase_a5(target_id, workspace_id, rescan_targets, db):
    """Launch Phase A.5 targeted mini-scan for discovered identifiers."""
    from api.models.scan import Scan
    from api.tasks.scan_orchestrator import launch_scan

    modules_needed = set()
    for target_type, _ in rescan_targets:
        modules_needed.update(PHASE_A5_MODULES.get(target_type, []))

    if not modules_needed:
        return

    scan = Scan(
        workspace_id=uuid.UUID(workspace_id),
        target_id=uuid.UUID(target_id),
        modules=list(modules_needed),
        module_progress={mod: "queued" for mod in modules_needed},
        scan_type="discovery_rescan",
    )
    db.add(scan)
    db.commit()

    launch_scan.delay(str(scan.id))

    publish_event("discovery.rescan_launched", {
        "workspace_id": workspace_id, "target_id": target_id,
        "scan_id": str(scan.id),
        "modules": list(modules_needed),
        "rescan_targets": [{"type": t, "value": v} for t, v in rescan_targets],
    })

    logger.info("Phase A.5 launched for %s: %d modules, %d targets",
                 target_id, len(modules_needed), len(rescan_targets))
