#!/usr/bin/env python3
"""
BFP invariance diagnostic — measure per-axis stability across fingerprint_history snapshots.

Read-only. Outputs Markdown + JSON to docs/diag/.

Usage:
    docker compose exec api python scripts/bfp_invariance_diag.py
    docker compose exec api python scripts/bfp_invariance_diag.py --workspace friends
    docker compose exec api python scripts/bfp_invariance_diag.py --limit 50
    docker compose exec api python scripts/bfp_invariance_diag.py --output-dir /tmp/diag
"""
import argparse
import json
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from api.tasks.utils import get_sync_session
from api.models.target import Target
from api.models.workspace import Workspace


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--workspace", default=None, help="Filter by workspace slug")
    p.add_argument("--limit", type=int, default=None, help="Cap analyzed targets")
    p.add_argument("--output-dir", default="docs/diag", help="Output dir (default: docs/diag)")
    p.add_argument("--date", default=None, help="Date string for output filenames (default: UTC today). Use this when the operator's local date differs from container UTC.")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Data fetch + extraction
# ---------------------------------------------------------------------------

def fetch_targets(session, workspace_slug: str | None = None, limit: int | None = None) -> list:
    """Fetch targets with non-null fingerprint_history. JSONB length filter happens in Python."""
    stmt = select(Target).where(Target.fingerprint_history.isnot(None))
    if workspace_slug:
        ws = session.execute(select(Workspace).where(Workspace.slug == workspace_slug)).scalar_one_or_none()
        if ws is None:
            print(f"ERROR: workspace slug '{workspace_slug}' not found", file=sys.stderr)
            sys.exit(2)
        stmt = stmt.where(Target.workspace_id == ws.id)
    if limit:
        stmt = stmt.limit(limit)
    return session.execute(stmt).scalars().all()


def extract_axis_series(target) -> dict[str, list[float]]:
    """From a target's fingerprint_history list, extract per-axis time series.

    Snapshot shape (verified 2026-05-23 via psql sample):
        {"axes": {<axis_name>: float}, "raw_values": {...}, "score": int,
         "hash": str, "computed_at": ISO, "scan_id": uuid, ...}

    Older snapshots (pre-S145/S147) may lack `formal_records` / `network_signature`
    axes — the series for those axes will be shorter for affected targets.
    """
    series: dict[str, list[float]] = defaultdict(list)
    for snap in target.fingerprint_history or []:
        axes = snap.get("axes") if isinstance(snap, dict) else None
        if not isinstance(axes, dict):
            continue
        for axis_name, value in axes.items():
            if isinstance(value, (int, float)):
                series[axis_name].append(float(value))
    return dict(series)


# ---------------------------------------------------------------------------
# Per-target per-axis metrics
# ---------------------------------------------------------------------------

def compute_target_axis_metrics(values: list[float]) -> dict | None:
    """Return metrics dict, or None if <2 values (no delta computable)."""
    if len(values) < 2:
        return None
    deltas = [abs(values[i + 1] - values[i]) for i in range(len(values) - 1)]
    mean_val = statistics.mean(values)
    stdev = statistics.stdev(values) if len(values) >= 2 else 0.0
    # CV = stdev / mean. When mean is 0 we use 0 to avoid div-by-zero — semantically a
    # constant-zero axis is perfectly stable, so CV=0 is the right read.
    cv = (stdev / mean_val) if mean_val > 0 else 0.0
    return {
        "mean_abs_delta": statistics.mean(deltas),
        "max_delta": max(deltas),
        "cv": cv,
        "range": max(values) - min(values),
        "mean_value": mean_val,
        "stdev": stdev,
        "n_snapshots": len(values),
    }


# ---------------------------------------------------------------------------
# Cross-target aggregation
# ---------------------------------------------------------------------------

