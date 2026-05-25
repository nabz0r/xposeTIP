#!/usr/bin/env python3
"""
S228 — Database hygiene audit (READ-ONLY).

4-block sweep beyond the scraper layer:
  A. Indicator value shape — regex/placeholder validators per indicator_type
  B. Targets hygiene — orphans, placeholders, stale, dup-email
  C. Profile aggregation drift — raw findings vs profile_data arrays
  D. Module/category coherence + BFP substrate integrity

Output: docs/qa/S228_db_hygiene_audit.md (markdown report, ranked).

Pattern: S159 / S213 / S224 audit-before-fix. Read-only — no DB modification.
Run from repo root with DB env vars set, or via:
    docker compose exec api python scripts/audit_db_hygiene.py
"""

import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras


OUT_PATH = "docs/qa/S228_db_hygiene_audit.md"
SAMPLE_SIZE = 50          # per indicator_type in Block A
SAMPLE_ROWS_SHOWN = 5     # malformed rows printed per category
STALE_DAYS = 30           # Block B threshold
DRIFT_TOP_N = 20          # Block C top deltas


def db_conn():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "postgres"),
        port=int(os.getenv("PGPORT", "5432")),
        user=os.getenv("PGUSER", "xpose"),
        password=os.getenv("PGPASSWORD", "xpose"),
        dbname=os.getenv("PGDATABASE", "xpose"),
    )


# ─────────────────────────── Block A validators ───────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_URL_RE = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)
_DOMAIN_RE = re.compile(
    r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$",
    re.IGNORECASE,
)
_IPV4_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
_IPV6_RE = re.compile(r"^[0-9a-f:]+$", re.IGNORECASE)
_BTC_RE = re.compile(r"^(bc1[a-z0-9]{6,87}|[13][a-zA-HJ-NP-Z0-9]{25,34})$")
_ETH_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
_USERNAME_SAFE_RE = re.compile(r"^[a-zA-Z0-9._\-]{1,40}$")
_PLACEHOLDER_RE = re.compile(
    r"^(test|demo|undefined|null|none|n/?a|nan|asdf+|xxx+|placeholder|\[redacted\]|example|sample|foo|bar|todo)$",
    re.IGNORECASE,
)


def _validate(itype: str, value: str) -> tuple[bool, str]:
    if value is None or value == "":
        return False, "empty"
    if _PLACEHOLDER_RE.match(value.strip()):
        return False, "placeholder"
    if itype == "email":
        return (True, "ok") if _EMAIL_RE.match(value) else (False, "bad_email_shape")
    if itype in ("url", "social_url", "photo_url"):
        return (True, "ok") if _URL_RE.match(value) else (False, "bad_url_shape")
    if itype == "domain":
        if "@" in value:
            return False, "domain_has_at"
        return (True, "ok") if _DOMAIN_RE.match(value) else (False, "bad_domain_shape")
    if itype == "ip":
        if _IPV4_RE.match(value):
            octets = [int(x) for x in value.split(".")]
            return (True, "ok") if all(0 <= o <= 255 for o in octets) else (False, "bad_ipv4_octet")
        if _IPV6_RE.match(value) and ":" in value:
            return True, "ok"
        return False, "bad_ip_shape"
    if itype == "phone":
        digits = re.sub(r"[\s+\-().]", "", value)
        if not digits.isdigit():
            return False, "phone_has_nondigit"
        if not (7 <= len(digits) <= 15):
            return False, "phone_bad_length"
        return True, "ok"
    if itype == "crypto_wallet":
        if _BTC_RE.match(value) or _ETH_RE.match(value):
            return True, "ok"
        return False, "bad_crypto_shape"
    if itype == "username":
        if "/" in value or "@" in value or " " in value:
            return False, "username_has_separator"
        if _DOMAIN_RE.match(value):
            return False, "username_is_domain"
        if not _USERNAME_SAFE_RE.match(value):
            return False, "username_bad_chars"
        return True, "ok"
    # name / corporate_officer / legal_record / media_mention / sanctions_match / behavioral_profile
    # — shape check is "non-empty, non-placeholder, has at least 1 alpha char"
    if not re.search(r"[a-zA-Z]", value):
        return False, "no_alpha"
    return True, "ok"


