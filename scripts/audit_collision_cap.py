#!/usr/bin/env python3
"""
S261 — Collision coherence-cap blast-radius audit (read-only).

For every target with a resolved profile, recompute the S261 cap predicate
(collision_seed AND NOT anchor_corroborated) using the SAME logic shipped in
profile_aggregator.py, and report how many existing profiles would flip to the
≤35% "unverified_collision" state.

Acceptance gate (per spec): if >~15% of targets flip, the bare_hits threshold
or COMMON_GIVEN_NAMES is too aggressive — retune before merge, do NOT ship.

Strictly SELECT-only. No DB modification, no migration. Run from repo root:
  docker compose exec api python scripts/audit_collision_cap.py
"""

import os
import sys
from collections import Counter

import psycopg2
import psycopg2.extras

# Pure helpers — no DB dependency, safe to import here.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.services.layer4.collision_guard import is_collision_prone_localpart  # noqa: E402

BARE_HITS_THRESHOLD = 3   # mirror profile_aggregator.py
WARN_FRACTION = 0.15      # stop-and-retune gate


def db_conn():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "postgres"),
        port=int(os.getenv("PGPORT", "5432")),
        user=os.getenv("PGUSER", "xpose"),
        password=os.getenv("PGPASSWORD", "xpose"),
        dbname=os.getenv("PGDATABASE", "xpose"),
    )


def main():
    conn = db_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Echo-type findings (domain/email/ip) merely repeat the seed input — they
    # are neither collision accounts nor corroborators. Mirror of the cap logic
    # in profile_aggregator.py.
    ECHO_SQL = "('domain','email','ip')"

    cur.execute("""
        SELECT id, workspace_id, email
        FROM targets
        WHERE email IS NOT NULL AND email <> ''
    """)
    targets = cur.fetchall()

    total = 0
    would_cap = 0
    capped_rows = []
    by_local = Counter()

    for t in targets:
        email = (t["email"] or "").strip().lower()
        local, _, domain = email.partition("@")
        if not local:
            continue
        total += 1
        if not is_collision_prone_localpart(local):
            continue

        # bare_hits: distinct account sources where the surfaced handle == local
        cur.execute(f"""
            SELECT count(DISTINCT coalesce(data->>'source', data->>'scraper', module))
            FROM findings
            WHERE target_id = %s AND workspace_id = %s AND status = 'active'
              AND coalesce(indicator_type,'') NOT IN {ECHO_SQL}
              AND lower(coalesce(indicator_value,'')) = %s
        """, (t["id"], t["workspace_id"], local))
        bare_hits = cur.fetchone()["count"]
        if bare_hits < BARE_HITS_THRESHOLD:
            continue

        # anchor corroboration: an ACCOUNT finding references the email/domain
        anchor = False
        if domain:
            cur.execute(f"""
                SELECT 1 FROM findings
                WHERE target_id = %s AND workspace_id = %s AND status = 'active'
                  AND coalesce(indicator_type,'') NOT IN {ECHO_SQL}
                  AND (
                    lower(coalesce(url, '')) LIKE %s
                    OR lower(coalesce(indicator_value, '')) LIKE %s
                    OR lower(coalesce(data::text, '')) LIKE %s
                  )
                LIMIT 1
            """, (t["id"], t["workspace_id"], f"%{domain}%", f"%{domain}%", f"%{domain}%"))
            anchor = cur.fetchone() is not None

        if not anchor:
            would_cap += 1
            by_local[local] += 1
            capped_rows.append((email, bare_hits))

    cur.close()
    conn.close()

    frac = (would_cap / total) if total else 0.0
    print("=" * 60)
    print("S261 collision coherence-cap blast-radius audit")
    print("=" * 60)
    print(f"targets with email           : {total}")
    print(f"would flip to capped/unverified: {would_cap} ({frac * 100:.1f}%)")
    print(f"distinct collision local-parts : {len(by_local)}")
    print()
    print("top capped local-parts:")
    for local, n in by_local.most_common(15):
        print(f"  {local:<20} {n}")
    print()
    print("sample capped emails (first 20):")
    for email, hits in capped_rows[:20]:
        print(f"  {email:<45} bare_hits={hits}")
    print()
    if frac > WARN_FRACTION:
        print(f"!! {frac * 100:.1f}% > {WARN_FRACTION * 100:.0f}% — TOO AGGRESSIVE. "
              "Retune bare_hits threshold or COMMON_GIVEN_NAMES before merge.")
        sys.exit(2)
    print(f"OK — {frac * 100:.1f}% <= {WARN_FRACTION * 100:.0f}% flip rate. Safe to merge.")


if __name__ == "__main__":
    main()
