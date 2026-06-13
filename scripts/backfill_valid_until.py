"""S304a — backfill findings.valid_until for rows stamped before the freshness layer.

valid_until = last_seen + resolve_ttl(category, per-scraper override). Idempotent
(only touches valid_until IS NULL). Batch-commit (not a global txn — S261 lesson).
--dry-run prints the resolved-TTL distribution by category without writing.

Run: docker compose exec api python scripts/backfill_valid_until.py [--dry-run]
"""
import argparse
import logging
from datetime import timedelta

logging.getLogger().setLevel(logging.WARNING)
from sqlalchemy import select  # noqa: E402

from api.tasks.utils import get_sync_session  # noqa: E402
from api.models.finding import Finding  # noqa: E402
from api.models.scraper import Scraper  # noqa: E402
from api.services.freshness import resolve_ttl  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--batch", type=int, default=500)
    args = ap.parse_args()

    s = get_sync_session()
    overrides = {
        name: ttl for name, ttl in s.execute(
            select(Scraper.name, Scraper.ttl_seconds).where(Scraper.ttl_seconds.is_not(None))
        ).all()
    }

    rows = s.execute(
        select(Finding.id, Finding.category, Finding.module, Finding.last_seen)
        .where(Finding.valid_until.is_(None))
    ).all()
    total = len(rows)
    print(f"valid_until IS NULL: {total} findings", flush=True)

    if args.dry_run:
        from collections import Counter
        dist = Counter()
        for _id, cat, mod, _ls in rows:
            ttl = resolve_ttl(cat, overrides.get(mod))
            dist[(cat or "<none>", ttl // 86400)] += 1
        print("resolved-TTL distribution (category, days → count):", flush=True)
        for (cat, days), c in sorted(dist.items(), key=lambda kv: -kv[1]):
            print(f"  {cat:24s} {days:4d}d  {c}", flush=True)
        print("DRY-RUN — no writes.", flush=True)
        return

    updated = skipped = 0
    for i, (fid, cat, mod, last_seen) in enumerate(rows, 1):
        if last_seen is None:
            skipped += 1
            continue
        f = s.get(Finding, fid)
        f.valid_until = last_seen + timedelta(seconds=resolve_ttl(cat, overrides.get(mod)))
        updated += 1
        if i % args.batch == 0:
            s.commit()
            print(f"  ...{i}/{total} committed", flush=True)
    s.commit()
    print(f"DONE updated={updated} skipped(no last_seen)={skipped} total={total}", flush=True)


if __name__ == "__main__":
    main()
