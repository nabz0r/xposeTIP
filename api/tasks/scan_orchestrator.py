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
    WEAK_EDGE_TYPES = {"associated_with", "located_in", "mentioned_in", "listed_on", "officer_of"}

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

        # Pass 1.5 — Username expansion (re-scan discovered usernames)
        try:
            from api.services.layer4.username_expander import expand_usernames
            target = session.execute(select(Target).where(Target.id == scan.target_id)).scalar_one_or_none()
            pass15_result = expand_usernames(
                scan.target_id, scan.workspace_id, session,
                scan_id=scan.id, email=target.email if target else None,
            )
            if pass15_result.get("findings_created", 0) > 0:
                logger.info(
                    "Pass 1.5 expanded %d usernames → %d new findings for target %s",
                    len(pass15_result.get("usernames_selected", [])),
                    pass15_result["findings_created"], scan.target_id,
                )
        except Exception:
            logger.exception("Pass 1.5 username expansion failed for %s", scan.target_id)

        # Pass 2 — Public exposure enrichment (name-based scrapers)
        try:
            from api.services.layer4.public_exposure_enricher import enrich_public_exposure
            pass2_result = enrich_public_exposure(scan.target_id, session, scan_id=scan.id)
            if pass2_result.get("findings_created", 0) > 0:
                session.commit()  # Persist pass 2 findings + graph edges
                logger.info(
                    "Pass 2 created %d public exposure findings for target %s",
                    pass2_result["findings_created"], scan.target_id,
                )
        except Exception:
            logger.exception("Pass 2 public exposure enrichment failed for %s", scan.target_id)

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

                # Ground truth: operator-set country overrides nationality estimation
                if target and target.country_code:
                    profile = dict(target.profile_data or {})
                    est = profile.get("identity_estimation", {})
                    if est and not est.get("nationality_override"):
                        est["nationality_override"] = target.country_code
                        profile["identity_estimation"] = est
                        target.profile_data = profile
                        session.commit()
                        logger.info("Nationality override set to %s for %s", target.country_code, target.email)
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
                personas = cluster_personas(scan.target_id, scan.workspace_id, session, graph_context=graph_context, profile_data=dict(target.profile_data or {}))
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
                country_code=target.country_code,
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


@celery_app.task(name="api.tasks.scan_orchestrator.deep_username_scan", bind=True)
def deep_username_scan(self, target_id: str, workspace_id: str, username: str, scan_id: str = None):
    """Operator-triggered deep scan of a single username.

    Runs all username-capable scrapers, then re-finalizes the target
    (graph, PageRank, profile, fingerprint) to integrate new findings.
    """
    from api.services.layer4.username_expander import scan_single_username

    session = get_sync_session()
    try:
        result = scan_single_username(
            uuid.UUID(target_id),
            uuid.UUID(workspace_id),
            session,
            username=username,
            scan_id=uuid.UUID(scan_id) if scan_id else None,
        )

        # If new findings were created, re-finalize to rebuild graph + profile
        if result.get("findings_created", 0) > 0:
            logger.info("Deep scan '%s' created %d findings — full re-finalize target %s",
                         username, result["findings_created"], target_id)
            _full_refinalize(target_id, workspace_id, session)
        else:
            logger.info("Deep scan '%s' — no new findings for target %s", username, target_id)

        return result

    except Exception:
        logger.exception("deep_username_scan task failed for '%s' target %s", username, target_id)
        raise
    finally:
        session.close()


