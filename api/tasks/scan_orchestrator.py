import logging
import uuid
from datetime import datetime, timezone

from celery import chord
from sqlalchemy import select

from api.tasks import celery_app
from api.tasks.utils import get_sync_session

logger = logging.getLogger(__name__)


@celery_app.task(name="api.tasks.scan_orchestrator.launch_scan", bind=True)
def launch_scan(self, scan_id: str):
    from api.models.scan import Scan
    from api.models.target import Target

    session = get_sync_session()
    try:
        scan = session.execute(select(Scan).where(Scan.id == uuid.UUID(scan_id))).scalar_one_or_none()
        if not scan:
            return {"error": "Scan not found"}

        scan.status = "running"
        scan.started_at = datetime.now(timezone.utc)
        session.commit()

        try:
            from api.services.event_bus import publish_event
            publish_event("scan.started", {
                "target_id": str(scan.target_id),
                "scan_id": str(scan_id),
                "workspace_id": str(scan.workspace_id),
            })
        except Exception:
            pass

        target = session.execute(select(Target).where(Target.id == scan.target_id)).scalar_one_or_none()
        if not target:
            scan.status = "failed"
            scan.error_log = "Target not found"
            session.commit()
            return {"error": "Target not found"}

        email = target.email
        modules = scan.modules or []

        if not modules:
            scan.status = "completed"
            scan.completed_at = datetime.now(timezone.utc)
            session.commit()
            return {"status": "no modules"}

        scan.module_progress = {mod: "queued" for mod in modules}
        session.commit()

        from api.tasks.module_tasks import run_module
        module_tasks = [run_module.s(scan_id, mod, email) for mod in modules]
        callback = finalize_scan.si(scan_id)
        chord(module_tasks)(callback)

        return {"status": "launched", "modules": modules}
    except Exception:
        session.rollback()
        logger.exception("launch_scan failed for %s", scan_id)
        raise
    finally:
        session.close()


