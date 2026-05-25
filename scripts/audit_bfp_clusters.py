#!/usr/bin/env python3
"""
S224 — BFP behavioral_hash_v1 cluster distribution audit.

Tests two hypotheses for the dominant `f9a5400a…` cluster found in S222/S222b:

  (a) K=3 collapse / default-bucket effect — empty-axis targets land in bucket 0
  (b) Genuine cross-corporate behavioral similarity

Output: docs/qa/S224_bfp_cluster_audit.md (markdown report with verdict + recos).

Read-only. No DB modification, no migration. Run from repo root with DB env vars set
(or via `docker compose exec api python scripts/audit_bfp_clusters.py`).
"""

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

import psycopg2
import psycopg2.extras


# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────

PREFIX_LEN = 16   # Same slice that drives PixelCat detail layer
TOP_N_CLUSTERS = 10
HASH_AXES = ("public_exposure", "geo_spread", "data_leaked")
N_BUCKETS = 20
OUT_PATH = "docs/qa/S224_bfp_cluster_audit.md"


def db_conn():
    """Connect to local Postgres. Adjust env reading if your setup differs."""
    return psycopg2.connect(
        host=os.getenv("PGHOST", "postgres"),
        port=int(os.getenv("PGPORT", "5432")),
        user=os.getenv("PGUSER", "xpose"),
        password=os.getenv("PGPASSWORD", "xpose"),
        dbname=os.getenv("PGDATABASE", "xpose"),
    )


# ─────────────────────────────────────────────────────────────
# Phase 1 — Distribution shape
# ─────────────────────────────────────────────────────────────

def phase1_distribution(cur):
    """Group all post-scan targets by hash prefix; return (total, top_clusters)."""
    cur.execute("""
        SELECT
            LEFT(bfp_behavioral_hash_v1, %s) AS prefix,
            COUNT(*) AS n_targets
        FROM targets
        WHERE bfp_behavioral_hash_v1 IS NOT NULL
          AND LENGTH(bfp_behavioral_hash_v1) >= %s
        GROUP BY prefix
        ORDER BY n_targets DESC
    """, (PREFIX_LEN, PREFIX_LEN))
    rows = cur.fetchall()
    total = sum(r["n_targets"] for r in rows)
    return total, list(rows)


# ─────────────────────────────────────────────────────────────
# Phase 2 — Top bucket content analysis
# ─────────────────────────────────────────────────────────────

def phase2_bucket_content(cur, prefix):
    """For a given prefix, fetch all member targets + their 3 hash axes."""
    cur.execute("""
        SELECT
            t.id,
            t.email,
            w.slug AS workspace_slug,
            t.profile_data->'fingerprint'->'axes' AS axes
        FROM targets t
        JOIN workspaces w ON w.id = t.workspace_id
        WHERE t.bfp_behavioral_hash_v1 LIKE %s
    """, (f"{prefix}%",))
    return cur.fetchall()