@celery_app.task(name="api.tasks.scan_orchestrator.deep_indicator_scan", bind=True)
def deep_indicator_scan(self, target_id: str, workspace_id: str,
                        indicator_type: str, indicator_value: str,
                        scan_id: str = None, _cascade_depth: int = 0):
    """Operator-triggered deep scan of any indicator type.

    Runs all scrapers matching the indicator_type, then re-finalizes.
    Cascade depth=0 triggers cross-type discovery; depth>=1 skips cascade.
    """
    from api.services.layer4.username_expander import scan_single_indicator

    session = get_sync_session()
    try:
        result = scan_single_indicator(
            uuid.UUID(target_id),
            uuid.UUID(workspace_id),
            session,
            indicator_type=indicator_type,
            indicator_value=indicator_value,
            scan_id=uuid.UUID(scan_id) if scan_id else None,
        )

        # Cascade: extract cross-type indicators from new findings (depth=0 only)
        if result.get("findings_created", 0) > 0 and _cascade_depth < 1:
            cascades = _extract_cascade_indicators(
                target_id, workspace_id, indicator_type, indicator_value, session
            )
            for cascade_type, cascade_value in cascades:
                logger.info("CASCADE: %s '%s' -> %s '%s'",
                             indicator_type, indicator_value,
                             cascade_type, cascade_value)
                cascade_result = scan_single_indicator(
                    uuid.UUID(target_id), uuid.UUID(workspace_id), session,
                    indicator_type=cascade_type,
                    indicator_value=cascade_value,
                    scan_id=uuid.UUID(scan_id) if scan_id else None,
                )
                result["findings_created"] += cascade_result.get("findings_created", 0)

        if result.get("findings_created", 0) > 0:
            logger.info("Deep %s scan '%s' created %d findings — full re-finalize",
                         indicator_type, indicator_value, result["findings_created"])
            _full_refinalize(target_id, workspace_id, session)
        else:
            logger.info("Deep %s scan '%s' — no new findings", indicator_type, indicator_value)

        return result

    except Exception:
        logger.exception("deep_indicator_scan failed for %s '%s'", indicator_type, indicator_value)
        raise
    finally:
        session.close()


def _extract_cascade_indicators(target_id_str, workspace_id_str,
                                source_type, source_value, session):
    """Extract cross-type indicators from deep scan findings for cascade."""
    from api.models.finding import Finding
    from api.models.identity import Identity

    target_id = uuid.UUID(target_id_str) if isinstance(target_id_str, str) else target_id_str
    workspace_id = uuid.UUID(workspace_id_str) if isinstance(workspace_id_str, str) else workspace_id_str

    deep_findings = session.execute(
        select(Finding).where(Finding.target_id == target_id)
    ).scalars().all()
    deep_findings = [f for f in deep_findings if f.data and isinstance(f.data, dict)
                     and f.data.get("pass") == "deep"]

    existing = set()
    identities = session.execute(
        select(Identity).where(
            Identity.target_id == target_id,
            Identity.workspace_id == workspace_id,
        )
    ).scalars().all()
    for ident in identities:
        if ident.value:
            existing.add((ident.type, ident.value.lower().strip()))

    cascades = []
    seen = set()
    source_key = (source_type, source_value.lower().strip())

    for f in deep_findings:
        data = f.data if isinstance(f.data, dict) else {}
        extracted = data.get("extracted", data)

        for field in ("email", "contact_email", "user_email"):
            val = extracted.get(field)
            if val and isinstance(val, str) and "@" in val:
                key = ("email", val.lower().strip())
                if key != source_key and key not in existing and key not in seen:
                    seen.add(key)
                    cascades.append(key)

        for field in ("twitter_username", "github_username", "username", "login"):
            val = extracted.get(field)
            if val and isinstance(val, str) and len(val) >= 2:
                key = ("username", val.strip())
                if key != source_key and key not in existing and key not in seen:
                    seen.add(key)
                    cascades.append(key)

        for field in ("blog", "website", "website_url", "homepage"):
            val = extracted.get(field)
            if val and isinstance(val, str):
                domain = val.replace("https://", "").replace("http://", "").split("/")[0].lower()
                if domain and "." in domain and len(domain) >= 4:
                    key = ("domain", domain)
                    if key != source_key and key not in existing and key not in seen:
                        seen.add(key)
                        cascades.append(key)

    return cascades[:5]


