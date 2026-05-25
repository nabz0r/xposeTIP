#!/usr/bin/env python3
"""
S213 — Username findings audit R&D extract (READ-ONLY).

Dumps every Finding with indicator_type='username' to docs/qa/, classified
per-row by validator pass/reason + source_kind + trust signals. Used to scope
a follow-up cleanup migration; this sprint itself writes nothing to the DB.

Pattern: S159 audit-before-fix. Closes the gap left by S179, which cleaned
the identities table but not the upstream findings source.

Usage:
    docker compose exec api python scripts/audit_username_findings.py
    docker compose exec api python scripts/audit_username_findings.py --workspace friends
    docker compose exec api python scripts/audit_username_findings.py --limit-per-module 100
    docker compose exec api python scripts/audit_username_findings.py --dry-run
"""
import argparse
import csv
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

from sqlalchemy import select

from api.tasks.utils import get_sync_session
from api.models.finding import Finding
from api.models.target import Target
from api.models.workspace import Workspace
from api.services.layer4.username_validator import (
    is_valid_username,
    is_looks_like_full_name,  # S230 — promoted from this script
    _TITLE_PATTERNS,
    _DOMAIN_TLD_RE,
)


# READ-ONLY — no writes to DB anywhere in this script.


def _classify_invalid_reason(value: str) -> str:
    """Mirror is_valid_username rule order, return label of first failing rule.

    Returns "none" if value passes. 12 fixed labels match T1 spec.
    """
    if not value or len(value) > 40:
        return "empty_or_too_long"
    if value.count(' ') >= 3:
        return "too_many_spaces"
    if ' - ' in value or ' – ' in value or ' — ' in value:
        return "dash_separator"
    if "|" in value:
        return "pipe_in_title"
    if "–" in value or "—" in value:
        return "endash_in_title"
    if "&#" in value or "&amp;" in value:
        return "html_entity"
    if not any(c.isalnum() for c in value):
        return "no_alnum"
    lower = value.lower()
    if any(p in lower for p in _TITLE_PATTERNS):
        return "title_pattern"
    if value.count(".") >= 2:
        return "multi_dot_handle"
    if _DOMAIN_TLD_RE.match(value):
        return "fqdn_tld"
    if "(" in value or ")" in value:
        return "paren_pattern"
    return "none"


# S229 — Advanced pattern classifier (runs only on validator-PASS rows).
# Surfaces patterns prod is_valid_username misses or cannot disambiguate
# without manual triage. NO DB writes, NO behavior change to prod validator.
# S230 — looks_like_full_name promoted to username_validator.py; imported above.

_SINGLE_DOT_HANDLE_RE = re.compile(r"^[a-z0-9]+\.[a-z0-9]+$")
_KNOWN_TLD_SUFFIX_RE = re.compile(
    r"\.(com|org|net|io|co|app|info|biz|me|tv|eu|us|ca|au|"
    r"lu|fr|de|uk|nl|be|ch|it|es|gov|edu|mil|ai|dev|xyz)$",
    re.IGNORECASE,
)


def _classify_advanced_pattern(value: str) -> str:
    """Tag prod-validator-PASS values with extra patterns missed by is_valid_username.

    Returns one of:
      - "looks_like_full_name"  : delegates to is_looks_like_full_name() (S230)
      - "single_dot_ambiguous"  : single dot, shape word.word, suffix NOT
                                  in known-TLD allow-list
      - "none"                  : passes prod validator + no advanced pattern matches
    """
    if not value:
        return "none"
    if is_looks_like_full_name(value):
        return "looks_like_full_name"
    if "." in value and value.count(".") == 1:
        if _SINGLE_DOT_HANDLE_RE.match(value) and not _KNOWN_TLD_SUFFIX_RE.search(value):
            return "single_dot_ambiguous"
    return "none"


def _source_kind(finding: Finding) -> str:
    """`scraper_engine` if data is a dict containing a 'scraper' key, else `direct`."""
    data = finding.data
    if isinstance(data, dict) and "scraper" in data:
        return "scraper_engine"
    return "direct"


def _isoformat(dt) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


CSV_COLUMNS = [
    "finding_id", "scan_id", "target_id", "target_email", "workspace_slug",
    "module", "source_kind", "indicator_value",
    "validator_pass", "validator_reason",
    "verified", "cross_verified", "cross_verified_sources_count",
    "source_url", "first_seen", "last_seen", "created_at",
    "advanced_pattern",  # NEW — S229 (appended to preserve existing column order)
]