def axes_stats(members):
    """For each of the 3 hash axes, compute (count_present, count_null, mean, median, p10, p90)."""
    stats = {}
    for axis in HASH_AXES:
        values = []
        nulls = 0
        for m in members:
            axes = m["axes"] or {}
            v = axes.get(axis)
            if v is None:
                nulls += 1
            else:
                try:
                    values.append(float(v))
                except (TypeError, ValueError):
                    nulls += 1
        if values:
            values_sorted = sorted(values)
            n = len(values)
            mean = sum(values) / n
            median = values_sorted[n // 2]
            p10 = values_sorted[int(n * 0.10)]
            p90 = values_sorted[int(n * 0.90)]
            zeros = sum(1 for v in values if v < 0.05)  # near-zero bucket
            stats[axis] = {
                "n_present": n,
                "n_null": nulls,
                "mean": round(mean, 4),
                "median": round(median, 4),
                "p10": round(p10, 4),
                "p90": round(p90, 4),
                "near_zero_count": zeros,
                "near_zero_pct": round(100 * zeros / n, 1) if n else 0,
            }
        else:
            stats[axis] = {"n_present": 0, "n_null": nulls, "note": "all null"}
    return stats


# ─────────────────────────────────────────────────────────────
# Phase 3 — Verdict
# ─────────────────────────────────────────────────────────────

def render_verdict(total, top_clusters, top_bucket_stats):
    """Decide (a) K=3 collapse, (b) genuine cluster, or (c) mixed."""
    if not top_clusters:
        return "INSUFFICIENT_DATA", "No post-scan targets with behavioral_hash. Cannot audit."

    top = top_clusters[0]
    top_pct = round(100 * top["n_targets"] / total, 1)

    # Heuristic thresholds:
    #   top_bucket > 30% of total → suspicious concentration
    #   AND > 70% of top bucket members have near-zero values on all 3 axes → K=3 collapse confirmed
    near_zero_signal = all(
        s.get("near_zero_pct", 0) >= 70
        for s in top_bucket_stats.values()
        if s.get("n_present", 0) > 0
    )

    if top_pct >= 30 and near_zero_signal:
        verdict = "K3_COLLAPSE"
        reason = (
            f"Top bucket holds {top_pct}% of all targets ({top['n_targets']}/{total}). "
            f"In that bucket, all 3 hash axes are near-zero (≥70% of members) for the "
            f"axes that are present. This is the K=3 default-bucket signature: targets "
            f"with computed-but-empty axes collapse into a shared MinHash."
        )
    elif top_pct >= 30 and not near_zero_signal:
        verdict = "GENUINE_CLUSTER"
        reason = (
            f"Top bucket holds {top_pct}% of all targets but axes are NOT uniformly "
            f"near-zero. This is consistent with genuine cross-corporate behavioral "
            f"similarity — the hash correctly groups behaviorally similar targets."
        )
    elif top_pct < 30:
        verdict = "HEALTHY_DISTRIBUTION"
        reason = (
            f"Top bucket only holds {top_pct}% of targets — distribution is reasonable, "
            f"no dominant collapse signal."
        )
    else:
        verdict = "MIXED"
        reason = (
            f"Top bucket holds {top_pct}% but axis signal is ambiguous. Manual review needed."
        )
    return verdict, reason


# ─────────────────────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────────────────────

def write_report(total, top_clusters, top_bucket_stats, top_bucket_members, verdict, reason):
    lines = []
    lines.append(f"# S224 — BFP behavioral_hash_v1 cluster audit")
    lines.append("")
    lines.append(f"_Generated {datetime.utcnow().isoformat()}Z_")
    lines.append("")
    lines.append(f"**Total post-scan targets with behavioral_hash**: {total}")
    lines.append(f"**Distinct hash prefixes (16 hex chars)**: {len(top_clusters)}")
    lines.append("")
    lines.append(f"## Verdict: `{verdict}`")
    lines.append("")
    lines.append(reason)
    lines.append("")

    lines.append("## Phase 1 — Top hash prefixes")
    lines.append("")
    lines.append("| Rank | Prefix | Targets | % of total |")
    lines.append("|------|--------|---------|-----------|")
    for i, c in enumerate(top_clusters[:TOP_N_CLUSTERS], 1):
        pct = round(100 * c["n_targets"] / total, 1)
        lines.append(f"| {i} | `{c['prefix']}` | {c['n_targets']} | {pct}% |")
    lines.append("")

    if top_bucket_stats:
        top_prefix = top_clusters[0]["prefix"]
        lines.append(f"## Phase 2 — Top bucket `{top_prefix}` axis breakdown")
        lines.append("")
        lines.append("Of the 3 axes that drive the hash (S166):")
        lines.append("")
        lines.append("| Axis | n_present | n_null | mean | median | p10 | p90 | near_zero_pct |")
        lines.append("|------|-----------|--------|------|--------|-----|-----|---------------|")
        for axis, s in top_bucket_stats.items():
            if s.get("n_present", 0) > 0:
                lines.append(
                    f"| `{axis}` | {s['n_present']} | {s['n_null']} | "
                    f"{s['mean']} | {s['median']} | {s['p10']} | {s['p90']} | "
                    f"{s['near_zero_pct']}% |"
                )
            else:
                lines.append(f"| `{axis}` | 0 | {s['n_null']} | — | — | — | — | — |")
        lines.append("")

        # Sample 10 members of top bucket
        lines.append(f"### Sample members of top bucket (10 of {len(top_bucket_members)})")
        lines.append("")
        lines.append("| Workspace | Email | public_exposure | geo_spread | data_leaked |")
        lines.append("|-----------|-------|----------------|-----------|-------------|")
        for m in top_bucket_members[:10]:
            axes = m["axes"] or {}
            pe = axes.get("public_exposure", "—")
            gs = axes.get("geo_spread", "—")
            dl = axes.get("data_leaked", "—")
            lines.append(f"| {m['workspace_slug']} | `{m['email']}` | {pe} | {gs} | {dl} |")
        lines.append("")

    lines.append("## Reco")
    lines.append("")
    if verdict == "K3_COLLAPSE":
        lines.append("Three options, ranked:")
        lines.append("")
        lines.append("1. **Accept as feature** (cheapest) — document that the hash naturally "
                     "groups info-starved targets into a 'cold start' bucket. PixelCat "
                     "renders identical cats for info-starved targets, which is honest "
                     "(\"we don't know enough about these targets yet to differentiate them\").")
        lines.append("")
        lines.append("2. **Treat near-zero as None** (medium effort, ~5-line change in "
                     "`fingerprint_engine.py`) — bump the `is None` check to `if value is None "
                     "or value < epsilon`. Reduces collapse but loses signal on genuine "
                     "low-exposure targets.")
        lines.append("")
        lines.append("3. **Move to 11-axis hash** (BFP-level decision) — extend the input set "
                     "beyond the 3 invariant axes. Breaks the K=3 design lock. Versioning "
                     "required (`bfp_behavioral_hash_v2`).")
    elif verdict == "GENUINE_CLUSTER":
        lines.append("Narrative win — the hash is doing what it's designed to do. Surface "
                     "more aggressively in product (cluster explorer S225 candidate). No "
                     "engine change.")
    else:
        lines.append("No action required at engine level. Continue monitoring.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_Audit script: `scripts/audit_bfp_clusters.py`. Read-only. Re-run after "
                 "rescans / new corpus / engine changes to re-evaluate._")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    conn = db_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("Phase 1 — bucket distribution…")
    total, top_clusters = phase1_distribution(cur)
    print(f"  total={total}, distinct_prefixes={len(top_clusters)}")
    if top_clusters:
        top = top_clusters[0]
        print(f"  top prefix={top['prefix']} ({top['n_targets']} targets, "
              f"{round(100*top['n_targets']/total,1)}%)")

    print("Phase 2 — top bucket axis analysis…")
    top_bucket_members = []
    top_bucket_stats = {}
    if top_clusters:
        top_bucket_members = phase2_bucket_content(cur, top_clusters[0]["prefix"])
        top_bucket_stats = axes_stats(top_bucket_members)
        for axis, s in top_bucket_stats.items():
            if s.get("n_present", 0) > 0:
                print(f"  {axis}: mean={s['mean']} near_zero={s['near_zero_pct']}%")

    print("Phase 3 — verdict…")
    verdict, reason = render_verdict(total, top_clusters, top_bucket_stats)
    print(f"  {verdict}: {reason[:80]}…")

    print(f"Writing report to {OUT_PATH}…")
    report = write_report(total, top_clusters, top_bucket_stats, top_bucket_members, verdict, reason)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        f.write(report)
    print("Done.")

    conn.close()


if __name__ == "__main__":
    main()