def aggregate_axis_metrics(all_target_metrics: dict) -> dict[str, dict]:
    """For each axis seen in ≥1 target, compute corpus-wide aggregates.

    Two complementary signals reported per axis:
      - Intra-target stability: mean_of_mean_abs_delta, mean_cv, max_range
        (axis stays the same for ONE person across their snapshots)
      - Inter-target discrimination: across_targets_stdev, across_targets_unique_count
        (axis varies BETWEEN people — required for the canonical hash to discriminate)

    A canonical-hash-worthy axis needs BOTH: low intra-target delta AND high inter-target
    spread. An axis that's constant for everyone (no discrimination) scores perfectly on
    stability but is useless. The script reports both; the operator picks K weighing both.
    """
    by_axis: dict[str, list[dict]] = defaultdict(list)
    for tid, axes in all_target_metrics.items():
        for axis_name, m in axes.items():
            if m is not None:
                by_axis[axis_name].append(m)

    aggregates = {}
    for axis_name, metrics_list in by_axis.items():
        mads = [m["mean_abs_delta"] for m in metrics_list]
        cvs = [m["cv"] for m in metrics_list]
        ranges = [m["range"] for m in metrics_list]
        # Inter-target: take each target's mean value as its "characteristic" value for the axis,
        # then look at the spread across the population.
        per_target_means = [m["mean_value"] for m in metrics_list]
        across_stdev = statistics.stdev(per_target_means) if len(per_target_means) >= 2 else 0.0
        across_min = min(per_target_means) if per_target_means else 0.0
        across_max = max(per_target_means) if per_target_means else 0.0
        # Discrete-bucket count: how many distinct ~0.01-bucket values do we see across the population?
        unique_buckets = len({round(v, 2) for v in per_target_means})
        aggregates[axis_name] = {
            "n_targets": len(metrics_list),
            # intra-target stability
            "mean_of_mean_abs_delta": statistics.mean(mads),
            "median_of_mean_abs_delta": statistics.median(mads),
            "mean_cv": statistics.mean(cvs),
            "mean_range": statistics.mean(ranges),
            "max_range_observed": max(ranges),
            # inter-target discrimination
            "across_targets_stdev": across_stdev,
            "across_targets_min": across_min,
            "across_targets_max": across_max,
            "across_targets_unique_buckets": unique_buckets,
        }
    return aggregates


def rank_axes_by_stability(aggregates: dict) -> list[tuple[str, dict]]:
    """Ascending by mean_of_mean_abs_delta — most stable first."""
    return sorted(aggregates.items(), key=lambda kv: kv[1]["mean_of_mean_abs_delta"])


# ---------------------------------------------------------------------------
# Per-target deep dive selection
# ---------------------------------------------------------------------------

def _target_avg_delta(target_metrics: dict) -> float:
    """Mean of per-axis mean_abs_delta for one target. Used to rank targets by overall stability."""
    vals = [m["mean_abs_delta"] for m in target_metrics.values() if m is not None]
    return statistics.mean(vals) if vals else float("inf")


def select_deep_dive_samples(all_metrics: dict, aggregates: dict) -> dict:
    """Pick most-stable / least-stable / outlier targets for the per-target section."""
    if not all_metrics:
        return {"most_stable": [], "least_stable": [], "outliers": []}

    rated = [(tid, _target_avg_delta(m)) for tid, m in all_metrics.items()]
    rated_sorted = sorted(rated, key=lambda x: x[1])

    most_stable_ids = [tid for tid, _ in rated_sorted[:3]]
    least_stable_ids = [tid for tid, _ in rated_sorted[-3:][::-1]]

    # Outlier = target where any axis mean_abs_delta exceeds the per-axis p95
    p95_per_axis = {}
    for axis_name, agg in aggregates.items():
        deltas_for_axis = [
            m[axis_name]["mean_abs_delta"]
            for m in all_metrics.values()
            if m.get(axis_name) is not None
        ]
        if len(deltas_for_axis) >= 20:
            deltas_for_axis.sort()
            p95_per_axis[axis_name] = deltas_for_axis[int(len(deltas_for_axis) * 0.95)]
        else:
            p95_per_axis[axis_name] = max(deltas_for_axis) if deltas_for_axis else 0.0

    outliers: list[dict] = []
    for tid, axes_metrics in all_metrics.items():
        bad_axes = []
        for axis_name, m in axes_metrics.items():
            if m is None:
                continue
            if m["mean_abs_delta"] > p95_per_axis.get(axis_name, 0):
                bad_axes.append((axis_name, m["mean_abs_delta"]))
        if bad_axes:
            outliers.append({
                "target_id": tid,
                "exceeding_axes": [{"axis": a, "mean_abs_delta": d} for a, d in bad_axes],
            })
    outliers.sort(key=lambda o: -len(o["exceeding_axes"]))
    outliers = outliers[:5]

    def detail(tid: str) -> dict:
        axes_metrics = all_metrics[tid]
        valid = [(a, m) for a, m in axes_metrics.items() if m is not None]
        valid.sort(key=lambda kv: kv[1]["mean_abs_delta"])
        return {
            "target_id": tid,
            "n_axes_measured": len(valid),
            "snapshots": valid[0][1]["n_snapshots"] if valid else 0,
            "top3_stable": [{"axis": a, "mean_abs_delta": round(m["mean_abs_delta"], 6)} for a, m in valid[:3]],
            "top3_drifting": [{"axis": a, "mean_abs_delta": round(m["mean_abs_delta"], 6)} for a, m in valid[-3:][::-1]],
        }

    return {
        "most_stable": [detail(t) for t in most_stable_ids],
        "least_stable": [detail(t) for t in least_stable_ids],
        "outliers": outliers,
    }