def block_a_indicator_shape(conn):
    """Per indicator_type: total, sample N, malformed rate, top reasons, sample rows."""
    out = {"types": [], "samples": defaultdict(list)}
    with conn.cursor() as cur:
        cur.execute("""
            SELECT indicator_type, COUNT(*) AS n
            FROM findings
            WHERE indicator_type IS NOT NULL AND indicator_value IS NOT NULL
            GROUP BY indicator_type
            ORDER BY n DESC
        """)
        type_counts = cur.fetchall()

    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        for itype, total in type_counts:
            cur.execute("""
                SELECT id, indicator_value, module, workspace_id, target_id
                FROM findings
                WHERE indicator_type = %s AND indicator_value IS NOT NULL
                ORDER BY random()
                LIMIT %s
            """, (itype, SAMPLE_SIZE))
            rows = cur.fetchall()
            reasons = Counter()
            malformed_samples = []
            for r in rows:
                ok, reason = _validate(itype, r["indicator_value"])
                if not ok:
                    reasons[reason] += 1
                    if len(malformed_samples) < SAMPLE_ROWS_SHOWN:
                        malformed_samples.append({
                            "value": r["indicator_value"][:80],
                            "module": r["module"],
                            "reason": reason,
                            "finding_id": str(r["id"]),
                        })
            malformed = sum(reasons.values())
            out["types"].append({
                "indicator_type": itype,
                "total_in_db": total,
                "sampled": len(rows),
                "malformed": malformed,
                "rate_pct": round(100.0 * malformed / max(len(rows), 1), 1),
                "top_reasons": reasons.most_common(5),
            })
            out["samples"][itype] = malformed_samples
    return out


# ─────────────────────────── Block B targets hygiene ───────────────────────────

