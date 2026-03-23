import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from celery import chord
from sqlalchemy import select

from api.tasks import celery_app
from api.tasks.utils import get_sync_session

logger = logging.getLogger(__name__)


def _build_graph_context(target_id, workspace_id, session):
    from sqlalchemy import func as sa_func
    """Build the unified graph context after PageRank.

    Returns a dict that ALL downstream services can read.
    No service should query graph data independently after this.
    """
    from api.models.identity import Identity, IdentityLink

    # Debug: verify links exist at start of graph_context build
    link_count = session.execute(
        select(sa_func.count()).select_from(IdentityLink).where(
            IdentityLink.workspace_id == workspace_id,
        )
    ).scalar()
    logger.info("GRAPH_DEBUG: %d identity_links at start of _build_graph_context for target %s",
                link_count, target_id)

    # Load all nodes with propagated confidence
    identities = session.execute(
        select(Identity).where(
            Identity.target_id == target_id,
            Identity.workspace_id == workspace_id,
        )
    ).scalars().all()

    id_set = set(i.id for i in identities)

    # Load all edges
    links = session.execute(
        select(IdentityLink).where(
            IdentityLink.workspace_id == workspace_id,
        )
    ).scalars().all()
    relevant_links = [l for l in links if l.source_id in id_set and l.dest_id in id_set]

    # 1. Node scores (from PageRank — already updated in DB)
    node_scores = {i.id: i.confidence or 0.0 for i in identities}

    # 2. Node map: value → {type, confidence, platform, id}
    node_map = {}
    for i in identities:
        key = i.value.lower().strip() if i.value else ""
        if key:
            if key not in node_map or (i.confidence or 0) > node_map[key].get("confidence", 0):
                node_map[key] = {
                    "id": i.id,
                    "type": i.type,
                    "confidence": i.confidence or 0.0,
                    "platform": i.platform,
                    "value": i.value,
                }

    # 3. Transition matrix: node_id → {dest_id: transition_probability}
    outgoing = defaultdict(list)
    for l in relevant_links:
        outgoing[l.source_id].append((l.dest_id, l.confidence or 0.5))

    transition_matrix = {}
    for src_id, dests in outgoing.items():
        total_weight = sum(w for _, w in dests)
        if total_weight > 0:
            transition_matrix[src_id] = {
                dest_id: round(w / total_weight, 4)
                for dest_id, w in dests
            }

    # 4. Graph clusters (connected components via BFS)
    visited = set()
    clusters = []

    # Only use STRONG edges for clustering (not associated_with/located_in)
    # associated_with = catch-all links that connect everything to email anchor
    # Good for PageRank propagation, toxic for persona clustering
    WEAK_EDGE_TYPES = {"associated_with", "located_in"}

    adj = defaultdict(set)
    for l in relevant_links:
        if getattr(l, "link_type", None) not in WEAK_EDGE_TYPES:
            adj[l.source_id].add(l.dest_id)
            adj[l.dest_id].add(l.source_id)

    for start_id in id_set:
        if start_id in visited:
            continue
        component = set()
        queue = [start_id]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            component.add(node)
            for neighbor in adj.get(node, []):
                if neighbor not in visited and neighbor in id_set:
                    queue.append(neighbor)

        if len(component) >= 2:
            cluster_conf = sum(node_scores.get(n, 0) for n in component) / len(component)
            internal_edges = [l for l in relevant_links
                             if l.source_id in component and l.dest_id in component]
            max_edges = len(component) * (len(component) - 1)
            density = len(internal_edges) / max_edges if max_edges > 0 else 0

            type_counts = defaultdict(int)
            for n in component:
                for i in identities:
                    if i.id == n:
                        type_counts[i.type] += 1

            clusters.append({
                "nodes": list(component),
                "node_count": len(component),
                "confidence": round(cluster_conf, 4),
                "density": round(density, 4),
                "internal_edges": len(internal_edges),
                "dominant_type": max(type_counts, key=type_counts.get) if type_counts else "unknown",
            })

    clusters.sort(key=lambda c: c["confidence"], reverse=True)

    return {
        "node_scores": node_scores,
        "node_map": node_map,
        "transition_matrix": transition_matrix,
        "clusters": clusters,
        "identities": identities,
        "links": relevant_links,
        "edge_count": len(relevant_links),
    }


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
        logger.info("PIPELINE[%s]: cross_verify done", scan.target_id)

        # Build identity graph FIRST (needed for graph_context)
        try:
            from api.services.layer4.graph_builder import build_graph
            build_graph(scan.target_id, scan.workspace_id, session)
        except Exception:
            logger.exception("Graph build failed for target %s", scan.target_id)
        logger.info("PIPELINE[%s]: graph_builder done", scan.target_id)

        # Propagate confidence through identity graph (PageRank)
        node_scores = None
        try:
            from api.services.layer4.confidence_propagator import propagate_confidence
            node_scores = propagate_confidence(scan.target_id, scan.workspace_id, session)
            if node_scores:
                logger.info("Confidence propagated: %d nodes scored for target %s",
                            len(node_scores), scan.target_id)
        except Exception:
            logger.exception("Confidence propagation failed for target %s", scan.target_id)
        logger.info("PIPELINE[%s]: pagerank done — %d nodes",
                    scan.target_id, len(node_scores) if node_scores else 0)

        # Build graph_context — the unified intelligence layer
        graph_context = None
        try:
            graph_context = _build_graph_context(scan.target_id, scan.workspace_id, session)
            logger.info("Graph context built: %d nodes, %d edges, %d clusters",
                        len(graph_context.get("node_scores", {})),
                        graph_context.get("edge_count", 0),
                        len(graph_context.get("clusters", [])))
        except Exception:
            logger.exception("Graph context build failed — downstream services will use fallback")
        if graph_context:
            logger.info("PIPELINE[%s]: graph_context — %d nodes, %d edges, %d clusters",
                        scan.target_id,
                        len(graph_context.get("node_scores", {})),
                        graph_context.get("edge_count", 0),
                        len(graph_context.get("clusters", [])))

        # Compute exposure score (now WITH graph_context)
        try:
            from api.services.layer4.score_engine import compute_score
            score, threat, breakdown = compute_score(scan.target_id, session, graph_context=graph_context)
            logger.info("Score for target %s: exposure=%d, threat=%d", scan.target_id, score, threat)
        except Exception:
            logger.exception("Score computation failed for target %s", scan.target_id)
            # Ensure score is at least 0 on failure
            if target:
                target.exposure_score = target.exposure_score or 0
                target.score_breakdown = target.score_breakdown or {}
                session.commit()
        logger.info("PIPELINE[%s]: score — exposure=%s, threat=%s",
                    scan.target_id,
                    getattr(target, 'exposure_score', '?') if target else '?',
                    getattr(target, 'threat_score', '?') if target else '?')

        # Aggregate profile data (with graph_context)
        try:
            from api.services.layer4.profile_aggregator import aggregate_profile
            aggregate_profile(scan.target_id, scan.workspace_id, session, graph_context=graph_context)
        except Exception:
            logger.exception("Profile aggregation failed for target %s", scan.target_id)
        logger.info("PIPELINE[%s]: profile_aggregator done", scan.target_id)

        # Force bio rejection for Telegram slogans and similar noise
        try:
            target = session.execute(select(Target).where(Target.id == scan.target_id)).scalar_one_or_none()
            if target:
                profile = dict(target.profile_data or {})
                bio = profile.get("bio", "")
                _BIO_REJECT = [
                    "you can contact", "contact @", "right away",
                    "fast. secure. powerful", "a new era of messaging",
                    "telegram is a cloud", "telegram messenger",
                    "pure instant messaging", "simple, fast, secure",
                ]
                if bio and any(p in bio.lower() for p in _BIO_REJECT):
                    profile["bio"] = None
                    target.profile_data = profile
                    session.commit()
        except Exception:
            logger.exception("Bio cleanup failed for target %s", scan.target_id)

        # Force blacklist check on target.display_name
        try:
            from api.services.layer4.profile_aggregator import _load_blacklist, _is_valid_name_db
            target = session.execute(select(Target).where(Target.id == scan.target_id)).scalar_one_or_none()
            if target:
                blacklist = _load_blacklist(session)
                profile = dict(target.profile_data or {})
                primary = profile.get("primary_name", "")

                if primary and _is_valid_name_db(primary, blacklist):
                    target.display_name = primary
                elif target.display_name and not _is_valid_name_db(target.display_name, blacklist):
                    target.display_name = None

                session.commit()
        except Exception:
            logger.exception("Display name validation failed for %s", scan.target_id)

        # Store quick_teaser in profile_data (for landing page freemium flow)
        try:
            target = session.execute(select(Target).where(Target.id == scan.target_id)).scalar_one_or_none()
            if target:
                all_scan_findings = session.execute(
                    select(Finding).where(Finding.scan_id == scan.id)
                    .order_by(Finding.severity)
                ).scalars().all()
                sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
                sorted_findings = sorted(all_scan_findings, key=lambda f: sev_order.get(f.severity, 5))
                profile = dict(target.profile_data or {})
                profile["quick_teaser"] = {
                    "top_findings": [
                        {"title": f.title, "severity": f.severity, "category": f.category}
                        for f in sorted_findings[:3]
                    ],
                    "total_findings": len(all_scan_findings),
                }
                target.profile_data = profile
                session.commit()
        except Exception:
            logger.exception("Quick teaser generation failed for target %s", scan.target_id)

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
                # Re-query if gender/age missing OR nationalities are low-confidence garbage
                max_nat_prob = max(
                    (n.get("probability", 0) for n in est.get("nationalities", [{}]) if isinstance(n, dict)),
                    default=0,
                )
                should_enrich = (
                    not est.get("gender")
                    or not est.get("age")
                    or max_nat_prob < 0.15
                )
                if should_enrich:
                    updated_est = enrich_identity(profile, target.email)
                    if updated_est and (updated_est.get("gender") or updated_est.get("age") or updated_est.get("nationalities")):
                        profile["identity_estimation"] = updated_est
                        target.profile_data = profile
                        session.commit()
                        logger.info("Identity enriched for %s with discovered name", target.email)
        except Exception:
            logger.exception("Identity enrichment failed for target %s", scan.target_id)

        # Load workspace plan + user role for feature gating
        try:
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
        except Exception:
            logger.exception("Failed to load workspace plan for target %s", scan.target_id)
            plan_name = "free"
            ws_role = "user"
            from api.services.plan_config import check_feature

        # Cluster personas (plan-gated)
        personas = []
        if check_feature(plan_name, "persona_clustering", ws_role):
            try:
                from api.services.layer4.persona_engine import cluster_personas
                personas = cluster_personas(scan.target_id, scan.workspace_id, session, graph_context=graph_context)
                if personas:
                    profile = dict(target.profile_data or {})
                    profile["personas"] = personas
                    target.profile_data = profile
                    session.commit()
                    logger.info("Personas clustered for target %s: %d personas", scan.target_id, len(personas))
            except Exception:
                logger.exception("Persona clustering failed for target %s", scan.target_id)
            logger.info("PIPELINE[%s]: personas — %d",
                        scan.target_id, len(personas) if personas else 0)

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
                links=all_links, graph_context=graph_context,
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

            # Store life timeline from fingerprint timestamp harvesting
            timeline = fingerprint.get("timeline_events", [])
            if timeline:
                profile["life_timeline"] = timeline

            # Store graph_context summary for frontend
            if graph_context:
                ns = graph_context.get("node_scores", {})
                gc = graph_context.get("clusters", [])
                profile["graph_context_summary"] = {
                    "cluster_count": len(gc),
                    "total_nodes": len(ns),
                    "total_edges": graph_context.get("edge_count", 0),
                    "top_cluster_confidence": gc[0]["confidence"] if gc else 0,
                    "avg_node_confidence": round(sum(ns.values()) / len(ns), 4) if ns else 0,
                }

            target.profile_data = profile

            session.commit()
            logger.info(
                "Fingerprint %s (score=%d, %s) for target %s",
                fingerprint["hash"], fingerprint["score"],
                fingerprint["risk_level"], scan.target_id,
            )
        except Exception:
            logger.exception("Fingerprint computation failed for target %s", scan.target_id)
        logger.info("PIPELINE[%s]: fingerprint done", scan.target_id)

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