# ---------------------------------------------------------------------------
# Cumulative coverage
# ---------------------------------------------------------------------------

def cumulative_coverage(ranked: list) -> list[dict]:
    """For K = 1..N, sum of inverse-delta weights of top-K axes as % of total inverse-delta sum.

    Inverse-delta is computed as 1 / (mean_of_mean_abs_delta + 1e-9). This gives axes that are
    nearly invariant a huge weight (because 1/x → ∞ as x → 0), but the normalization to % of
    total still places them on a 0-100% scale. Lets us read "top-K axes capture X% of
    stability budget".
    """
    weights = [(axis, 1.0 / (agg["mean_of_mean_abs_delta"] + 1e-9)) for axis, agg in ranked]
    total = sum(w for _, w in weights)
    cumulative = []
    running = 0.0
    included: list[str] = []
    for k, (axis, w) in enumerate(weights, start=1):
        running += w
        included.append(axis)
        cumulative.append({
            "k": k,
            "axes": list(included),
            "coverage_pct": round(100.0 * running / total, 2) if total > 0 else 0.0,
        })
    return cumulative


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def get_head_sha() -> str:
    """Read HEAD sha directly from .git/ — no git binary required (containers often
    don't ship git). Falls back to subprocess if .git is missing."""
    for repo_root in ("/app", str(Path(__file__).resolve().parents[1])):
        head_file = Path(repo_root) / ".git" / "HEAD"
        if head_file.is_file():
            try:
                ref_line = head_file.read_text().strip()
                if ref_line.startswith("ref: "):
                    ref_path = Path(repo_root) / ".git" / ref_line[5:]
                    if ref_path.is_file():
                        return ref_path.read_text().strip()[:8]
                else:
                    return ref_line[:8]  # detached HEAD with raw sha
            except Exception:
                pass
    try:
        return subprocess.check_output(["git", "rev-parse", "--short=8", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"


def write_markdown_report(path: Path, head_sha: str, corpus: dict,
                           aggregates: dict, ranked: list,
                           samples: dict, coverage: list) -> None:
    lines: list[str] = []
    report_date = corpus.get("report_date") or datetime.now(timezone.utc).date().isoformat()
    lines.append(f"# BFP invariance diagnostic — {report_date}")
    lines.append("")
    lines.append(f"**HEAD:** `{head_sha}`")
    lines.append(f"**Workspace scope:** `{corpus['workspace_filter']}`")
    lines.append(
        f"**Corpus:** {corpus['total_targets_analyzed']} targets analyzed (≥2 snapshots), "
        f"avg {corpus['avg_snapshots']:.2f} snapshots/target "
        f"(min={corpus['min_snapshots']}, max={corpus['max_snapshots']})"
    )
    lines.append("**Methodology:** per S165 spec — mean absolute delta + CV + range per (target, axis), aggregated across corpus.")
    lines.append("")
    lines.append("Snapshot shape (verified via psql before run): `{\"axes\": {<name>: float}, \"raw_values\": {...}, \"score\": int, \"hash\": str, \"computed_at\": ISO}`.")
    lines.append("Older snapshots (pre-S145 / pre-S147) lack `formal_records` / `network_signature` axes — affected targets contribute shorter series for those axes; `n_targets` per axis reflects the actual observed coverage.")
    lines.append("")

    # Section 1
    lines.append("## 1. Axis stability ranking")
    lines.append("")
    lines.append("Ascending by `mean_of_mean_abs_delta` (most stable first).")
    lines.append("")
    lines.append("Two complementary signals: **intra-target stability** (axis doesn't drift for ONE person across re-scans — `Mean abs delta` low) AND **inter-target discrimination** (axis varies BETWEEN people — `Across-pop stdev` non-trivial, `Unique` buckets > a handful). A canonical-hash-worthy axis needs BOTH.")
    lines.append("")
    lines.append("| Rank | Axis | Mean abs delta | Median abs delta | Mean range | Max range | Across-pop stdev | Across-pop min..max | Unique | N targets |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for rank, (axis, agg) in enumerate(ranked, start=1):
        lines.append(
            f"| {rank} | `{axis}` | "
            f"{agg['mean_of_mean_abs_delta']:.6f} | "
            f"{agg['median_of_mean_abs_delta']:.6f} | "
            f"{agg['mean_range']:.4f} | "
            f"{agg['max_range_observed']:.4f} | "
            f"{agg['across_targets_stdev']:.4f} | "
            f"{agg['across_targets_min']:.3f}..{agg['across_targets_max']:.3f} | "
            f"{agg['across_targets_unique_buckets']} | "
            f"{agg['n_targets']} |"
        )
    lines.append("")

    # Section 2
    lines.append("## 2. Cumulative coverage")
    lines.append("")
    lines.append("If we include only the top K most-stable axes, what fraction of the inverse-stability budget do they capture?")
    lines.append("")
    lines.append("| K | Axes included | Cumulative coverage |")
    lines.append("|---|---|---|")
    for entry in coverage:
        axes_str = " · ".join(f"`{a}`" for a in entry["axes"])
        lines.append(f"| {entry['k']} | {axes_str} | {entry['coverage_pct']}% |")
    lines.append("")
    # Detect knee — point where adding one more axis adds <5% coverage
    knee_k = None
    for i, entry in enumerate(coverage):
        prev = coverage[i - 1]["coverage_pct"] if i > 0 else 0.0
        if i > 0 and entry["coverage_pct"] - prev < 5.0:
            knee_k = entry["k"] - 1
            break
    if knee_k:
        lines.append(f"**Observation:** curve shows a knee at K={knee_k} — beyond this, each added axis contributes <5% additional inverse-stability coverage.")
    else:
        lines.append("**Observation:** no clear knee — coverage grows roughly linearly with K.")
    lines.append("")

    # Section 3
    lines.append("## 3. Per-target deep dive")
    lines.append("")

    def render_sample_group(title: str, group: list[dict]) -> None:
        lines.append(f"### {title}")
        lines.append("")
        if not group:
            lines.append("_(no targets in this group)_")
            lines.append("")
            return
        for s in group:
            lines.append(f"- **`{s['target_id']}`** — {s['snapshots']} snapshots, {s['n_axes_measured']} axes measured")
            lines.append("  - Top 3 stable: " + ", ".join(f"`{x['axis']}` ({x['mean_abs_delta']:.4f})" for x in s["top3_stable"]))
            lines.append("  - Top 3 drifting: " + ", ".join(f"`{x['axis']}` ({x['mean_abs_delta']:.4f})" for x in s["top3_drifting"]))
        lines.append("")

    render_sample_group("Most-stable target sample (3 targets)", samples["most_stable"])
    render_sample_group("Least-stable target sample (3 targets)", samples["least_stable"])

    lines.append("### Outliers")
    lines.append("")
    if samples["outliers"]:
        lines.append("Targets where one or more axes exceed the corpus p95 mean_abs_delta. Top 5 by exceeding-axis count.")
        lines.append("")
        for o in samples["outliers"]:
            ax_str = ", ".join(f"`{x['axis']}`({x['mean_abs_delta']:.4f})" for x in o["exceeding_axes"][:6])
            lines.append(f"- **`{o['target_id']}`** — {len(o['exceeding_axes'])} axes above p95: {ax_str}")
        lines.append("")
    else:
        lines.append("_(no outliers detected — distribution is narrow)_")
        lines.append("")

    # Section 4
    lines.append("## 4. Recommendation for S166")
    lines.append("")
    # Threshold-free recommendation: report the K range that captures 70-90% of coverage
    k_70 = next((c["k"] for c in coverage if c["coverage_pct"] >= 70.0), None)
    k_90 = next((c["k"] for c in coverage if c["coverage_pct"] >= 90.0), None)
    top1 = ranked[0][0] if ranked else "(none)"
    top3 = [a for a, _ in ranked[:3]]
    lines.append(f"Based on observed distribution across {corpus['total_targets_analyzed']} targets:")
    lines.append("")
    # Cumulative coverage is dominated by axes with near-zero delta (1/x explosion when delta→0).
    # Don't over-rely on it; the per-axis table with intra+inter signals is the actual decision tool.
    if k_70 and k_90 and k_70 != k_90:
        lines.append(f"- **Coverage-curve suggested K range:** K={k_70}..{k_90} (≥70%..≥90% of inverse-stability budget).")
    else:
        lines.append("- **Coverage-curve degenerate:** ≥1 axis has near-zero mean_abs_delta (perfectly invariant per-target), so the inverse-stability weight collapses to that axis. Don't read K from coverage alone — read the per-axis table.")
    lines.append("")
    # Compute axes that pass BOTH stability + discrimination thresholds
    discriminating_stable = []
    for axis, agg in ranked:
        if agg["mean_of_mean_abs_delta"] < 0.05 and agg["across_targets_unique_buckets"] >= 10:
            discriminating_stable.append(axis)
    lines.append(f"- **Most stable single axis (lowest delta):** `{top1}`.")
    lines.append(f"- **Top 3 most stable:** {', '.join(f'`{a}`' for a in top3)}.")
    if discriminating_stable:
        lines.append(f"- **Stable AND discriminating** (mean_abs_delta < 0.05 AND ≥10 unique-bucket values across targets): {', '.join(f'`{a}`' for a in discriminating_stable)} — best candidates for canonical hash inclusion.")
    else:
        lines.append("- **Stable AND discriminating:** none meet both thresholds in this corpus. Consider relaxing — or accept that all stable axes are also low-variance.")
    lines.append("")
    # Caveats: axes with low mean delta but high max range
    caveats = []
    for axis, agg in ranked:
        if agg["mean_of_mean_abs_delta"] < 0.05 and agg["max_range_observed"] > 0.5:
            caveats.append(f"`{axis}` is stable on average (mean_abs_delta={agg['mean_of_mean_abs_delta']:.4f}) but has been observed to swing as much as {agg['max_range_observed']:.2f} for at least one target — investigate the affected target before relying on it for canonical hash")
    if caveats:
        lines.append("- **Caveats (stable-mean, high-tail):**")
        for c in caveats:
            lines.append(f"  - {c}")
        lines.append("")
    lines.append("- **Decision deferred to operator:** the exact K and any per-axis weighting in MinHash construction. This report measures, it does not decide.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"_Generated by `scripts/bfp_invariance_diag.py` at {datetime.now(timezone.utc).isoformat()}._")
    lines.append("")
    path.write_text("\n".join(lines))


def write_json_sidecar(path: Path, head_sha: str, corpus: dict,
                        all_metrics: dict, aggregates: dict,
                        ranked: list, coverage: list) -> None:
    payload = {
        "meta": {
            "head_sha": head_sha,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "workspace_filter": corpus["workspace_filter"],
            "corpus": {
                "total_targets": corpus["total_targets_analyzed"],
                "avg_snapshots": corpus["avg_snapshots"],
                "min_snapshots": corpus["min_snapshots"],
                "max_snapshots": corpus["max_snapshots"],
            },
        },
        "aggregates": aggregates,
        "ranked_axes": [
            {"rank": i + 1, "axis": axis, "mean_abs_delta": agg["mean_of_mean_abs_delta"]}
            for i, (axis, agg) in enumerate(ranked)
        ],
        "cumulative_coverage": coverage,
        "per_target": all_metrics,
    }
    path.write_text(json.dumps(payload, indent=2, default=str))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    session = get_sync_session()
    try:
        targets = fetch_targets(session, args.workspace, args.limit)
        targets_with_history = [
            t for t in targets
            if isinstance(t.fingerprint_history, list) and len(t.fingerprint_history) >= 2
        ]
        print(f"Analyzing {len(targets_with_history)} targets with ≥2 snapshots...", file=sys.stderr)

        all_metrics: dict[str, dict] = {}
        for t in targets_with_history:
            series = extract_axis_series(t)
            all_metrics[str(t.id)] = {
                axis: compute_target_axis_metrics(values)
                for axis, values in series.items()
            }

        aggregates = aggregate_axis_metrics(all_metrics)
        ranked = rank_axes_by_stability(aggregates)
        samples = select_deep_dive_samples(all_metrics, aggregates)
        coverage = cumulative_coverage(ranked)

        snapshot_lengths = [len(t.fingerprint_history) for t in targets_with_history]
        date_str = args.date or datetime.now(timezone.utc).date().isoformat()
        corpus = {
            "total_targets_analyzed": len(targets_with_history),
            "workspace_filter": args.workspace or "all",
            "avg_snapshots": round(statistics.mean(snapshot_lengths), 2) if snapshot_lengths else 0.0,
            "min_snapshots": min(snapshot_lengths) if snapshot_lengths else 0,
            "max_snapshots": max(snapshot_lengths) if snapshot_lengths else 0,
            "report_date": date_str,
        }
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        md_path = out_dir / f"invariance_{date_str}.md"
        json_path = out_dir / f"invariance_{date_str}.json"

        head_sha = get_head_sha()
        write_markdown_report(md_path, head_sha, corpus, aggregates, ranked, samples, coverage)
        write_json_sidecar(json_path, head_sha, corpus, all_metrics, aggregates, ranked, coverage)

        print(f"Done — {md_path}", file=sys.stderr)
        print(f"     — {json_path}", file=sys.stderr)
    finally:
        session.close()


if __name__ == "__main__":
    main()
