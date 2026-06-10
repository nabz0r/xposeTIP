#!/usr/bin/env python3
"""
S262 — Typed-confidence shadow audit (read-only, in-memory).

Computes the typed confidence for every target via the SAME shared function the
aggregator uses (`finding_classifier.compute_typed_confidence`), compares it to the
stored legacy `confidence.overall`, and reports the corpus distribution + the
Play-1 report deltas + the biggest movers.

S261 deploy lesson baked in: NO recompute, NO persist, NO --apply, NO long
transaction, NO `findings.confidence` row locks. Each target is a short read.

Run from repo root:
  docker compose exec api python scripts/audit_typed_confidence.py
"""

import logging
import sys

logging.getLogger().setLevel(logging.ERROR)
from sqlalchemy import select  # noqa: E402

from api.tasks.utils import get_sync_session  # noqa: E402
from api.models.finding import Finding  # noqa: E402
from api.models.target import Target  # noqa: E402
from api.services.layer4.finding_classifier import compute_typed_confidence  # noqa: E402


def _decile(x):
    return min(9, int(x * 10))


def main():
    s = get_sync_session()
    targets = s.execute(select(Target)).scalars().all()

    rows = []          # (email, legacy, typed, breakdown)
    skipped = 0
    legacy_hist = [0] * 10
    typed_hist = [0] * 10

    for t in targets:
        pd = t.profile_data or {}
        conf = pd.get("confidence") or {}
        legacy = conf.get("overall")
        names = pd.get("names") or []

        findings = s.execute(
            select(Finding).where(Finding.target_id == t.id, Finding.status == "active")
        ).scalars().all()

        seed_email = (t.email or "").strip().lower()
        seed_domain = seed_email.split("@")[-1] if "@" in seed_email else ""
        typed, breakdown = compute_typed_confidence(findings, names, seed_email, seed_domain)

        if legacy is None:
            skipped += 1
            continue

        rows.append((t.email, float(legacy), typed, breakdown))
        legacy_hist[_decile(float(legacy))] += 1
        typed_hist[_decile(typed)] += 1

    s.close()

    n = len(rows)
    if not n:
        print("No targets with a stored legacy confidence.overall — nothing to compare.")
        sys.exit(0)

    deltas = sorted(typed - legacy for (_, legacy, typed, _) in rows)
    median_shift = deltas[n // 2]
    moved_big = sum(1 for d in deltas if abs(d) > 0.30)
    legacy_above_07 = sum(1 for (_, l, _, _) in rows if l >= 0.70)
    typed_above_07 = sum(1 for (_, _, ty, _) in rows if ty >= 0.70)
    crossed_down = sum(1 for (_, l, ty, _) in rows if l >= 0.70 and ty < 0.70)

    print("=" * 70)
    print("S262 typed-confidence shadow audit  (read-only, no writes)")
    print("=" * 70)
    print(f"targets compared : {n}   (skipped, no stored confidence: {skipped})")
    print()
    print("decile histogram        legacy   typed")
    for d in range(10):
        bar_l = "#" * (legacy_hist[d] * 40 // max(legacy_hist + [1]))
        print(f"  {d/10:.1f}-{d/10+0.1:.1f}   L={legacy_hist[d]:4d}  T={typed_hist[d]:4d}  {bar_l}")
    print()
    print(f"median shift (typed - legacy) : {median_shift:+.2f}")
    print(f"targets moving > 0.30         : {moved_big} ({moved_big*100//n}%)")
    print(f"legacy >= 0.70                : {legacy_above_07} ({legacy_above_07*100//n}%)")
    print(f"typed  >= 0.70                : {typed_above_07} ({typed_above_07*100//n}%)")
    print(f"crossed DOWN through 0.70     : {crossed_down}")
    print()
    print("PLAY-1 DELTA (how the consulting/PDF confidence line would change):")
    print(f"  corpus mean legacy : {sum(l for _,l,_,_ in rows)/n*100:.0f}%")
    print(f"  corpus mean typed  : {sum(ty for _,_,ty,_ in rows)/n*100:.0f}%")
    print()
    by_drop = sorted(rows, key=lambda r: r[2] - r[1])
    print("TOP 20 DROPS (inflated-by-volume profiles):")
    for email, legacy, typed, bd in by_drop[:20]:
        print(f"  {email:<42} {legacy*100:3.0f}% -> {typed*100:3.0f}%  "
              f"echo={bd['echo']} acct={bd['account']} corrob={bd['corroborating']} ent={bd['entity']}")
    print()
    print("TOP 20 RISES:")
    for email, legacy, typed, bd in sorted(rows, key=lambda r: r[1] - r[2])[:20]:
        if typed - legacy <= 0:
            break
        print(f"  {email:<42} {legacy*100:3.0f}% -> {typed*100:3.0f}%  "
              f"echo={bd['echo']} acct={bd['account']} corrob={bd['corroborating']} ent={bd['entity']}")


if __name__ == "__main__":
    main()
