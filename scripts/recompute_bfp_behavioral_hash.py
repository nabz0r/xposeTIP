#!/usr/bin/env python3
"""
Backfill bfp_behavioral_hash_v1 across the existing corpus.

Reads each target's current fingerprint from `target.profile_data["fingerprint"]`
(the engine writes there post-scan; orchestrator also persists history in
`target.fingerprint_history`). Recomputes the v1 behavioral hash from the cached
axes and writes to `target.bfp_behavioral_hash_v1` (S166 column).

Idempotent — re-running produces the same hash for the same input.

Usage:
    docker compose exec api python scripts/recompute_bfp_behavioral_hash.py
    docker compose exec api python scripts/recompute_bfp_behavioral_hash.py --workspace friends
    docker compose exec api python scripts/recompute_bfp_behavioral_hash.py --dry-run
    docker compose exec api python scripts/recompute_bfp_behavioral_hash.py --compare <uuid_a> <uuid_b>
"""
import argparse
import sys
import uuid as _uuid

from sqlalchemy import select

from api.tasks.utils import get_sync_session
from api.models.target import Target
from api.models.workspace import Workspace
from api.services.layer4.fingerprint_engine import FingerprintEngine


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--workspace", default=None, help="Workspace slug to filter (default: all)")
    p.add_argument("--dry-run", action="store_true", help="Compute but do not write")
    p.add_argument("--limit", type=int, default=None, help="Max targets")
    p.add_argument("--compare", nargs=2, metavar=("UUID_A", "UUID_B"),
                   help="Compute Jaccard similarity between two existing hashes (skips backfill)")
    return p.parse_args()


def _get_current_axes(target) -> dict | None:
    """Return current axes dict from profile_data['fingerprint']['axes'], or
    fall back to the most recent fingerprint_history entry. Returns None when
    no axes have ever been computed for this target."""
    profile = target.profile_data or {}
    fp = profile.get("fingerprint") if isinstance(profile, dict) else None
    if isinstance(fp, dict) and isinstance(fp.get("axes"), dict):
        return fp["axes"]
    history = target.fingerprint_history or []
    if isinstance(history, list) and history:
        last = history[-1]
        if isinstance(last, dict) and isinstance(last.get("axes"), dict):
            return last["axes"]
    return None


def compare_hashes(session, uuid_a: str, uuid_b: str) -> float | None:
    """Compute Jaccard similarity between two stored behavioral hashes."""
    try:
        from datasketch import MinHash
        import numpy as np
    except ImportError:
        print("ERROR: datasketch and/or numpy not installed", file=sys.stderr)
        sys.exit(3)

    a = session.get(Target, _uuid.UUID(uuid_a))
    b = session.get(Target, _uuid.UUID(uuid_b))
    if not (a and b and a.bfp_behavioral_hash_v1 and b.bfp_behavioral_hash_v1):
        return None

    m_a = MinHash(num_perm=128, seed=42)
    m_b = MinHash(num_perm=128, seed=42)
    m_a.hashvalues = np.frombuffer(bytes.fromhex(a.bfp_behavioral_hash_v1), dtype=np.uint64).copy()
    m_b.hashvalues = np.frombuffer(bytes.fromhex(b.bfp_behavioral_hash_v1), dtype=np.uint64).copy()
    return m_a.jaccard(m_b)


def main() -> None:
    args = parse_args()
    session = get_sync_session()
    try:
        if args.compare:
            sim = compare_hashes(session, args.compare[0], args.compare[1])
            if sim is None:
                print("One or both targets lack bfp_behavioral_hash_v1", file=sys.stderr)
                sys.exit(1)
            print(f"Jaccard similarity: {sim:.4f}")
            return

        stmt = select(Target)
        if args.workspace:
            ws = session.execute(
                select(Workspace).where(Workspace.slug == args.workspace)
            ).scalar_one_or_none()
            if ws is None:
                print(f"ERROR: workspace slug '{args.workspace}' not found", file=sys.stderr)
                sys.exit(2)
            stmt = stmt.where(Target.workspace_id == ws.id)
        if args.limit:
            stmt = stmt.limit(args.limit)

        targets = session.execute(stmt).scalars().all()

        engine = FingerprintEngine()
        n_total = len(targets)
        n_computed = 0
        n_written = 0
        n_skipped_no_axes = 0
        n_unchanged = 0

        for t in targets:
            axes = _get_current_axes(t)
            if axes is None:
                n_skipped_no_axes += 1
                continue
            raw = (t.profile_data or {}).get("fingerprint", {}).get("raw_values", {}) if t.profile_data else {}
            hash_hex = engine._compute_behavioral_hash_v1(axes, raw, t.email or "")
            n_computed += 1
            if not hash_hex:
                # Empty hash → no selected axes were present. Treat as skip rather than NULL-overwrite.
                continue
            if t.bfp_behavioral_hash_v1 == hash_hex:
                n_unchanged += 1
                continue
            if not args.dry_run:
                t.bfp_behavioral_hash_v1 = hash_hex
                n_written += 1

        if not args.dry_run:
            session.commit()

        print(
            f"Targets: {n_total}  computed: {n_computed}  written: {n_written}  "
            f"unchanged: {n_unchanged}  skipped(no_axes): {n_skipped_no_axes}",
            file=sys.stderr,
        )
        if args.dry_run:
            print("(dry-run — no writes)", file=sys.stderr)
    finally:
        session.close()


if __name__ == "__main__":
    main()
