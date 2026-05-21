"""S144 — Recompute fingerprints from existing scan data after AXIS_MAX recalibration.

For every target with an existing fingerprint in profile_data, re-runs
FingerprintEngine.compute() on the same findings/identities (no rescan),
appends the new snapshot to fingerprint_history with reason='S144_recalibration',
writes the new fingerprint to profile_data['fingerprint'], and refreshes that
target's row in target_similarities by calling similarity_engine.recompute_for_target.

Idempotent. Safe to re-run. Each target updated independently — partial-run
crashes don't corrupt prior targets (per-target commit).

Usage:
    docker compose exec api python scripts/recompute_fingerprints.py
    docker compose exec api python scripts/recompute_fingerprints.py --workspace friends
    docker compose exec api python scripts/recompute_fingerprints.py --dry-run --limit 5
"""
import argparse
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from api.tasks.utils import get_sync_session
from api.models.workspace import Workspace
from api.models.target import Target
from api.models.finding import Finding
from api.models.identity import Identity, IdentityLink
from api.services.layer4.fingerprint_engine import FingerprintEngine
from api.services.layer4.similarity_engine import recompute_for_target

RECOMPUTE_REASON = "S144_recalibration"


def _dedupe_findings(raw_findings):
    """Same Python-side dedup the orchestrator uses (latest per (module, title))."""
    seen = {}
    for f in raw_findings:
        key = (f.module, f.title)
        existing = seen.get(key)
        if existing is None or (f.created_at and (not existing.created_at or f.created_at > existing.created_at)):
            seen[key] = f
    return list(seen.values())


def _axes_changed_count(old_axes, new_axes, threshold=0.05):
    """Count how many axes shifted by >= threshold (normalized)."""
    if not old_axes:
        return len(new_axes)
    count = 0
    for k, new_v in new_axes.items():
        old_v = old_axes.get(k, 0.0) or 0.0
        if abs((new_v or 0.0) - old_v) >= threshold:
            count += 1
    return count


def _all_axes_unchanged(old_axes, new_axes):
    """Idempotency check — true if old and new have the SAME keys and every
    axis is within 0.001 of the old value. Returns False when a new axis was
    added even if its value is 0 (dimension change still requires a write so
    the persisted fingerprint reflects the current schema)."""
    if not old_axes or not new_axes:
        return False
    if set(old_axes.keys()) != set(new_axes.keys()):
        return False
    for k, new_v in new_axes.items():
        old_v = old_axes.get(k, 0.0) or 0.0
        if abs((new_v or 0.0) - old_v) > 0.001:
            return False
    return True


def _process_target(session, target, fp_engine, dry_run):
    """Recompute fingerprint for one target. Returns (status, summary_dict)."""
    raw_findings = session.execute(
        select(Finding).where(Finding.target_id == target.id)
    ).scalars().all()
    if not raw_findings:
        return "no_findings", None

    all_findings = _dedupe_findings(raw_findings)
    all_identities = session.execute(
        select(Identity).where(Identity.target_id == target.id)
    ).scalars().all()

    identity_ids = [i.id for i in all_identities]
    all_links = []
    if identity_ids:
        all_links = session.execute(
            select(IdentityLink).where(IdentityLink.workspace_id == target.workspace_id)
        ).scalars().all()
        id_set = set(identity_ids)
        all_links = [l for l in all_links if l.source_id in id_set or l.dest_id in id_set]

    old_fp = (target.profile_data or {}).get("fingerprint") or {}
    old_axes = old_fp.get("axes") or {}
    old_score = old_fp.get("score")

    fingerprint = fp_engine.compute(
        all_findings, all_identities, target.profile_data, target.email,
        links=all_links, graph_context=None,
        country_code=target.country_code,
    )
    new_axes = fingerprint["axes"]
    new_score = fingerprint["score"]
    delta_axes = _axes_changed_count(old_axes, new_axes)

    summary = {
        "old_score": old_score,
        "new_score": new_score,
        "delta_axes": delta_axes,
        "unchanged": _all_axes_unchanged(old_axes, new_axes),
    }

    if dry_run:
        return "dry_run", summary

    if summary["unchanged"]:
        return "skip_unchanged", summary

    snapshot = {
        "hash": fingerprint["hash"],
        "score": fingerprint["score"],
        "risk_level": fingerprint["risk_level"],
        "axes": fingerprint["axes"],
        "raw_values": fingerprint["raw_values"],
        "label": fingerprint.get("label", ""),
        "scan_id": None,
        "computed_at": fingerprint["computed_at"],
        "findings_count": len(all_findings),
        "reason": RECOMPUTE_REASON,
    }
    history = list(target.fingerprint_history or [])
    history.append(snapshot)
    target.fingerprint_history = history[-50:]

    profile = dict(target.profile_data or {})
    profile["fingerprint"] = fingerprint
    target.profile_data = profile
    target.updated_at = datetime.now(timezone.utc)

    session.commit()

    # Refresh similarity rows for this target. recompute_for_target commits internally.
    try:
        sim_result = recompute_for_target(session, target.id, target.workspace_id)
        summary["sim_pairs"] = sim_result.get("matches_persisted", 0)
    except Exception as e:
        summary["sim_pairs"] = 0
        summary["sim_error"] = str(e)

    return "recomputed", summary


