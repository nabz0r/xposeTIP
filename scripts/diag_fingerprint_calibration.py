"""S143 — fingerprint calibration diagnostic.

One-shot analysis script. Reads target.profile_data['fingerprint'] for every
target in a workspace, computes per-axis distribution stats, recomputes the
FULL pairwise cosine similarity distribution (ignoring the 0.70 storage filter
applied in similarity_engine), and emits a Markdown + JSON report to docs/diag/.

Read-only on DB. Touches no production code.

Usage:
    docker compose exec api python scripts/diag_fingerprint_calibration.py --workspace <slug>
"""
import argparse
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from sqlalchemy import select

from api.tasks.utils import get_sync_session
from api.models.workspace import Workspace
from api.models.target import Target
from api.services.layer4.similarity_engine import FINGERPRINT_AXES, _extract_axes, _cosine
from api.services.layer4.fingerprint_engine import FingerprintEngine

SCRIPT_VERSION = "S143-v1"

# Mirror of FingerprintEngine._normalize() mapping, reversed (axis_name → raw_key).
AXIS_RAW_KEYS = {
    "accounts": "accounts",
    "platforms": "platforms",
    "username_reuse": "username_reuse",
    "breaches": "breaches",
    "geo_spread": "geo_spread",
    "data_leaked": "data_leaked",
    "email_age": "email_age_years",
    "security": "security_weak",
    "public_exposure": "public_exposure_raw",
    "formal_records": "formal_records_raw",
}

POPULATED_THRESHOLD = 0.1  # Axes with normalized value > 0.1 count as "meaningfully populated"


# ─── Stat helpers ────────────────────────────────────────────────────────────

def _safe_stdev(vals):
    return statistics.stdev(vals) if len(vals) >= 2 else 0.0


def _safe_quantile(vals, q):
    """q ∈ [0.1, 0.5, 0.9]. Returns None if insufficient data."""
    if len(vals) < 2:
        return None
    qs = statistics.quantiles(sorted(vals), n=10)
    # quantiles(n=10) returns 9 cut points: q[0]=10th pct, q[4]=50th, q[8]=90th
    idx = {0.1: 0, 0.5: 4, 0.9: 8}[q]
    return qs[idx]


def _histogram(vals, n_bins=10, lo=0.0, hi=1.0):
    """Returns list[int] of length n_bins. Last bin includes hi."""
    if not vals:
        return [0] * n_bins
    width = (hi - lo) / n_bins
    counts = [0] * n_bins
    for v in vals:
        if v >= hi:
            counts[n_bins - 1] += 1
        elif v < lo:
            counts[0] += 1
        else:
            idx = int((v - lo) / width)
            if idx >= n_bins:
                idx = n_bins - 1
            counts[idx] += 1
    return counts


def _ascii_bar(counts, width=10):
    """Convert a histogram list to a single-line ASCII bar string."""
    if not any(counts):
        return "·" * len(counts)
    blocks = " ▁▂▃▄▅▆▇█"
    mx = max(counts)
    return "".join(blocks[min(8, int((c / mx) * 8))] if c > 0 else "·" for c in counts)