@celery_app.task(name="api.tasks.scan_orchestrator.finalize_scan")
def finalize_scan(scan_id: str):
    from api.models.scan import Scan
    from api.models.target import Target
    from api.models.finding import Finding
    from sqlalchemy import func

    session = get_sync_session()
    try:
        scan = session.execute(select(Scan).where(Scan.id == uuid.UUID(scan_id))).scalar_one_or_none()
        if not scan:
            return

        # Count findings
        total_findings = session.execute(
            select(func.count()).select_from(Finding).where(Finding.scan_id == scan.id)
        ).scalar() or 0

        scan.status = "completed"
        scan.completed_at = datetime.now(timezone.utc)
        scan.findings_count = total_findings
        if scan.started_at:
            duration = datetime.now(timezone.utc) - scan.started_at
            scan.duration_ms = int(duration.total_seconds() * 1000)

        # Update target
        target = session.execute(select(Target).where(Target.id == scan.target_id)).scalar_one_or_none()
        if target:
            target.status = "completed"
            target.last_scanned = datetime.now(timezone.utc)
            if not target.first_scanned:
                target.first_scanned = datetime.now(timezone.utc)

        session.commit()

        # Cross-verify findings from multiple sources (boosts confidence)
        try:
            from api.services.layer4.source_scoring import cross_verify_findings
            cv_count = cross_verify_findings(scan.target_id, session)
            if cv_count:
                logger.info("Cross-verified %d findings for target %s", cv_count, scan.target_id)
        except Exception:
            logger.exception("Cross-verification failed for target %s", scan.target_id)

        # Compute exposure score (separate transaction so scan status is visible)
        try:
            from api.services.layer4.score_engine import compute_score
            score, threat, breakdown = compute_score(scan.target_id, session)
            logger.info("Score for target %s: exposure=%d, threat=%d", scan.target_id, score, threat)
        except Exception:
            logger.exception("Score computation failed for target %s", scan.target_id)
            # Ensure score is at least 0 on failure
            if target:
                target.exposure_score = target.exposure_score or 0
                target.score_breakdown = target.score_breakdown or {}
                session.commit()

        # Build identity graph (separate transaction)
        try:
            from api.services.layer4.graph_builder import build_graph
            build_graph(scan.target_id, scan.workspace_id, session)
        except Exception:
            logger.exception("Graph build failed for target %s", scan.target_id)

        # Propagate confidence through identity graph (PageRank)
        try:
            from api.services.layer4.confidence_propagator import propagate_confidence
            node_scores = propagate_confidence(scan.target_id, scan.workspace_id, session)
            if node_scores:
                logger.info("Confidence propagated: %d nodes scored for target %s",
                            len(node_scores), scan.target_id)
        except Exception:
            logger.exception("Confidence propagation failed for target %s", scan.target_id)

        # Aggregate profile data
        try:
            from api.services.layer4.profile_aggregator import aggregate_profile
            aggregate_profile(scan.target_id, scan.workspace_id, session)
        except Exception:
            logger.exception("Profile aggregation failed for target %s", scan.target_id)

        try:
            from api.services.event_bus import publish_event
            publish_event("target.updated", {
                "target_id": str(scan.target_id),
                "workspace_id": str(scan.workspace_id),
            })
        except Exception:
            pass

        # Identity enrichment — re-query with discovered name
        try:
            from api.services.layer4.identity_enricher import enrich_identity
            target = session.execute(select(Target).where(Target.id == scan.target_id)).scalar_one_or_none()
            if target:
                profile = dict(target.profile_data or {})
                est = profile.get("identity_estimation", {})
                if not est.get("gender") or not est.get("age"):
                    updated_est = enrich_identity(profile, target.email)
                    if updated_est and (updated_est.get("gender") or updated_est.get("age")):
                        profile["identity_estimation"] = updated_est
                        target.profile_data = profile
                        session.commit()
                        logger.info("Identity enriched for %s with discovered name", target.email)
        except Exception:
            logger.exception("Identity enrichment failed for target %s", scan.target_id)

        # Load workspace plan + user role for feature gating
        from api.models.workspace import Workspace
        from api.models.user import UserWorkspace
        from api.services.plan_config import check_feature
        ws = session.execute(select(Workspace).where(Workspace.id == scan.workspace_id)).scalar_one_or_none()
        plan_name = ws.plan if ws else "free"
        # Get the role of the workspace owner (or first member) for bypass check
        uw = session.execute(
            select(UserWorkspace).where(UserWorkspace.workspace_id == scan.workspace_id).limit(1)
        ).scalar_one_or_none()
        ws_role = uw.role if uw else "user"

        # Cluster personas (plan-gated)
        if check_feature(plan_name, "persona_clustering", ws_role):
            try:
                from api.services.layer4.persona_engine import cluster_personas
                personas = cluster_personas(scan.target_id, scan.workspace_id, session)
                if personas:
                    profile = dict(target.profile_data or {})
                    profile["personas"] = personas
                    target.profile_data = profile
                    session.commit()
                    logger.info("Personas clustered for target %s: %d personas", scan.target_id, len(personas))
            except Exception:
                logger.exception("Persona clustering failed for target %s", scan.target_id)

        # Run intelligence analysis pipeline (plan-gated)
        if check_feature(plan_name, "intelligence_pipeline", ws_role):
            try:
                from api.services.layer4.analysis_pipeline import AnalysisPipeline
                pipeline = AnalysisPipeline()
                intel_count = pipeline.run(scan.target_id, scan.workspace_id, scan_id, session)
                if intel_count:
                    logger.info("Intelligence pipeline created %d findings for target %s", intel_count, scan.target_id)
                    # Update scan findings count with intelligence findings
                    scan.findings_count = (scan.findings_count or 0) + intel_count
                    session.commit()
            except Exception:
                logger.exception("Intelligence pipeline failed for target %s", scan.target_id)

        # Compute digital fingerprint
        try:
            from api.services.layer4.fingerprint_engine import FingerprintEngine
            from api.models.identity import Identity, IdentityLink

            # Deduplicate findings: latest per (module, title) — Python-side
            raw_findings = session.execute(
                select(Finding).where(Finding.target_id == scan.target_id)
            ).scalars().all()
            seen_fp = {}
            for f in raw_findings:
                key = (f.module, f.title)
                existing = seen_fp.get(key)
                if existing is None or (f.created_at and (not existing.created_at or f.created_at > existing.created_at)):
                    seen_fp[key] = f
            all_findings = list(seen_fp.values())
            all_identities = session.execute(
                select(Identity).where(Identity.target_id == scan.target_id)
            ).scalars().all()

            # Load identity links for eigenvalue computation
            identity_ids = [i.id for i in all_identities]
            all_links = []
            if identity_ids:
                all_links = session.execute(
                    select(IdentityLink).where(
                        IdentityLink.workspace_id == scan.workspace_id,
                    )
                ).scalars().all()
                id_set = set(identity_ids)
                all_links = [l for l in all_links if l.source_id in id_set or l.dest_id in id_set]

            fp_engine = FingerprintEngine()
            fingerprint = fp_engine.compute(
                all_findings, all_identities, target.profile_data, target.email,
                links=all_links,
            )

            # Save snapshot to history
            snapshot = {
                "hash": fingerprint["hash"],
                "score": fingerprint["score"],
                "risk_level": fingerprint["risk_level"],
                "axes": fingerprint["axes"],
                "raw_values": fingerprint["raw_values"],
                "label": fingerprint.get("label", ""),
                "scan_id": str(scan_id),
                "computed_at": fingerprint["computed_at"],
                "findings_count": len(all_findings),
            }
            history = list(target.fingerprint_history or [])
            history.append(snapshot)
            target.fingerprint_history = history[-50:]

            # Save current fingerprint in profile_data
            profile = dict(target.profile_data or {})
            profile["fingerprint"] = fingerprint
            target.profile_data = profile

            session.commit()
            logger.info(
                "Fingerprint %s (score=%d, %s) for target %s",
                fingerprint["hash"], fingerprint["score"],
                fingerprint["risk_level"], scan.target_id,
            )
        except Exception:
            logger.exception("Fingerprint computation failed for target %s", scan.target_id)

        # Publish scan.completed event for SSE
        try:
            from api.services.event_bus import publish_event
            target = session.execute(select(Target).where(Target.id == scan.target_id)).scalar_one_or_none()
            publish_event("scan.completed", {
                "target_id": str(scan.target_id),
                "scan_id": str(scan_id),
                "workspace_id": str(scan.workspace_id),
                "findings_count": scan.findings_count or 0,
                "exposure_score": target.exposure_score if target else 0,
                "threat_score": target.threat_score if target else 0,
            })
        except Exception:
            pass

    except Exception:
        session.rollback()
        logger.exception("finalize_scan failed for %s", scan_id)
        raise
    finally:
        session.close()