def _row_dict(finding, target_email, workspace_slug, validator_pass,
              validator_reason, source_kind, advanced_pattern="none"):
    sources = finding.cross_verification_sources or []
    return {
        "finding_id": str(finding.id),
        "scan_id": str(finding.scan_id) if finding.scan_id else "",
        "target_id": str(finding.target_id) if finding.target_id else "",
        "target_email": target_email or "",
        "workspace_slug": workspace_slug or "",
        "module": finding.module or "",
        "source_kind": source_kind,
        "indicator_value": finding.indicator_value or "",
        "validator_pass": "true" if validator_pass else "false",
        "validator_reason": validator_reason,
        "verified": "true" if finding.verified else "false",
        "cross_verified": str(finding.cross_verification_count or 0),
        "cross_verified_sources_count": str(len(sources) if isinstance(sources, list) else 0),
        "source_url": finding.url or "",
        "first_seen": _isoformat(finding.first_seen),
        "last_seen": _isoformat(finding.last_seen),
        "created_at": _isoformat(finding.created_at),
        "advanced_pattern": advanced_pattern,
    }


def _write_csv(path, rows, columns=CSV_COLUMNS):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _markdown_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |"]
    out.append("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--workspace", default=None, help="Filter by workspace slug")
    p.add_argument("--limit-per-module", type=int, default=0,
                   help="Cap rows-per-module CSV at N (full-table CSVs always include all rows)")
    p.add_argument("--out-dir", default=None, help="Output directory")
    p.add_argument("--dry-run", action="store_true", help="Print stats only, write nothing")
    p.add_argument("--sprint", default="S229", help="Sprint tag for output dir prefix (default S229)")
    return p.parse_args()