def _axis_stats(vals, raw=False, axis_max=None):
    """Return dict of axis distribution stats. Empty list → all zeros / None."""
    n = len(vals)
    if n == 0:
        base = {"n": 0, "mean": 0.0, "stdev": 0.0, "min": 0.0, "max": 0.0,
                "p10": None, "p50": None, "p90": None, "hist": [0] * 10}
        if raw:
            base["pct_at_max"] = 0.0
        else:
            base["pct_zero"] = 0.0
            base["pct_saturated"] = 0.0
        return base
    if raw and axis_max is not None:
        # Raw values can exceed AXIS_MAX. Histogram normalized to [0, AXIS_MAX]
        # then clipped — gives a sense of how much overflow exists.
        hist_hi = float(axis_max)
        hist = _histogram(vals, n_bins=10, lo=0.0, hi=hist_hi)
        pct_at_max = 100.0 * sum(1 for v in vals if v >= axis_max) / n
    else:
        hist = _histogram(vals, n_bins=10, lo=0.0, hi=1.0)
        pct_zero = 100.0 * sum(1 for v in vals if v == 0.0) / n
        pct_saturated = 100.0 * sum(1 for v in vals if v >= 0.999) / n
    out = {
        "n": n,
        "mean": statistics.mean(vals),
        "stdev": _safe_stdev(vals),
        "min": min(vals),
        "max": max(vals),
        "p10": _safe_quantile(vals, 0.1),
        "p50": _safe_quantile(vals, 0.5),
        "p90": _safe_quantile(vals, 0.9),
        "hist": hist,
    }
    if raw:
        out["pct_at_max"] = pct_at_max
    else:
        out["pct_zero"] = pct_zero
        out["pct_saturated"] = pct_saturated
    return out


def _fmt(v, dp=3):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{dp}f}"
    return str(v)


# ─── Markdown rendering ──────────────────────────────────────────────────────