def block_b_targets_hygiene(conn):
    out = {}

    # B1 — orphan targets (no findings)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM targets t
            WHERE NOT EXISTS (SELECT 1 FROM findings WHERE target_id = t.id)
        """)
        out["orphan_count"] = cur.fetchone()[0]

        cur.execute("""
            SELECT id, email, display_name, status, created_at
            FROM targets t
            WHERE NOT EXISTS (SELECT 1 FROM findings WHERE target_id = t.id)
            ORDER BY created_at DESC
            LIMIT 20
        """)
        out["orphan_samples"] = [
            {"id": str(r[0]), "email": r[1], "display_name": r[2], "status": r[3], "created_at": str(r[4])}
            for r in cur.fetchall()
        ]

    # B2 — placeholder names
    PLACEHOLDER_SQL = r"^(test|demo|undefined|null|none|n/?a|nan|asdf+|xxx+|placeholder|example|foo|bar|todo)$"
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT id, email, display_name, user_first_name, user_last_name
            FROM targets
            WHERE user_first_name ~* %s
               OR user_last_name ~* %s
               OR display_name ~* %s
               OR email ~* %s
            LIMIT 50
        """, (PLACEHOLDER_SQL, PLACEHOLDER_SQL, PLACEHOLDER_SQL, PLACEHOLDER_SQL))
        out["placeholder_samples"] = [dict(r) for r in cur.fetchall()]
        out["placeholder_count"] = len(out["placeholder_samples"])

    # B3 — stale targets
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT COUNT(*) FROM targets
            WHERE last_scanned IS NOT NULL
              AND last_scanned < NOW() - INTERVAL '{STALE_DAYS} days'
        """)
        out["stale_count"] = cur.fetchone()[0]

    # B4 — duplicate email per workspace
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT workspace_id, lower(email) AS email, COUNT(*) AS n,
                   array_agg(id::text) AS target_ids
            FROM targets
            WHERE email IS NOT NULL AND email <> ''
            GROUP BY workspace_id, lower(email)
            HAVING COUNT(*) > 1
            ORDER BY n DESC
            LIMIT 30
        """)
        out["dup_email_groups"] = [dict(r) for r in cur.fetchall()]

    # B5 — status=pending but last_scanned set (inconsistent state)
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT id, email, status, last_scanned
            FROM targets
            WHERE status = 'pending' AND last_scanned IS NOT NULL
            ORDER BY last_scanned DESC
            LIMIT 20
        """)
        out["pending_but_scanned"] = [dict(r) for r in cur.fetchall()]
        cur.execute("""
            SELECT COUNT(*) FROM targets
            WHERE status = 'pending' AND last_scanned IS NOT NULL
        """)
        out["pending_but_scanned_count"] = cur.fetchone()[0]

    return out


# ─────────────────────────── Block C profile drift ───────────────────────────

def block_c_profile_drift(conn):
    """For each target with phone/crypto findings, compare raw count vs profile_data array length."""
    out = {}
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # phones drift
        cur.execute("""
            WITH raw AS (
                SELECT target_id, COUNT(*) AS raw_phones
                FROM findings
                WHERE indicator_type = 'phone'
                GROUP BY target_id
            ),
            aggr AS (
                SELECT id AS target_id, email,
                       COALESCE(jsonb_array_length(profile_data->'phones'), 0) AS profile_phones
                FROM targets
                WHERE profile_data IS NOT NULL
            )
            SELECT a.target_id, a.email, r.raw_phones, a.profile_phones,
                   (r.raw_phones - a.profile_phones) AS delta
            FROM raw r
            JOIN aggr a ON r.target_id = a.target_id
            WHERE r.raw_phones <> a.profile_phones
            ORDER BY abs(r.raw_phones - a.profile_phones) DESC
            LIMIT %s
        """, (DRIFT_TOP_N,))
        out["phone_drift_top"] = [dict(r) for r in cur.fetchall()]

        # crypto_wallets drift
        cur.execute("""
            WITH raw AS (
                SELECT target_id, COUNT(*) AS raw_wallets
                FROM findings
                WHERE indicator_type = 'crypto_wallet'
                GROUP BY target_id
            ),
            aggr AS (
                SELECT id AS target_id, email,
                       COALESCE(jsonb_array_length(profile_data->'crypto_wallets'), 0) AS profile_wallets
                FROM targets
                WHERE profile_data IS NOT NULL
            )
            SELECT a.target_id, a.email, r.raw_wallets, a.profile_wallets,
                   (r.raw_wallets - a.profile_wallets) AS delta
            FROM raw r
            JOIN aggr a ON r.target_id = a.target_id
            WHERE r.raw_wallets <> a.profile_wallets
            ORDER BY abs(r.raw_wallets - a.profile_wallets) DESC
            LIMIT %s
        """, (DRIFT_TOP_N,))
        out["crypto_drift_top"] = [dict(r) for r in cur.fetchall()]

        # targets with profile_data but missing primary_name
        cur.execute("""
            SELECT COUNT(*) FROM targets
            WHERE profile_data IS NOT NULL
              AND (profile_data->>'primary_name' IS NULL OR profile_data->>'primary_name' = '')
        """)
        out["profile_no_primary_name"] = cur.fetchone()[0]

        # targets with profile_data but empty social_profiles
        cur.execute("""
            SELECT COUNT(*) FROM targets
            WHERE profile_data IS NOT NULL
              AND COALESCE(jsonb_array_length(profile_data->'social_profiles'), 0) = 0
        """)
        out["profile_empty_socials"] = cur.fetchone()[0]

        # totals for context
        cur.execute("SELECT COUNT(*) FROM targets WHERE profile_data IS NOT NULL")
        out["profile_total"] = cur.fetchone()[0]

    return out


# ─────────────────────────── Block D coherence + BFP ───────────────────────────

def block_d_coherence_and_bfp(conn):
    out = {}

    # D1 — module/category drift
    with conn.cursor() as cur:
        cur.execute("""
            WITH per_mod AS (
                SELECT module, category, COUNT(*) AS n
                FROM findings
                GROUP BY module, category
            ),
            totals AS (
                SELECT module, SUM(n) AS total FROM per_mod GROUP BY module
            )
            SELECT p.module, p.category, p.n, t.total,
                   round(100.0 * p.n / t.total, 1) AS pct
            FROM per_mod p
            JOIN totals t ON p.module = t.module
            WHERE t.total >= 20
              AND (100.0 * p.n / t.total) >= 10.0
            ORDER BY p.module, pct DESC
        """)
        rows = cur.fetchall()
        per_mod = defaultdict(list)
        for module, cat, n, total, pct in rows:
            per_mod[module].append({"category": cat, "n": n, "pct": float(pct)})
        out["module_category_drift"] = [
            {"module": m, "total": sum(x["n"] for x in cats), "splits": cats}
            for m, cats in per_mod.items() if len(cats) >= 2
        ]

    # D2 — bfp_behavioral_hash_v1 top buckets
    with conn.cursor() as cur:
        cur.execute("""
            SELECT bfp_behavioral_hash_v1, COUNT(*) AS n
            FROM targets
            WHERE bfp_behavioral_hash_v1 IS NOT NULL
            GROUP BY bfp_behavioral_hash_v1
            ORDER BY n DESC
            LIMIT 20
        """)
        out["bfp_hash_top_buckets"] = [
            {"hash_prefix": h[:16] if h else None, "count": n} for h, n in cur.fetchall()
        ]
        cur.execute("SELECT COUNT(*) FROM targets WHERE bfp_behavioral_hash_v1 IS NOT NULL")
        out["bfp_hash_total"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT bfp_behavioral_hash_v1) FROM targets WHERE bfp_behavioral_hash_v1 IS NOT NULL")
        out["bfp_hash_distinct"] = cur.fetchone()[0]

    # D3 — cross_verification_count distribution
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
              CASE
                WHEN cross_verification_count = 0 THEN '0'
                WHEN cross_verification_count = 1 THEN '1'
                WHEN cross_verification_count BETWEEN 2 AND 4 THEN '2-4'
                ELSE '5+'
              END AS bucket,
              COUNT(*) AS n
            FROM findings
            GROUP BY 1
            ORDER BY 1
        """)
        out["xverif_buckets"] = [{"bucket": b, "count": n} for b, n in cur.fetchall()]

    # D4 — BFP claims integrity
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM bfp_claims")
        out["claims_total"] = cur.fetchone()[0]
        cur.execute("""
            SELECT claim_type, COUNT(*) AS n
            FROM bfp_claims
            GROUP BY claim_type
            ORDER BY n DESC
        """)
        out["claims_by_type"] = [{"type": t, "count": n} for t, n in cur.fetchall()]
        cur.execute("SELECT COUNT(*) FROM bfp_claims WHERE claim_hash IS NULL OR claim_hash = ''")
        out["claims_no_hash"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM bfp_claims WHERE claim_value IS NULL OR claim_value = ''")
        out["claims_empty_value"] = cur.fetchone()[0]

    # D5 — data.scraper vs module column coherence
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT id, module, data->>'scraper' AS data_scraper
            FROM findings
            WHERE data ? 'scraper'
            ORDER BY random()
            LIMIT 200
        """)
        rows = cur.fetchall()
        mismatches = [r for r in rows if r["data_scraper"] and r["module"] != r["data_scraper"]]
        out["data_scraper_sample_total"] = len(rows)
        out["data_scraper_mismatches"] = len(mismatches)
        out["data_scraper_mismatch_samples"] = [
            {"finding_id": str(r["id"]), "module": r["module"], "data_scraper": r["data_scraper"]}
            for r in mismatches[:5]
        ]

    return out


# ─────────────────────────── Report writer ───────────────────────────

def write_report(a, b, c, d, out_path: str):
    ts = datetime.now(timezone.utc).isoformat()
    lines = []
    L = lines.append

    L(f"# S228 — DB Hygiene Audit\n")
    L(f"_Generated: {ts}_\n")
    L(f"_Pattern: S159 / S213 / S224 audit-before-fix. Read-only._\n\n")

    L("## Top-line summary\n")
    top_issues = []
    high_malform = sorted(a["types"], key=lambda x: x["rate_pct"], reverse=True)[:3]
    for t in high_malform:
        if t["rate_pct"] > 5.0:
            top_issues.append(f"- `{t['indicator_type']}`: **{t['rate_pct']}%** malformed in sample "
                              f"({t['malformed']}/{t['sampled']}, total {t['total_in_db']:,} in DB)")
    if b["orphan_count"] > 0:
        top_issues.append(f"- **{b['orphan_count']:,}** orphan targets (no findings)")
    if b["placeholder_count"] > 0:
        top_issues.append(f"- **{b['placeholder_count']}** targets with placeholder name fields (sample-capped at 50)")
    if b["stale_count"] > 0:
        top_issues.append(f"- **{b['stale_count']:,}** targets stale (last_scanned > {STALE_DAYS}d)")
    if b["dup_email_groups"]:
        top_issues.append(f"- **{len(b['dup_email_groups'])}** workspace+email dup groups")
    if c["phone_drift_top"]:
        max_delta = max(abs(r["delta"]) for r in c["phone_drift_top"])
        top_issues.append(f"- Phone aggregation drift detected (max delta {max_delta})")
    if c["crypto_drift_top"]:
        max_delta = max(abs(r["delta"]) for r in c["crypto_drift_top"])
        top_issues.append(f"- Crypto aggregation drift detected (max delta {max_delta})")
    if d["module_category_drift"]:
        top_issues.append(f"- **{len(d['module_category_drift'])}** modules emit under multiple categories (>=10% split)")
    if d["claims_no_hash"] > 0:
        top_issues.append(f"- **{d['claims_no_hash']}** BFP claims with NULL claim_hash (integrity break)")
    if d["data_scraper_mismatches"] > 0:
        top_issues.append(f"- {d['data_scraper_mismatches']}/{d['data_scraper_sample_total']} sample findings: "
                          f"data.scraper ≠ module (emission tag drift)")
    if not top_issues:
        L("OK — No anomalies above threshold detected.\n\n")
    else:
        for line in top_issues:
            L(line)
        L("\n")

    L("## Block A — Indicator value shape\n\n")
    L("| indicator_type | total in DB | sampled | malformed | rate % | top reasons |\n")
    L("|---|---:|---:|---:|---:|---|\n")
    for t in sorted(a["types"], key=lambda x: x["rate_pct"], reverse=True):
        reasons_str = ", ".join(f"{r}={n}" for r, n in t["top_reasons"])
        L(f"| `{t['indicator_type']}` | {t['total_in_db']:,} | {t['sampled']} | {t['malformed']} | "
          f"{t['rate_pct']} | {reasons_str} |")
    L("\n### Sample malformed rows (top 5 per type)\n\n")
    for itype, samples in a["samples"].items():
        if not samples:
            continue
        L(f"**`{itype}`**\n\n")
        L("| value (<=80c) | module | reason | finding_id |\n")
        L("|---|---|---|---|\n")
        for s in samples:
            v = s["value"].replace("|", "\\|")
            L(f"| `{v}` | {s['module']} | {s['reason']} | {s['finding_id']} |")
        L("\n")

    L("\n## Block B — Targets hygiene\n\n")
    L(f"- Orphan targets (no findings): **{b['orphan_count']:,}**\n")
    L(f"- Placeholder-name targets (sample-capped at 50): **{b['placeholder_count']}**\n")
    L(f"- Stale (last_scanned > {STALE_DAYS}d): **{b['stale_count']:,}**\n")
    L(f"- Status=pending BUT last_scanned set: **{b['pending_but_scanned_count']}**\n")
    L(f"- Workspace+email dup groups: **{len(b['dup_email_groups'])}**\n\n")
    if b["orphan_samples"]:
        L("### Orphan samples\n\n")
        L("| email | display_name | status | created_at |\n|---|---|---|---|\n")
        for o in b["orphan_samples"]:
            L(f"| {o['email']} | {o['display_name'] or '—'} | {o['status']} | {o['created_at']} |")
        L("\n")
    if b["placeholder_samples"]:
        L("### Placeholder-name samples\n\n")
        L("| email | display_name | user_first_name | user_last_name |\n|---|---|---|---|\n")
        for p in b["placeholder_samples"][:20]:
            L(f"| {p['email']} | {p['display_name'] or '—'} | {p['user_first_name'] or '—'} | "
              f"{p['user_last_name'] or '—'} |")
        L("\n")
    if b["dup_email_groups"]:
        L("### Workspace+email dups\n\n")
        L("| workspace_id | email | count |\n|---|---|---:|\n")
        for g in b["dup_email_groups"][:20]:
            L(f"| {g['workspace_id']} | {g['email']} | {g['n']} |")
        L("\n")

    L("\n## Block C — Profile aggregation drift\n\n")
    L(f"- Targets with non-null profile_data: **{c['profile_total']:,}**\n")
    L(f"- Targets with profile_data but missing primary_name: **{c['profile_no_primary_name']}**\n")
    L(f"- Targets with profile_data but empty social_profiles: **{c['profile_empty_socials']}**\n\n")
    if c["phone_drift_top"]:
        L(f"### Phone drift (raw findings vs `profile_data->phones`, top {DRIFT_TOP_N})\n\n")
        L("| email | raw | aggregated | delta |\n|---|---:|---:|---:|\n")
        for r in c["phone_drift_top"]:
            L(f"| {r['email']} | {r['raw_phones']} | {r['profile_phones']} | {r['delta']} |")
        L("\n")
    if c["crypto_drift_top"]:
        L(f"### Crypto wallets drift (raw vs `profile_data->crypto_wallets`, top {DRIFT_TOP_N})\n\n")
        L("| email | raw | aggregated | delta |\n|---|---:|---:|---:|\n")
        for r in c["crypto_drift_top"]:
            L(f"| {r['email']} | {r['raw_wallets']} | {r['profile_wallets']} | {r['delta']} |")
        L("\n")

    L("\n## Block D — Module/category coherence + BFP substrate\n\n")
    L(f"### D1 — Modules with category split >=10% on >=2 categories ({len(d['module_category_drift'])} flagged)\n\n")
    if d["module_category_drift"]:
        L("| module | total findings | splits |\n|---|---:|---|\n")
        for m in d["module_category_drift"][:30]:
            splits_str = ", ".join(f"{s['category']}={s['pct']}%" for s in m["splits"])
            L(f"| `{m['module']}` | {m['total']:,} | {splits_str} |")
        L("\n")
    L(f"### D2 — BFP behavioral_hash_v1 distribution\n\n")
    L(f"- Total hashed targets: **{d['bfp_hash_total']:,}** / **{d['bfp_hash_distinct']:,}** distinct hashes\n\n")
    L("| hash prefix (16c) | count |\n|---|---:|\n")
    for b_ in d["bfp_hash_top_buckets"]:
        L(f"| `{b_['hash_prefix']}` | {b_['count']:,} |")
    L(f"\n### D3 — Finding cross_verification_count buckets\n\n")
    L("| bucket | count |\n|---|---:|\n")
    for r in d["xverif_buckets"]:
        L(f"| {r['bucket']} | {r['count']:,} |")
    L(f"\n### D4 — BFP claims integrity\n\n")
    L(f"- Total claims: **{d['claims_total']:,}**\n")
    L(f"- NULL/empty claim_hash: **{d['claims_no_hash']}**\n")
    L(f"- NULL/empty claim_value: **{d['claims_empty_value']}**\n\n")
    L("| claim_type | count |\n|---|---:|\n")
    for c_ in d["claims_by_type"]:
        L(f"| `{c_['type']}` | {c_['count']:,} |")
    L(f"\n### D5 — `data.scraper` vs `module` coherence\n\n")
    L(f"- Sample size: **{d['data_scraper_sample_total']}** (random)\n")
    L(f"- Mismatches: **{d['data_scraper_mismatches']}**\n\n")
    if d["data_scraper_mismatch_samples"]:
        L("| finding_id | module | data.scraper |\n|---|---|---|\n")
        for s in d["data_scraper_mismatch_samples"]:
            L(f"| {s['finding_id']} | {s['module']} | {s['data_scraper']} |")
        L("\n")

    L("\n## Actionable backlog candidates (ranked by anomaly volume)\n\n")
    backlog = []
    for t in a["types"]:
        if t["rate_pct"] > 5.0:
            backlog.append((t["malformed"], f"Cleanup malformed `{t['indicator_type']}` findings "
                                            f"({t['rate_pct']}% rate in sample, est. "
                                            f"{int(t['rate_pct'] * t['total_in_db'] / 100):,} rows)"))
    if b["orphan_count"] > 50:
        backlog.append((b["orphan_count"], f"Prune {b['orphan_count']} orphan targets (no findings)"))
    if b["placeholder_count"] >= 5:
        backlog.append((b["placeholder_count"] * 100, f"Audit {b['placeholder_count']} placeholder-name targets"))
    if c["phone_drift_top"]:
        backlog.append((len(c["phone_drift_top"]) * 10,
                        f"Investigate phone aggregation drift on {len(c['phone_drift_top'])} targets"))
    if c["crypto_drift_top"]:
        backlog.append((len(c["crypto_drift_top"]) * 10,
                        f"Investigate crypto aggregation drift on {len(c['crypto_drift_top'])} targets"))
    if d["module_category_drift"]:
        backlog.append((len(d["module_category_drift"]) * 100,
                        f"Stabilize category emission on {len(d['module_category_drift'])} modules"))
    if d["claims_no_hash"] > 0:
        backlog.append((d["claims_no_hash"] * 1000,
                        f"INTEGRITY: {d['claims_no_hash']} BFP claims with NULL claim_hash"))
    if d["data_scraper_mismatches"] > 5:
        backlog.append((d["data_scraper_mismatches"] * 10,
                        f"Resolve data.scraper/module drift ({d['data_scraper_mismatches']}/200 sample)"))
    for _, item in sorted(backlog, reverse=True):
        L(f"- {item}")
    if not backlog:
        L("_(no backlog candidates above threshold)_")
    L("")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write("\n".join(lines))


def main():
    conn = db_conn()
    try:
        print("Block A — indicator value shape...", flush=True)
        a = block_a_indicator_shape(conn)
        print("Block B — targets hygiene...", flush=True)
        b = block_b_targets_hygiene(conn)
        print("Block C — profile aggregation drift...", flush=True)
        c = block_c_profile_drift(conn)
        print("Block D — module coherence + BFP substrate...", flush=True)
        d = block_d_coherence_and_bfp(conn)
        write_report(a, b, c, d, OUT_PATH)
        print(f"\nReport written: {OUT_PATH}")
        print(f"   - Block A types covered: {len(a['types'])}")
        print(f"   - Block B orphans/placeholders/stale: "
              f"{b['orphan_count']}/{b['placeholder_count']}/{b['stale_count']}")
        print(f"   - Block C drift rows: phone={len(c['phone_drift_top'])} crypto={len(c['crypto_drift_top'])}")
        print(f"   - Block D claims/modules: {d['claims_total']}/{len(d['module_category_drift'])}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