def main():
    args = parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir or os.path.join("docs", "qa", f"{args.sprint}_username_audit_{ts}")

    if not args.dry_run:
        # Default uses timestamp so collision is non-existent. Custom --out-dir
        # that already exists + non-empty is refused.
        if args.out_dir and os.path.isdir(out_dir) and os.listdir(out_dir):
            print(f"ERROR: --out-dir {out_dir} already exists and is non-empty. Refusing to overwrite.",
                  file=sys.stderr)
            sys.exit(2)
        os.makedirs(out_dir, exist_ok=True)
        os.makedirs(os.path.join(out_dir, "by_module"), exist_ok=True)

    session = get_sync_session()
    try:
        # Single SELECT joining Finding + Target + Workspace, ordered for deterministic output.
        stmt = (
            select(Finding, Target.email, Workspace.slug)
            .join(Target, Target.id == Finding.target_id)
            .join(Workspace, Workspace.id == Finding.workspace_id)
            .where(Finding.indicator_type == "username")
            .order_by(Finding.module.asc(), Finding.created_at.desc())
        )
        if args.workspace:
            stmt = stmt.where(Workspace.slug == args.workspace)

        # In-memory aggregates
        all_rows: list[dict] = []
        validator_fail_rows: list[dict] = []
        low_trust_rows: list[dict] = []
        name_scraper_rows: list[dict] = []
        by_module_rows: dict[str, list[dict]] = defaultdict(list)

        per_module_total: Counter = Counter()
        per_module_fail: Counter = Counter()
        per_module_reason: dict[str, Counter] = defaultdict(Counter)
        reason_counter: Counter = Counter()
        reason_examples: dict[str, list[str]] = defaultdict(list)
        invalid_value_counter: Counter = Counter()
        invalid_value_targets: dict[str, set] = defaultdict(set)
        invalid_value_modules: dict[str, set] = defaultdict(set)
        invalid_value_reason: dict[str, str] = {}
        targets_touched: set = set()
        workspaces_touched: set = set()

        cross_tab_counter: Counter = Counter()  # (validator_pass, cross_ge_1) -> count

        # Stream-iterate
        results = session.execute(stmt)
        total = 0
        for finding, target_email, workspace_slug in results:
            total += 1
            value = finding.indicator_value or ""
            validator_pass = is_valid_username(value)
            validator_reason = _classify_invalid_reason(value) if not validator_pass else "none"
            source_kind = _source_kind(finding)
            # S229 — run advanced classifier only on prod-validator-PASS rows
            advanced_pattern = _classify_advanced_pattern(value) if validator_pass else "none"

            row = _row_dict(finding, target_email, workspace_slug,
                            validator_pass, validator_reason, source_kind,
                            advanced_pattern=advanced_pattern)
            all_rows.append(row)

            # Aggregates
            mod = finding.module or "(none)"
            per_module_total[mod] += 1
            if not validator_pass:
                per_module_fail[mod] += 1
                per_module_reason[mod][validator_reason] += 1
                reason_counter[validator_reason] += 1
                if len(reason_examples[validator_reason]) < 3 and value not in reason_examples[validator_reason]:
                    reason_examples[validator_reason].append(value)
                invalid_value_counter[value] += 1
                invalid_value_targets[value].add(str(finding.target_id))
                invalid_value_modules[value].add(mod)
                invalid_value_reason[value] = validator_reason
                validator_fail_rows.append(row)

            if not finding.verified and (finding.cross_verification_count or 0) == 0:
                low_trust_rows.append(row)

            if mod == "name_scraper_engine":
                name_scraper_rows.append(row)

            by_module_rows[mod].append(row)

            if finding.target_id:
                targets_touched.add(str(finding.target_id))
            if workspace_slug:
                workspaces_touched.add(workspace_slug)

            ct_key = (validator_pass, (finding.cross_verification_count or 0) >= 1)
            cross_tab_counter[ct_key] += 1

        # === Compose output ===
        name_scraper_total = per_module_total.get("name_scraper_engine", 0)
        name_scraper_fail = per_module_fail.get("name_scraper_engine", 0)
        total_fail = sum(per_module_fail.values())
        total_low_trust = len(low_trust_rows)

        pct = (lambda n, d: (100.0 * n / d) if d else 0.0)

        # Stdout summary (also when dry-run)
        print("S213 audit complete.")
        print(f"  Total username findings: {total}")
        print(f"  Workspaces touched: {len(workspaces_touched)}")
        print(f"  Targets touched: {len(targets_touched)}")
        print(f"  Modules emitting username findings: {len(per_module_total)}")
        print(f"  Validator-fail: {total_fail} ({pct(total_fail, total):.1f}%)")
        print(f"  Low-trust (unverified + cross_verified=0): {total_low_trust} ({pct(total_low_trust, total):.1f}%)")
        print(f"  name_scraper_engine total: {name_scraper_total} | validator-fail: {name_scraper_fail}")
        print(f"  Output: {out_dir if not args.dry_run else '(dry-run, no files written)'}")

        if args.dry_run:
            return

        # === Write CSVs ===
        _write_csv(os.path.join(out_dir, "findings_full.csv"), all_rows)
        _write_csv(os.path.join(out_dir, "flagged_validator_fail.csv"), validator_fail_rows)
        _write_csv(os.path.join(out_dir, "flagged_low_trust.csv"), low_trust_rows)
        _write_csv(os.path.join(out_dir, "flagged_name_scraper.csv"), name_scraper_rows)

        # top_invalid_values.csv
        top_invalid = invalid_value_counter.most_common(100)
        with open(os.path.join(out_dir, "top_invalid_values.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["indicator_value", "validator_reason", "occurrence_count",
                        "distinct_targets", "distinct_modules"])
            for value, count in top_invalid:
                w.writerow([
                    value,
                    invalid_value_reason.get(value, ""),
                    count,
                    len(invalid_value_targets[value]),
                    len(invalid_value_modules[value]),
                ])

        # by_module/<module>.csv (only modules with >=10 findings)
        for mod, rows in by_module_rows.items():
            if len(rows) < 10:
                continue
            sliced = rows
            if args.limit_per_module > 0:
                sliced = rows[: args.limit_per_module]
            safe = re.sub(r"[^a-zA-Z0-9_-]", "_", mod) or "_unknown"
            _write_csv(os.path.join(out_dir, "by_module", f"{safe}.csv"), sliced)

        # S229 — Extended pattern slices on validator-PASS rows
        flagged_full_name_rows = [r for r in all_rows if r["advanced_pattern"] == "looks_like_full_name"]
        flagged_single_dot_rows = [r for r in all_rows if r["advanced_pattern"] == "single_dot_ambiguous"]
        if flagged_full_name_rows:
            _write_csv(os.path.join(out_dir, "flagged_looks_like_full_name.csv"), flagged_full_name_rows)
        if flagged_single_dot_rows:
            _write_csv(os.path.join(out_dir, "flagged_single_dot_ambiguous.csv"), flagged_single_dot_rows)

        # Per-module advanced-pattern ranking (denominator = validator-PASS only)
        mod_advanced: Counter = Counter()
        mod_total_pass: Counter = Counter()
        for r in all_rows:
            if r["validator_pass"] == "true":
                mod_total_pass[r["module"]] += 1
                if r["advanced_pattern"] != "none":
                    mod_advanced[r["module"]] += 1
        mod_rank_rows = [
            {
                "module": m,
                "validator_pass_count": mod_total_pass[m],
                "advanced_pattern_count": mod_advanced[m],
                "advanced_rate_pct": round(100.0 * mod_advanced[m] / mod_total_pass[m], 1),
            }
            for m in mod_total_pass if mod_advanced[m] > 0
        ]
        mod_rank_rows.sort(key=lambda r: (-r["advanced_rate_pct"], -r["advanced_pattern_count"]))
        if mod_rank_rows:
            _write_csv(
                os.path.join(out_dir, "by_module_advanced.csv"),
                mod_rank_rows,
                columns=["module", "validator_pass_count", "advanced_pattern_count", "advanced_rate_pct"],
            )

        # === summary.md ===
        md_lines: list[str] = []
        md_lines.append("# S213 — Username Findings Audit")
        md_lines.append("")
        md_lines.append(f"- **Run UTC:** {ts}")
        md_lines.append(f"- **Workspace filter:** `{args.workspace or '(all)'}`")
        md_lines.append(f"- **Total username findings:** {total}")
        md_lines.append(f"- **Targets touched:** {len(targets_touched)}")
        md_lines.append(f"- **Workspaces touched:** {len(workspaces_touched)}")
        md_lines.append(f"- **Validator-fail:** {total_fail} ({pct(total_fail, total):.1f}%)")
        md_lines.append(f"- **Low-trust (verified=False AND cross_verified=0):** {total_low_trust} ({pct(total_low_trust, total):.1f}%)")
        md_lines.append("")

        # By module table
        md_lines.append("## By module")
        md_lines.append("")
        rows = []
        for mod in per_module_total:
            t = per_module_total[mod]
            fl = per_module_fail.get(mod, 0)
            top = per_module_reason.get(mod, Counter()).most_common(1)
            top_reason = top[0][0] if top else "—"
            rows.append((mod, t, fl, f"{pct(fl, t):.1f}%", top_reason))
        rows.sort(key=lambda r: (-(float(r[3][:-1])), -r[1]))
        md_lines.append(_markdown_table(
            ["module", "total", "validator_fail", "fail_%", "top_reason"],
            rows,
        ))
        md_lines.append("")

        # By validator reason
        md_lines.append("## By validator reason")
        md_lines.append("")
        reason_rows = []
        for reason, count in reason_counter.most_common():
            ex = ", ".join(f"`{v}`" for v in reason_examples.get(reason, []))
            reason_rows.append((reason, count, ex))
        md_lines.append(_markdown_table(
            ["reason", "count", "example_values (top 3)"],
            reason_rows,
        ))
        md_lines.append("")

        # Cross-tab
        md_lines.append("## Trust signal cross-tabs")
        md_lines.append("")
        md_lines.append("Rows = `validator_pass`, Columns = `cross_verified >= 1`")
        md_lines.append("")
        ct_rows = [
            ("True",  cross_tab_counter.get((True,  True),  0), cross_tab_counter.get((True,  False), 0)),
            ("False", cross_tab_counter.get((False, True),  0), cross_tab_counter.get((False, False), 0)),
        ]
        md_lines.append(_markdown_table(
            ["validator_pass", "cross_verified >= 1", "cross_verified = 0"],
            ct_rows,
        ))
        md_lines.append("")

        # name_scraper_engine focus
        md_lines.append("## name_scraper_engine focus (Bug 12 candidates)")
        md_lines.append("")
        md_lines.append(f"- Total: **{name_scraper_total}**")
        md_lines.append(f"- Validator-fail: **{name_scraper_fail}**")
        md_lines.append("")
        md_lines.append("Sample (up to 10):")
        md_lines.append("")
        sample_rows = []
        for r in name_scraper_rows[:10]:
            sample_rows.append((r["target_email"], r["indicator_value"]))
        if sample_rows:
            md_lines.append(_markdown_table(["target_email", "indicator_value"], sample_rows))
        else:
            md_lines.append("_(no name_scraper_engine username findings present)_")
        md_lines.append("")

        # S229 — Advanced patterns section on validator-PASS rows
        md_lines.append("## S229 — Advanced patterns on validator-PASS rows")
        md_lines.append("")
        total_pass = sum(1 for r in all_rows if r["validator_pass"] == "true")
        adv_full_name = sum(1 for r in all_rows if r["advanced_pattern"] == "looks_like_full_name")
        adv_single_dot = sum(1 for r in all_rows if r["advanced_pattern"] == "single_dot_ambiguous")
        md_lines.append(f"- Total validator-PASS: **{total_pass:,}**")
        md_lines.append(f"- `looks_like_full_name`: **{adv_full_name}** "
                        f"({pct(adv_full_name, total_pass):.1f}%)")
        md_lines.append(f"- `single_dot_ambiguous`: **{adv_single_dot}** "
                        f"({pct(adv_single_dot, total_pass):.1f}%)")
        md_lines.append("")
        if mod_rank_rows:
            md_lines.append("### Top modules by advanced-pattern rate (validator-PASS denominator)")
            md_lines.append("")
            adv_table = [
                (f"`{r['module']}`", r["validator_pass_count"],
                 r["advanced_pattern_count"], f"{r['advanced_rate_pct']}%")
                for r in mod_rank_rows[:15]
            ]
            md_lines.append(_markdown_table(
                ["module", "pass count", "advanced count", "advanced rate %"],
                adv_table,
            ))
            md_lines.append("")

        with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

    finally:
        session.close()


if __name__ == "__main__":
    main()