def render_md(report):
    ws = report["workspace"]
    summary = report["summary"]
    lines = []
    push = lines.append

    push(f"# Fingerprint calibration diagnostic — {ws['slug']}")
    push("")
    push(f"_Generated {report['generated_at_utc']} · script {report['version']}_")
    push("")

    # Section A
    push("## A — Summary")
    push("")
    push(f"- Workspace: **{ws['name']}** (`{ws['slug']}`, id `{ws['id']}`)")
    push(f"- Total targets: **{summary['n_total']}**")
    push(f"- Targets with fingerprint key: **{summary['n_with_fingerprint']}**")
    push(f"- Targets with extractable axes (_extract_axes ≠ None): **{summary['n_extractable']}**")
    push("")

    # Section B
    push("## B — Per-axis normalized distribution")
    push("")
    if not report["axes_normalized"]:
        push("_No extractable fingerprints — section skipped._")
        push("")
    else:
        push("| axis | n | mean | stdev | min | max | %=0 | %sat | p10 | p50 | p90 |")
        push("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
        for axis in FINGERPRINT_AXES:
            s = report["axes_normalized"][axis]
            push(f"| {axis} | {s['n']} | {_fmt(s['mean'])} | {_fmt(s['stdev'])} | "
                 f"{_fmt(s['min'])} | {_fmt(s['max'])} | "
                 f"{_fmt(s['pct_zero'], 1)} | {_fmt(s['pct_saturated'], 1)} | "
                 f"{_fmt(s['p10'])} | {_fmt(s['p50'])} | {_fmt(s['p90'])} |")
        push("")
        push("Histogram bars (bin width 0.1, last bin includes 1.0):")
        push("")
        push("```")
        push("axis               0───────────────────────1")
        for axis in FINGERPRINT_AXES:
            bar = _ascii_bar(report["axes_normalized"][axis]["hist"])
            push(f"{axis:<18} {bar}")
        push("```")
        push("")

    # Section C
    push("## C — Per-axis raw distribution")
    push("")
    if report["axes_raw"] is None:
        push("_No `raw_values` key on sampled fingerprints — section skipped._")
        push("")
    else:
        push("| axis (raw key) | n | mean | stdev | min | max | ≥AXIS_MAX | p10 | p50 | p90 |")
        push("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
        for axis in FINGERPRINT_AXES:
            raw_key = AXIS_RAW_KEYS[axis]
            s = report["axes_raw"][axis]
            axis_max = FingerprintEngine.AXIS_MAX.get(raw_key, "?")
            push(f"| {axis} (`{raw_key}`, max={axis_max}) | {s['n']} | "
                 f"{_fmt(s['mean'])} | {_fmt(s['stdev'])} | "
                 f"{_fmt(s['min'])} | {_fmt(s['max'])} | "
                 f"{_fmt(s['pct_at_max'], 1)} | "
                 f"{_fmt(s['p10'])} | {_fmt(s['p50'])} | {_fmt(s['p90'])} |")
        push("")
        push("Raw histogram bars (binned to [0, AXIS_MAX], last bin captures saturation):")
        push("")
        push("```")
        push("axis               0───────────────────AXIS_MAX")
        for axis in FINGERPRINT_AXES:
            bar = _ascii_bar(report["axes_raw"][axis]["hist"])
            push(f"{axis:<18} {bar}")
        push("```")
        push("")

    # Section D
    push("## D — Rich-target count")
    push("")
    push(f"Targets where ≥K of 9 axes have normalized value > {POPULATED_THRESHOLD}:")
    push("")
    push("| K | count | % of n_extractable |")
    push("|--:|--:|--:|")
    n_ext = summary["n_extractable"]
    for k in [3, 5, 7, 9]:
        cnt = report["rich_targets"].get(str(k), 0)
        pct = (100.0 * cnt / n_ext) if n_ext else 0.0
        push(f"| {k} | {cnt} | {_fmt(pct, 1)}% |")
    push("")

    # Section E
    push("## E — Pairwise cosine similarity (fresh recompute, full distribution)")
    push("")
    sim = report["similarity"]
    if sim is None:
        push("_Fewer than 2 extractable targets — no pairs possible._")
        push("")
    else:
        push(f"- Total unique pairs: **{sim['total_pairs']}** (N·(N-1)/2)")
        push(f"- Ignoring the 0.70 storage filter applied by `similarity_engine`")
        push(f"- mean = {_fmt(sim['mean'])} · stdev = {_fmt(sim['stdev'])}")
        push("")
        push("| threshold | count ≥ | % of pairs |")
        push("|--:|--:|--:|")
        for t in [0.5, 0.6, 0.7, 0.8, 0.9]:
            entry = sim["above"][str(t)]
            push(f"| {t} | {entry['count']} | {_fmt(entry['pct'], 2)}% |")
        push("")
        push("Histogram (bin width 0.1):")
        push("")
        push("```")
        push("similarity         0───────────────────────1")
        push(f"pair density       {_ascii_bar(sim['hist'])}")
        push("```")
        push("")
        pct_70 = sim["above"]["0.7"]["pct"]
        push(f"**Threshold sanity:** {_fmt(pct_70, 2)}% of pairs ≥ 0.7. "
             f"If > 5% → threshold likely too low. If < 0.1% → threshold too high or vectors too noisy.")
        push("")

    # Section F
    push("## F — Top 20 highest-similarity pairs (fresh recompute)")
    push("")
    if not report["top_pairs"]:
        push("_No pairs computed._")
        push("")
    else:
        push("| rank | sim | target a (email) | target b (email) | top-3 co-axes |")
        push("|--:|--:|---|---|---|")
        for p in report["top_pairs"]:
            top_axes = ", ".join(p["top_axes"])
            push(f"| {p['rank']} | {_fmt(p['sim'])} | "
                 f"`{p['a']['email']}` | `{p['b']['email']}` | {top_axes} |")
        push("")

    # Section G
    push("## G — Auto-flagged observations")
    push("")
    if not report["observations"]:
        push("_No auto-flags raised._")
    else:
        for obs in report["observations"]:
            push(f"- {obs}")
    push("")
    push("---")
    push("")
    push("_Heuristic flags only. Read the data above and decide. Re-run this script "
         "after data growth or normalization tweaks to track drift._")

    return "\n".join(lines) + "\n"


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--workspace", help="Workspace slug")
    parser.add_argument("--out-dir", default="docs/diag")
    args = parser.parse_args()

    session = get_sync_session()
    try:
        if not args.workspace:
            wss = session.execute(select(Workspace).order_by(Workspace.slug)).scalars().all()
            print("Available workspaces:")
            for w in wss:
                print(f"  {w.slug}\t{w.name}")
            print("\nPass --workspace <slug> to run.", file=sys.stderr)
            return 1

        ws = session.execute(select(Workspace).where(Workspace.slug == args.workspace)).scalar_one_or_none()
        if not ws:
            wss = session.execute(select(Workspace).order_by(Workspace.slug)).scalars().all()
            print(f"Workspace slug '{args.workspace}' not found.", file=sys.stderr)
            print("Available:", file=sys.stderr)
            for w in wss:
                print(f"  {w.slug}", file=sys.stderr)
            return 1

        t_start = datetime.now(timezone.utc)
        targets = session.execute(select(Target).where(Target.workspace_id == ws.id)).scalars().all()
        n_total = len(targets)

        # Classify
        with_fp = []
        extractable = []
        for t in targets:
            pd_ = t.profile_data or {}
            if isinstance(pd_, dict) and "fingerprint" in pd_:
                with_fp.append(t)
            if _extract_axes(t) is not None:
                extractable.append(t)
        n_with_fingerprint = len(with_fp)
        n_extractable = len(extractable)

        # ─── Section B: normalized axes ──────────────────────────────────
        axes_normalized = {}
        if n_with_fingerprint > 0:
            for axis in FINGERPRINT_AXES:
                vals = []
                for t in with_fp:
                    axes_dict = (t.profile_data["fingerprint"].get("axes") or {})
                    vals.append(float(axes_dict.get(axis, 0.0) or 0.0))
                axes_normalized[axis] = _axis_stats(vals, raw=False)

        # ─── Section C: raw axes ─────────────────────────────────────────
        axes_raw = None
        if with_fp:
            sample_raw = (with_fp[0].profile_data["fingerprint"].get("raw_values") or {})
            if sample_raw:
                axes_raw = {}
                for axis in FINGERPRINT_AXES:
                    raw_key = AXIS_RAW_KEYS[axis]
                    axis_max = FingerprintEngine.AXIS_MAX.get(raw_key, 10)
                    vals = []
                    for t in with_fp:
                        raw_dict = (t.profile_data["fingerprint"].get("raw_values") or {})
                        vals.append(float(raw_dict.get(raw_key, 0) or 0))
                    axes_raw[axis] = _axis_stats(vals, raw=True, axis_max=axis_max)

        # ─── Section D: rich-target count ────────────────────────────────
        rich_targets = {}
        for k in [3, 5, 7, 9]:
            cnt = 0
            for t in extractable:
                axes_dict = (t.profile_data["fingerprint"].get("axes") or {})
                populated = sum(1 for axis in FINGERPRINT_AXES
                                if float(axes_dict.get(axis, 0.0) or 0.0) > POPULATED_THRESHOLD)
                if populated >= k:
                    cnt += 1
            rich_targets[str(k)] = cnt

        # ─── Section E + F: full pairwise similarity ─────────────────────
        similarity = None
        top_pairs_out = []
        if n_extractable >= 2:
            pair_sims = []
            for a, b in combinations(extractable, 2):
                va = _extract_axes(a)
                vb = _extract_axes(b)
                s = _cosine(va, vb)
                pair_sims.append((s, a, b, va, vb))
            sim_vals = [p[0] for p in pair_sims]
            above = {}
            for t in [0.5, 0.6, 0.7, 0.8, 0.9]:
                cnt = sum(1 for s in sim_vals if s >= t)
                above[str(t)] = {"count": cnt, "pct": 100.0 * cnt / len(sim_vals) if sim_vals else 0.0}
            similarity = {
                "total_pairs": len(sim_vals),
                "mean": statistics.mean(sim_vals) if sim_vals else 0.0,
                "stdev": _safe_stdev(sim_vals),
                "above": above,
                "hist": _histogram(sim_vals, n_bins=10, lo=0.0, hi=1.0),
            }

            pair_sims.sort(key=lambda p: p[0], reverse=True)
            for rank, (s, a, b, va, vb) in enumerate(pair_sims[:20], start=1):
                # top-3 co-axes by min(axes_a, axes_b)
                pair_axes = [(axis, min(va[i], vb[i])) for i, axis in enumerate(FINGERPRINT_AXES)]
                pair_axes.sort(key=lambda x: x[1], reverse=True)
                top_axes = [a_name for a_name, _ in pair_axes[:3]]
                top_pairs_out.append({
                    "rank": rank,
                    "sim": round(s, 4),
                    "a": {"id": str(a.id), "email": a.email},
                    "b": {"id": str(b.id), "email": b.email},
                    "top_axes": top_axes,
                })

        # ─── Section G: auto-flagged observations ────────────────────────
        observations = []
        for axis in FINGERPRINT_AXES:
            if axis in axes_normalized:
                s = axes_normalized[axis]
                if s["pct_saturated"] > 30:
                    raw_key = AXIS_RAW_KEYS[axis]
                    am = FingerprintEngine.AXIS_MAX.get(raw_key, "?")
                    observations.append(
                        f"saturation: `{axis}` is {s['pct_saturated']:.1f}% saturated — "
                        f"AXIS_MAX[`{raw_key}`]={am} likely too low"
                    )
                if s["pct_zero"] > 80 and n_extractable >= 5:
                    observations.append(
                        f"starved: `{axis}` is zero for {s['pct_zero']:.1f}% of fingerprints — "
                        f"data plumbing or AXIS_MAX too high"
                    )
        if axes_raw is not None:
            for axis in FINGERPRINT_AXES:
                s = axes_raw[axis]
                if s["pct_at_max"] > 20:
                    raw_key = AXIS_RAW_KEYS[axis]
                    am = FingerprintEngine.AXIS_MAX.get(raw_key, "?")
                    observations.append(
                        f"saturation cause confirmed: `{axis}` raw ≥ AXIS_MAX (={am}) in "
                        f"{s['pct_at_max']:.1f}% of fingerprints"
                    )
        if similarity:
            pct_70 = similarity["above"]["0.7"]["pct"]
            verdict = (
                "threshold likely too low" if pct_70 > 5
                else "threshold too high or vectors too noisy" if pct_70 < 0.1
                else "threshold within sane range"
            )
            observations.append(
                f"similarity threshold sanity: {pct_70:.2f}% of pairs ≥ 0.7 → {verdict}"
            )
        if rich_targets.get("7", 0) < 10:
            observations.append(
                f"calibration thin: only {rich_targets.get('7', 0)} targets have ≥7/9 axes "
                f"populated (>{POPULATED_THRESHOLD}) — consider growing the corpus "
                "before tuning weights"
            )

        # ─── Assemble report ─────────────────────────────────────────────
        report = {
            "version": SCRIPT_VERSION,
            "workspace": {"slug": ws.slug, "name": ws.name, "id": str(ws.id)},
            "summary": {
                "n_total": n_total,
                "n_with_fingerprint": n_with_fingerprint,
                "n_extractable": n_extractable,
            },
            "axes_normalized": axes_normalized,
            "axes_raw": axes_raw,
            "rich_targets": rich_targets,
            "similarity": similarity,
            "top_pairs": top_pairs_out,
            "observations": observations,
            "generated_at_utc": t_start.strftime("%Y-%m-%d %H:%M UTC"),
        }

        # ─── Write outputs ───────────────────────────────────────────────
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = t_start.strftime("%Y%m%d-%H%M")
        slug_safe = ws.slug.replace("/", "_")
        base = f"fingerprint_calibration_{slug_safe}_{stamp}"
        md_path = out_dir / f"{base}.md"
        json_path = out_dir / f"{base}.json"

        md_path.write_text(render_md(report), encoding="utf-8")
        json_path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")

        elapsed = (datetime.now(timezone.utc) - t_start).total_seconds()
        print(f"S143 diag complete — {elapsed:.1f}s")
        print(f"  targets:      {n_total} total · {n_with_fingerprint} with FP · {n_extractable} extractable")
        if similarity:
            print(f"  pairs:        {similarity['total_pairs']} computed")
        print(f"  markdown:     {md_path}")
        print(f"  json:         {json_path}")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
