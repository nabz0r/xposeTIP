"""Staggered bulk rescan of every human-workspace target.

S303 — ops harness. Dispatches one Scan per human target via Celery, spaced
`--window` seconds apart (default 540 = 9 min) so workers + API keys are never
saturated: with ~few-min quick scans and 9-min spacing, ≈1 scan is active at a time.

SAFE BY DEFAULT — dry-run unless `--yes`. The dry-run prints N + the estimated
wall-clock + a cost note and dispatches NOTHING.

Mirrors create_scan (api/routers/scans.py) for module resolution + Scan creation,
and the _s261_recompute_all.py discipline: COMMIT PER TARGET (never a global txn —
that locks the corpus and blocks live scans), per-target try/except so one bad
target can't abort the run.

The 9-min window throttles RATE, not total volume: N targets = N rounds of paid-key
lookups (HIBP / Shodan / etc.). Use --workspace / --limit to scope.

Run (dry):  docker compose exec api python scripts/rescan_all_human.py
Run (go):   docker compose exec api python scripts/rescan_all_human.py --yes
Scope:      ... --workspace <uuid> | --limit <n> | --window <sec>
"""
import argparse
import logging
import uuid as uuidlib

logging.getLogger().setLevel(logging.WARNING)
from sqlalchemy import select  # noqa: E402

from api.tasks.utils import get_sync_session  # noqa: E402
from api.tasks.module_tasks import SCANNER_REGISTRY  # noqa: E402
from api.tasks.scan_orchestrator import launch_scan  # noqa: E402
from api.routers.scans import DEFAULT_QUICK_MODULES  # noqa: E402
from api.models.target import Target  # noqa: E402
from api.models.workspace import Workspace  # noqa: E402
from api.models.module import Module  # noqa: E402
from api.models.scan import Scan  # noqa: E402


def _fmt_eta(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="actually dispatch (default: dry-run)")
    ap.add_argument("--workspace", help="scope to one workspace UUID (default: all human)")
    ap.add_argument("--window", type=int, default=540, help="seconds between dispatches (default 540 = 9 min)")
    ap.add_argument("--limit", type=int, help="cap target count (trial runs)")
    args = ap.parse_args()

    s = get_sync_session()

    # Agent targets NEVER enter (kind == 'human' only) — S291 invariant.
    q = (
        select(Target.id, Target.workspace_id)
        .join(Workspace, Workspace.id == Target.workspace_id)
        .where(Workspace.kind == "human")
    )
    if args.workspace:
        q = q.where(Target.workspace_id == uuidlib.UUID(args.workspace))
    q = q.order_by(Target.created_at.asc())
    targets = [(t.id, t.workspace_id) for t in s.execute(q).all()]
    if args.limit:
        targets = targets[: args.limit]
    n = len(targets)

    # enabled modules + workspace default_modules cache
    enabled_ids = {m.id for m in s.execute(select(Module).where(Module.enabled.is_(True))).scalars().all()}
    ws_defaults = {
        w.id: (w.settings or {}).get("default_modules")
        for w in s.execute(select(Workspace).where(Workspace.kind == "human")).scalars().all()
    }

    last_eta_min = (n - 1) * args.window // 60 if n else 0
    print(f"START human_targets={n}", flush=True)
    print(f"window={args.window}s/target  →  estimated total wall-clock ≈ {_fmt_eta(last_eta_min)} (last scan eta +{last_eta_min}min)", flush=True)
    print("modules = DEFAULT_QUICK_MODULES (or workspace default_modules where set)", flush=True)
    print(f"NOTE: the {args.window}s window throttles RATE, not total volume — {n} targets = {n}x paid-key lookups (HIBP/Shodan/etc.).", flush=True)

    if not args.yes:
        print("Dry-run only. Re-run with --yes to dispatch.", flush=True)
        return

    dispatched = failed = 0
    for idx, (tid, wid) in enumerate(targets):
        try:
            requested = ws_defaults.get(wid) or DEFAULT_QUICK_MODULES
            valid = [m for m in requested if m in enabled_ids and m in SCANNER_REGISTRY]
            if not valid:
                print(f"[{idx+1}/{n}] target={tid} SKIP (no valid modules)", flush=True)
                continue
            scan = Scan(
                workspace_id=wid, target_id=tid, modules=valid,
                module_progress={m: "queued" for m in valid},
            )
            s.add(scan)
            tgt = s.execute(select(Target).where(Target.id == tid)).scalar_one()
            tgt.status = "scanning"
            s.commit()
            s.refresh(scan)
            task = launch_scan.apply_async(args=[str(scan.id)], countdown=idx * args.window)
            scan.celery_task_id = task.id
            s.commit()
            dispatched += 1
            print(f"[{idx+1}/{n}] target={tid} scan={scan.id} eta=+{idx * args.window // 60}min", flush=True)
        except Exception as e:  # noqa: BLE001
            s.rollback()
            failed += 1
            print(f"[{idx+1}/{n}] target={tid} FAILED {e!r}", flush=True)
            continue

    print(f"DISPATCHED {dispatched} scans, failed={failed}, last eta +{last_eta_min}min — run the report after that + ~5min buffer.", flush=True)


if __name__ == "__main__":
    main()