def _full_refinalize(target_id_str: str, workspace_id_str: str, session):
    """Full re-finalize: mirrors finalize_scan() pipeline without Pass 1.5/2.

    Steps: cross-verify -> graph -> PageRank -> graph_context -> score ->
    profile -> bio cleanup -> name validation -> quick teaser ->
    identity enrichment -> personas -> intelligence -> fingerprint -> SSE.
    """
    from api.models.target import Target
    from api.models.finding import Finding
    from api.models.scan import Scan
    from api.models.identity import Identity, IdentityLink

    target_id = uuid.UUID(target_id_str) if isinstance(target_id_str, str) else target_id_str
    workspace_id = uuid.UUID(workspace_id_str) if isinstance(workspace_id_str, str) else workspace_id_str

    target = session.execute(select(Target).where(Target.id == target_id)).scalar_one_or_none()
    if not target:
        return

    # Resolve latest scan_id (needed for intelligence pipeline)
    latest_scan = session.execute(
        select(Scan).where(
            Scan.target_id == target_id,
            Scan.status == "completed",
        ).order_by(Scan.completed_at.desc()).limit(1)
    ).scalar_one_or_none()
    scan_id = latest_scan.id if latest_scan else None

    # 1. Cross-verify findings
    try:
        from api.services.layer4.source_scoring import cross_verify_findings
        cross_verify_findings(target_id, session)
    except Exception:
        logger.exception("REFINALIZE[%s]: cross-verify failed", target_id)
    logger.info("REFINALIZE[%s]: cross_verify done", target_id)

    # 2. Build graph
    try:
        from api.services.layer4.graph_builder import build_graph
        build_graph(target_id, workspace_id, session)
    except Exception:
        logger.exception("REFINALIZE[%s]: graph build failed", target_id)
    logger.info("REFINALIZE[%s]: graph_builder done", target_id)

    # 3. PageRank
    try:
        from api.services.layer4.confidence_propagator import propagate_confidence
        propagate_confidence(target_id, workspace_id, session)
    except Exception:
        logger.exception("REFINALIZE[%s]: PageRank failed", target_id)
    logger.info("REFINALIZE[%s]: pagerank done", target_id)

    # 4. Build graph_context
    graph_context = None
    try:
        graph_context = _build_graph_context(target_id, workspace_id, session)
    except Exception:
        logger.exception("REFINALIZE[%s]: graph_context failed", target_id)
    logger.info("REFINALIZE[%s]: graph_context done", target_id)

    # 5. Score (correct signature: target_id, session, graph_context)
    try:
        from api.services.layer4.score_engine import compute_score
        compute_score(target_id, session, graph_context=graph_context)
    except Exception:
        logger.exception("REFINALIZE[%s]: score failed", target_id)
    logger.info("REFINALIZE[%s]: score done", target_id)

    # 6. Profile aggregation
    try:
        from api.services.layer4.profile_aggregator import aggregate_profile
        aggregate_profile(target_id, workspace_id, session, graph_context=graph_context)
    except Exception:
        logger.exception("REFINALIZE[%s]: profile aggregation failed", target_id)
    logger.info("REFINALIZE[%s]: profile_aggregator done", target_id)

    # 7. Bio cleanup
    try:
        target = session.execute(select(Target).where(Target.id == target_id)).scalar_one_or_none()
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
        logger.exception("REFINALIZE[%s]: bio cleanup failed", target_id)

    # 8. Display name validation
    try:
        from api.services.layer4.profile_aggregator import _load_blacklist, _is_valid_name_db
        target = session.execute(select(Target).where(Target.id == target_id)).scalar_one_or_none()
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
        logger.exception("REFINALIZE[%s]: name validation failed", target_id)

    # 9. Quick teaser
    try:
        target = session.execute(select(Target).where(Target.id == target_id)).scalar_one_or_none()
        if target:
            all_target_findings = session.execute(
                select(Finding).where(Finding.target_id == target_id)
            ).scalars().all()
            sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
            sorted_findings = sorted(all_target_findings, key=lambda f: sev_order.get(f.severity, 5))
            profile = dict(target.profile_data or {})
            profile["quick_teaser"] = {
                "top_findings": [
                    {"title": f.title, "severity": f.severity, "category": f.category}
                    for f in sorted_findings[:3]
                ],
                "total_findings": len(all_target_findings),
            }
            target.profile_data = profile
            session.commit()
    except Exception:
        logger.exception("REFINALIZE[%s]: quick teaser failed", target_id)

    # 10. Identity enrichment
    try:
        from api.services.layer4.identity_enricher import enrich_identity
        target = session.execute(select(Target).where(Target.id == target_id)).scalar_one_or_none()
        if target:
            profile = dict(target.profile_data or {})
            est = profile.get("identity_estimation", {})
            max_nat_prob = max(
                (n.get("probability", 0) for n in est.get("nationalities", [{}]) if isinstance(n, dict)),
                default=0,
            )
            if not est.get("gender") or not est.get("age") or max_nat_prob < 0.15:
                updated_est = enrich_identity(profile, target.email)
                if updated_est and (updated_est.get("gender") or updated_est.get("age")):
                    profile["identity_estimation"] = updated_est
                    target.profile_data = profile
                    session.commit()
    except Exception:
        logger.exception("REFINALIZE[%s]: identity enrichment failed", target_id)

    # Load plan for feature gating
    try:
        from api.models.workspace import Workspace
        from api.models.user import UserWorkspace
        from api.services.plan_config import check_feature
        ws = session.execute(select(Workspace).where(Workspace.id == workspace_id)).scalar_one_or_none()
        plan_name = ws.plan if ws else "free"
        uw = session.execute(
            select(UserWorkspace).where(UserWorkspace.workspace_id == workspace_id).limit(1)
        ).scalar_one_or_none()
        ws_role = uw.role if uw else "user"
    except Exception:
        logger.exception("REFINALIZE[%s]: plan load failed", target_id)
        plan_name = "free"
        ws_role = "user"
        from api.services.plan_config import check_feature

    # 11. Persona clustering (plan-gated)
    if check_feature(plan_name, "persona_clustering", ws_role):
        try:
            from api.services.layer4.persona_engine import cluster_personas
            target = session.execute(select(Target).where(Target.id == target_id)).scalar_one_or_none()
            personas = cluster_personas(target_id, workspace_id, session,
                                        graph_context=graph_context,
                                        profile_data=dict(target.profile_data or {}))
            if personas:
                profile = dict(target.profile_data or {})
                profile["personas"] = personas
                target.profile_data = profile
                session.commit()
        except Exception:
            logger.exception("REFINALIZE[%s]: personas failed", target_id)
    logger.info("REFINALIZE[%s]: personas done", target_id)

    # 12. Intelligence pipeline (plan-gated)
    if scan_id and check_feature(plan_name, "intelligence_pipeline", ws_role):
        try:
            from api.services.layer4.analysis_pipeline import AnalysisPipeline
            pipeline = AnalysisPipeline()
            intel_count = pipeline.run(target_id, workspace_id, str(scan_id), session)
            if intel_count:
                logger.info("REFINALIZE[%s]: intelligence created %d findings", target_id, intel_count)
        except Exception:
            logger.exception("REFINALIZE[%s]: intelligence pipeline failed", target_id)
    logger.info("REFINALIZE[%s]: intelligence done", target_id)

    # 13. Fingerprint (correct signature: findings, identities, profile_data, email, ...)
    try:
        from api.services.layer4.fingerprint_engine import FingerprintEngine
        target = session.execute(select(Target).where(Target.id == target_id)).scalar_one_or_none()

        raw_findings = session.execute(
            select(Finding).where(Finding.target_id == target_id)
        ).scalars().all()
        seen_fp = {}
        for f in raw_findings:
            key = (f.module, f.title)
            existing = seen_fp.get(key)
            if existing is None or (f.created_at and (not existing.created_at or f.created_at > existing.created_at)):
                seen_fp[key] = f
        all_findings = list(seen_fp.values())

        all_identities = session.execute(
            select(Identity).where(Identity.target_id == target_id)
        ).scalars().all()

        identity_ids = [i.id for i in all_identities]
        all_links = []
        if identity_ids:
            all_links = session.execute(
                select(IdentityLink).where(IdentityLink.workspace_id == workspace_id)
            ).scalars().all()
            id_set = set(identity_ids)
            all_links = [l for l in all_links if l.source_id in id_set or l.dest_id in id_set]

        fp_engine = FingerprintEngine()
        fingerprint = fp_engine.compute(
            all_findings, all_identities, target.profile_data, target.email,
            links=all_links, graph_context=graph_context,
            country_code=target.country_code,
        )

        if fingerprint:
            # 14. History snapshot
            snapshot = {
                "hash": fingerprint["hash"],
                "score": fingerprint["score"],
                "risk_level": fingerprint["risk_level"],
                "axes": fingerprint["axes"],
                "raw_values": fingerprint["raw_values"],
                "label": fingerprint.get("label", ""),
                "scan_id": str(scan_id) if scan_id else None,
                "computed_at": fingerprint["computed_at"],
                "findings_count": len(all_findings),
            }
            history = list(target.fingerprint_history or [])
            history.append(snapshot)
            target.fingerprint_history = history[-50:]

            profile = dict(target.profile_data or {})
            profile["fingerprint"] = fingerprint
            timeline = fingerprint.get("timeline_events", [])
            if timeline:
                profile["life_timeline"] = timeline
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
    except Exception:
        logger.exception("REFINALIZE[%s]: fingerprint failed", target_id)
    logger.info("REFINALIZE[%s]: fingerprint done", target_id)

    # 15. SSE event
    try:
        from api.services.event_bus import publish_event
        target = session.execute(select(Target).where(Target.id == target_id)).scalar_one_or_none()
        publish_event("target.updated", {
            "target_id": str(target_id),
            "workspace_id": str(workspace_id),
            "exposure_score": target.exposure_score if target else 0,
            "threat_score": target.threat_score if target else 0,
        })
    except Exception:
        pass

    logger.info("REFINALIZE[%s]: complete", target_id)