def _process_workspace(session, ws, fp_engine, dry_run, limit):
    print(f"\nWorkspace: {ws.slug} ({ws.name})")
    targets = session.execute(
        select(Target).where(Target.workspace_id == ws.id)
    ).scalars().all()
    # Only process targets that already have a fingerprint
    with_fp = [t for t in targets if (t.profile_data or {}).get("fingerprint")]
    if not with_fp:
        print("  (no fingerprints to recompute)")
        return {"recomputed": 0, "skipped": 0, "errors": 0, "sim_pairs": 0}
    if limit:
        with_fp = with_fp[:limit]
    print(f"  {len(with_fp)} targets with fingerprint")

    counters = {"recomputed": 0, "skipped": 0, "errors": 0, "sim_pairs": 0}
    t0 = time.time()
    for idx, target in enumerate(with_fp, start=1):
        try:
            status, summary = _process_target(session, target, fp_engine, dry_run)
        except Exception as e:
            session.rollback()
            counters["errors"] += 1
            print(f"  [{idx:>3}/{len(with_fp)}] {target.email:<40} ERROR: {e}")
            continue

        if status == "no_findings":
            counters["skipped"] += 1
            print(f"  [{idx:>3}/{len(with_fp)}] {target.email:<40} skipped: no findings")
        elif status == "dry_run":
            old_s = summary["old_score"] if summary["old_score"] is not None else "—"
            print(f"  [{idx:>3}/{len(with_fp)}] {target.email:<40} "
                  f"score {old_s}→{summary['new_score']}  Δaxes={summary['delta_axes']}  [DRY]")
        elif status == "skip_unchanged":
            counters["skipped"] += 1
            print(f"  [{idx:>3}/{len(with_fp)}] {target.email:<40} unchanged (idempotent skip)")
        else:
            counters["recomputed"] += 1
            counters["sim_pairs"] += summary.get("sim_pairs", 0)
            old_s = summary["old_score"] if summary["old_score"] is not None else "—"
            sim_pairs = summary.get("sim_pairs", 0)
            print(f"  [{idx:>3}/{len(with_fp)}] {target.email:<40} "
                  f"score {old_s}→{summary['new_score']}  Δaxes={summary['delta_axes']}  sim_pairs={sim_pairs}")

    dt = time.time() - t0
    print(f"  Done in {dt:.1f}s — "
          f"recomputed={counters['recomputed']}  skipped={counters['skipped']}  "
          f"errors={counters['errors']}  sim_pairs={counters['sim_pairs']}")
    return counters


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--workspace", help="Workspace slug; if omitted, processes all")
    parser.add_argument("--dry-run", action="store_true", help="Compute, print diff, do NOT write")
    parser.add_argument("--limit", type=int, help="Max targets per workspace")
    args = parser.parse_args()

    session = get_sync_session()
    fp_engine = FingerprintEngine()

    try:
        if args.workspace:
            ws = session.execute(
                select(Workspace).where(Workspace.slug == args.workspace)
            ).scalar_one_or_none()
            if not ws:
                print(f"Workspace slug '{args.workspace}' not found.", file=sys.stderr)
                return 1
            workspaces = [ws]
        else:
            workspaces = session.execute(
                select(Workspace).order_by(Workspace.slug)
            ).scalars().all()

        if args.dry_run:
            print("=== DRY-RUN: no DB writes ===")

        t_global = time.time()
        totals = {"recomputed": 0, "skipped": 0, "errors": 0, "sim_pairs": 0}
        ws_count = 0
        for ws in workspaces:
            c = _process_workspace(session, ws, fp_engine, args.dry_run, args.limit)
            for k in totals:
                totals[k] += c[k]
            ws_count += 1
        dt_global = time.time() - t_global

        print("\n=== S144 Recompute Summary ===")
        print(f"Workspaces processed:        {ws_count}")
        print(f"Targets recomputed:          {totals['recomputed']}")
        print(f"Targets skipped:             {totals['skipped']}")
        print(f"Errors:                      {totals['errors']}")
        print(f"Similarity pairs persisted:  {totals['sim_pairs']}")
        print(f"Total runtime:               {dt_global:.1f}s")
        if args.dry_run:
            print("(dry-run — no DB writes performed)")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
