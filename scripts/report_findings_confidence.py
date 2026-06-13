"""Detailed findings + per-finding confidence/corroboration report (human targets).

S303 — READ-ONLY. No writes to findings/profiles/scores. Enumerates human-workspace
targets, dumps every active finding with its source-scored confidence + cross-
verification, and writes a 3-file report under docs/qa/rescan_<UTC-ts>/.

Confidence semantics (surfaced in summary.md so the report is self-explaining):
  confidence = per-finding source-scored value (reliability x verification x
  corroboration); ceiling 0.95 for system-derived, 1.0 only operator-asserted.
  cross_verification_count = number of independent corroborating sources.

Run: docker compose exec api python scripts/report_findings_confidence.py
     ... --since <iso>  (only findings refreshed at/after this time)
     ... --workspace <uuid>
"""
import argparse
import csv
import logging
import os
import uuid as uuidlib
from datetime import datetime, timezone

logging.getLogger().setLevel(logging.WARNING)
from sqlalchemy import select  # noqa: E402

from api.tasks.utils import get_sync_session  # noqa: E402
from api.models.target import Target  # noqa: E402
from api.models.workspace import Workspace  # noqa: E402
from api.models.finding import Finding  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="ISO timestamp — only findings with last_seen >= since")
    ap.add_argument("--workspace", help="scope to one workspace UUID (default: all human)")
    args = ap.parse_args()

    since = None
    if args.since:
        since = datetime.fromisoformat(args.since)
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)

    s = get_sync_session()

    tq = (
        select(Target.id, Target.email, Target.workspace_id, Target.exposure_score, Target.threat_score)
        .join(Workspace, Workspace.id == Target.workspace_id)
        .where(Workspace.kind == "human")
    )
    if args.workspace:
        tq = tq.where(Target.workspace_id == uuidlib.UUID(args.workspace))
    targets = s.execute(tq).all()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    outdir = os.path.join("docs", "qa", f"rescan_{ts}")
    os.makedirs(outdir, exist_ok=True)

    # confidence buckets + tallies
    buckets = {"1.0": 0, "0.8-0.99": 0, "0.5-0.79": 0, "<0.5": 0, "none": 0}
    module_counts: dict[str, int] = {}
    total_findings = total_verified = total_xverified = 0
    conf_sum = 0.0
    conf_n = 0

    findings_path = os.path.join(outdir, "findings.csv")
    per_target_path = os.path.join(outdir, "per_target.csv")

    with open(findings_path, "w", newline="") as ff, open(per_target_path, "w", newline="") as pf:
        fw = csv.writer(ff)
        fw.writerow([
            "workspace_id", "target_id", "target_email", "module", "layer", "category",
            "severity", "indicator_type", "indicator_value", "title", "confidence",
            "cross_verification_count", "verified", "last_seen",
        ])
        pw = csv.writer(pf)
        pw.writerow([
            "target_email", "findings_total", "findings_verified", "mean_confidence",
            "max_confidence", "exposure_score", "threat_score",
        ])

        for tid, email, wid, exp, thr in targets:
            fq = select(Finding).where(Finding.target_id == tid, Finding.status == "active")
            if since is not None:
                fq = fq.where(Finding.last_seen >= since)
            rows = s.execute(fq).scalars().all()

            t_confs = []
            t_verified = 0
            for f in rows:
                total_findings += 1
                module_counts[f.module] = module_counts.get(f.module, 0) + 1
                c = f.confidence
                if c is None:
                    buckets["none"] += 1
                else:
                    conf_sum += c
                    conf_n += 1
                    t_confs.append(c)
                    if c >= 1.0:
                        buckets["1.0"] += 1
                    elif c >= 0.8:
                        buckets["0.8-0.99"] += 1
                    elif c >= 0.5:
                        buckets["0.5-0.79"] += 1
                    else:
                        buckets["<0.5"] += 1
                if f.verified:
                    t_verified += 1
                    total_verified += 1
                if (f.cross_verification_count or 0) > 0:
                    total_xverified += 1
                fw.writerow([
                    wid, tid, email, f.module, f.layer, f.category, f.severity,
                    f.indicator_type, f.indicator_value, (f.title or "").replace("\n", " "),
                    f.confidence, f.cross_verification_count, f.verified,
                    f.last_seen.isoformat() if f.last_seen else "",
                ])
            mean_c = round(sum(t_confs) / len(t_confs), 3) if t_confs else ""
            max_c = round(max(t_confs), 3) if t_confs else ""
            pw.writerow([email, len(rows), t_verified, mean_c, max_c, exp, thr])

    mean_conf = round(conf_sum / conf_n, 3) if conf_n else 0
    xshare = round(100 * total_xverified / total_findings, 1) if total_findings else 0
    top_modules = sorted(module_counts.items(), key=lambda kv: -kv[1])[:15]

    with open(os.path.join(outdir, "summary.md"), "w") as sm:
        sm.write(f"# Rescan findings/confidence report — {ts}\n\n")
        if since:
            sm.write(f"Filter: findings with `last_seen >= {since.isoformat()}`\n\n")
        if args.workspace:
            sm.write(f"Scope: workspace `{args.workspace}`\n\n")
        sm.write(f"- targets: **{len(targets)}**\n")
        sm.write(f"- findings (active): **{total_findings}**\n")
        sm.write(f"- verified: **{total_verified}** ({round(100*total_verified/total_findings,1) if total_findings else 0}%)\n")
        sm.write(f"- cross-verified (>=1 corroborating source): **{total_xverified}** ({xshare}%)\n")
        sm.write(f"- mean confidence: **{mean_conf}**\n\n")
        sm.write("## Confidence distribution\n\n")
        sm.write("| bucket | n |\n|---|---|\n")
        for k, v in buckets.items():
            sm.write(f"| {k} | {v} |\n")
        sm.write("\n## Top modules by finding count\n\n")
        sm.write("| module | n |\n|---|---|\n")
        for m, c in top_modules:
            sm.write(f"| {m} | {c} |\n")
        sm.write("\n## Confidence semantics\n\n")
        sm.write(
            "`confidence` is the per-finding source-scored value "
            "(reliability x verification x corroboration); ceiling 0.95 for system-derived, "
            "1.0 only operator-asserted. `cross_verification_count` = independent corroborating sources.\n"
        )

    print(f"OUTPUT {outdir}", flush=True)
    print(f"targets={len(targets)} findings={total_findings} verified={total_verified} "
          f"cross_verified={total_xverified} ({xshare}%) mean_confidence={mean_conf}", flush=True)


if __name__ == "__main__":
    main()
