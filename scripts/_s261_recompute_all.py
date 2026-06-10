"""Per-target-commit profile recompute across ALL workspaces.

Generalized deploy harness (first used S261, mandatory for the S263 typed-confidence
flip). Mirrors the system.py "Recalculate Profiles" endpoint (S125 finding-confidence
rebuild + cross-verify + aggregation) but iterates every workspace and COMMITS PER
TARGET so:
  - `findings.confidence` row locks release continuously (no corpus-wide lock that
    would block live scans),
  - progress survives an interruption,
  - a single bad target can't roll back the whole pass.

NEVER replace this with a single global transaction (the S261 deploy failure mode:
a 20-min uncommitted txn holding locks DB-wide). Read-only audits should use
scripts/audit_typed_confidence.py instead — this script WRITES.

Run: docker compose exec api python scripts/_s261_recompute_all.py
"""
import logging
import sys

logging.getLogger().setLevel(logging.WARNING)
from sqlalchemy import select  # noqa: E402

from api.tasks.utils import get_sync_session  # noqa: E402
from api.services.layer4.profile_aggregator import aggregate_profile  # noqa: E402
from api.services.layer4.identity_enricher import enrich_identity  # noqa: E402
from api.services.layer4.source_scoring import (  # noqa: E402
    compute_finding_confidence, cross_verify_findings,
)
from api.models.finding import Finding  # noqa: E402
from api.models.target import Target  # noqa: E402

s = get_sync_session()
target_ids = [
    (t.id, t.workspace_id) for t in s.execute(select(Target.id, Target.workspace_id)).all()
]
total = len(target_ids)
print(f"START total={total}", flush=True)

updated = enriched = conf_recomputed = cv_boosted = capped = failed = 0
over_ceiling = []   # S263 stop-gate canary: any system value > 0.95 (operator-assert excepted)
for idx, (tid, wid) in enumerate(target_ids, 1):
    try:
        tf = s.execute(
            select(Finding).where(Finding.target_id == tid, Finding.status == "active")
        ).scalars().all()
        for f in tf:
            nc = compute_finding_confidence(f)
            if f.confidence != nc:
                f.confidence = nc
                conf_recomputed += 1
        if tf:
            s.flush()
        cv_boosted += cross_verify_findings(tid, s)
        p = aggregate_profile(tid, wid, s)
        conf = p.get("confidence") or {}
        if conf.get("coherence_flag") == "unverified_collision":
            capped += 1
        if conf.get("overall", 0) > 0.95 and p.get("primary_name_source") != "operator":
            over_ceiling.append((tid, conf.get("overall")))
        updated += 1
        tgt = s.execute(select(Target).where(Target.id == tid)).scalar_one_or_none()
        if tgt:
            prof = dict(tgt.profile_data or {})
            est = prof.get("identity_estimation", {})
            if not est.get("gender") or not est.get("age"):
                ue = enrich_identity(prof, tgt.email)
                if ue and (ue.get("gender") or ue.get("age")):
                    prof["identity_estimation"] = ue
                    tgt.profile_data = prof
                    enriched += 1
        s.commit()  # per-target commit — release locks, persist progress
    except Exception:
        s.rollback()
        failed += 1
        logging.exception("fail target %s", tid)
    if idx % 25 == 0 or idx == total:
        print(f"PROGRESS {idx}/{total} capped={capped} failed={failed}", flush=True)

s.close()
print(
    f"RESULT total={total} recalculated={updated} enriched={enriched} "
    f"confidence_recomputed={conf_recomputed} cross_verified_boosted={cv_boosted} "
    f"collision_capped={capped} failed={failed}",
    flush=True,
)
print(f"OVER_CEILING (system overall > 0.95, should be empty): {over_ceiling[:20]}", flush=True)
sys.exit(0)
