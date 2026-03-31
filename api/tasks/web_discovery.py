"""Celery task for Phase C — Web Discovery."""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from api.tasks import celery_app
from api.tasks.utils import get_sync_session
from api.services.event_bus import publish_event

logger = logging.getLogger(__name__)


@celery_app.task(
    name="api.tasks.web_discovery.run_discovery",
    bind=True,
    soft_time_limit=120,
    time_limit=180,
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

    except Exception as e:
        logger.exception("Discovery failed for %s: %s", target_id, e)
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
            pass

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
    },
}

PHASE_A5_MODULES = {
    "username": ["holehe", "sherlock", "social_enricher", "username_hunter", "scraper_engine"],
    "email": ["email_validator", "emailrep", "holehe", "hibp", "gravatar", "epieos"],
}

_LEAD_TYPE_TO_CATEGORY = {
    "username": "social_account", "email": "metadata", "name": "identity",
    "organization": "identity", "url": "metadata", "document": "metadata", "mention": "metadata",
}

_LEAD_TYPE_TO_INDICATOR = {
    "username": "username", "email": "email", "name": "name",
    "organization": "organization", "url": "url", "document": "url", "mention": "text",
}


@celery_app.task(
    name="api.tasks.web_discovery.auto_ingest_leads",
    bind=True,
    soft_time_limit=60,
    time_limit=90,
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
            finding = Finding(
                workspace_id=wid,
                target_id=tid,
                module="discovery",
                layer=3,
                category=_LEAD_TYPE_TO_CATEGORY.get(lead.lead_type, "metadata"),
                severity="info",
                title=title[:255],
                description=(
                    f"Auto-ingested from web discovery (confidence: {lead.confidence:.0%}). "
                    f"Source: {lead.source_url or 'unknown'}"
                ),
                data={
                    "lead_value": lead.lead_value,
                    "lead_type": lead.lead_type,
                    "confidence": lead.confidence,
                    "source_url": lead.source_url,
                    "extractor_type": lead.extractor_type,
                    "discovery_chain": lead.discovery_chain,
                    "auto_ingested": True,
                    "session_id": session_id,
                },
                indicator_value=lead.lead_value[:500],
                indicator_type=_LEAD_TYPE_TO_INDICATOR.get(lead.lead_type, "text"),
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
