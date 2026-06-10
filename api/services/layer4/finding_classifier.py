"""S262 — Typed finding classification + honest typed confidence (shadow compute).

Kills "confidence = volume of accounts." Every finding is one of:

  echo          — re-states the seed (the email/domain/IP itself, DNS/WHOIS/breach
                  infrastructure) OR repeats a bare collision handle. Zero identity
                  weight. This is the eric@plutontechnologies.com trap.
  account       — a platform presence whose handle does NOT link back to the anchor
                  and is NOT independently cross-verified. Weak, saturates low.
  corroborating — an account that back-references the seed domain OR is cross-verified
                  by an independent source. Strong.
  entity        — a real-world record naming a person (corporate officer, gazette,
                  compliance). Strong. NOTE: BODACC/SEC filer names are often
                  COMPANIES not persons (see S211) — person-vs-company split is S-C.
  noise         — metadata/intelligence/analyzer output with no identity weight.

SINGLE source of truth (`compute_typed_confidence`) is called by BOTH the aggregator
(writes the shadow field) AND the audit (read-only) so the two cannot drift.

S262 is SHADOW ONLY — `confidence.overall` is never modified here.

THREE corrections vs the S262 spec draft, all verified against the live corpus and
all in the S261 lineage ("collision repetition is not verification"):
  1. `cross_verification_count > 0` does NOT mean corroborating for a BARE COLLISION
     HANDLE — 50 modules all finding "eric" cross-verify each other. Bare collision
     handles with no domain back-reference are suppressed to `echo` before the
     cross-verification check. Without this, eric scores ~0.85 (acceptance #1 wants
     ≤0.20).
  2. `indicator_type in {domain, ip}` is always echo (infrastructure / never a person
     account) — the live `metadata` bucket (5.4K rows) is dominated by dns_deep,
     email_validator, rdap_domain etc. on the seed domain.
  3. ECHO_MODULES extended from the real DB sample (domain/email infrastructure that
     emits sub-domains/hosts whose indicator_value != the seed but is still pure echo).
"""

import json
import re

# Categories that always re-state the seed input.
ECHO_CATEGORIES = {"breach", "domain_registration", "paste"}

# Domain/email/network infrastructure modules. Belt-and-braces for findings whose
# indicator_value is a sub-domain/host (!= the seed) but is still pure echo.
ECHO_MODULES = {
    "dns_deep", "dns_dmarc_check", "dns_txt_saas", "rdap_domain", "whois_lookup",
    "crtsh_subdomains", "hackertarget_hosts", "alienvault_otx_domain", "virustotal",
    "securitytrails_ping", "email_validator", "disposable_email_check", "disify_email",
    "mailcheck_email", "emailrep_scanner_validate", "geoip", "maxmind_geo",
}

# indicator_types that never represent a person's account.
ECHO_TYPES = {"domain", "ip"}

ACCOUNT_CATEGORIES = {"social_account", "social"}

# Real-world entity records — strong identity signal.
ENTITY_CATEGORIES = {"corporate", "formal_records", "compliance"}

_IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$|:")


def _is_ip(val: str) -> bool:
    return bool(val) and bool(_IP_RE.search(val))


def _url_queries_handle(url: str, handle: str) -> bool:
    """True if the URL was fetched by querying `handle` as a path segment.

    Collision-farm findings store the SCRAPED PAGE TITLE in indicator_value
    ('Eric on about.me', 'Sign Up', 'Eric 🤪🛹 13y/o'), not the queried handle —
    but the handle survives in the URL, either as a path segment (about.me/eric,
    threads.net/@eric, api.github.com/users/eric, snapchat.com/add/eric) OR as a
    query-param value (mastodon ?q=eric, keybase ?usernames=eric, devto ?url=eric).
    Matched with boundaries so '/eric' hits but '/erica' does not.
    """
    if not url or not handle:
        return False
    u = url.lower()
    h = re.escape(handle)
    # path segment: /eric or /@eric  (boundary: next /, ?, # or end)
    if re.search(rf"/@?{h}(?:[/?#]|$)", u):
        return True
    # query-param value: ?q=eric, &usernames=eric, ?url=@eric
    if re.search(rf"[?&][^=&]+=@?{h}(?:[&#]|$)", u):
        return True
    return False


def classify_finding(f, seed_email: str, seed_domain: str, collision_local: str | None = None) -> str:
    """Return one of: 'echo' | 'account' | 'corroborating' | 'entity' | 'noise'.

    collision_local: the seed local-part IFF it is collision-prone (S261). When set,
    a bare handle equal to it with no domain back-reference is treated as echo —
    collision repetition is not corroboration.
    """
    val = (f.indicator_value or "").strip().lower()
    itype = (f.indicator_type or "").lower()
    cat = f.category or ""
    mod = f.module or ""
    sd = (seed_domain or "").lower()
    se = (seed_email or "").lower()

    # 1. echo — seed re-statement / pure infrastructure
    if cat in ECHO_CATEGORIES or mod in ECHO_MODULES:
        return "echo"
    if itype in ECHO_TYPES:
        return "echo"
    if val and (val == se or val == sd):
        return "echo"
    if _is_ip(val):
        return "echo"

    # 2. collision echo (S261) — a bare collision handle that does not link back to
    #    the seed domain is repetition, NOT corroboration, regardless of how many
    #    independent sources "found" it. The handle may be in indicator_value, in a
    #    data field, OR (collision-farm profile scrapes) only in the URL path while
    #    indicator_value holds the scraped page title.
    if collision_local:
        data = f.data if isinstance(f.data, dict) else {}
        data_handle = ""
        for k in ("username", "login", "handle", "preferredUsername"):
            v = data.get(k)
            if v:
                data_handle = str(v).strip().lower()
                break
        queried_collision = (
            val == collision_local
            or data_handle == collision_local
            or _url_queries_handle(f.url or "", collision_local)
        )
        if queried_collision:
            blob = f"{f.url or ''} {json.dumps(data, default=str)}".lower()
            # the seed domain appearing only as the queried-handle path doesn't count
            if not (sd and sd in blob):
                return "echo"

    # 3. entity — real-world record
    if cat in ENTITY_CATEGORIES:
        return "entity"

    # 4. account vs corroborating — platform presence
    if cat in ACCOUNT_CATEGORIES or itype in ("username", "social_url"):
        if (getattr(f, "cross_verification_count", 0) or 0) > 0:
            return "corroborating"
        blob = f"{f.url or ''} {json.dumps(f.data or {}, default=str)}".lower()
        if sd and sd in blob:
            return "corroborating"
        return "account"

    # 5. noise — metadata / intelligence / analyzer output, neutral
    return "noise"


def compute_typed_confidence(findings, profile_names, seed_email, seed_domain):
    """SINGLE source of truth for typed confidence — used by BOTH the aggregator
    (writes the shadow field) AND the audit (read-only). Pure function, no DB writes,
    so the two paths cannot drift.

    Returns (typed_overall: float, breakdown: dict).
    """
    from api.services.layer4.source_scoring import get_source_reliability
    from api.services.layer4.collision_guard import (
        is_junk_name_token, is_collision_prone_localpart,
    )

    seed_local = (seed_email or "").split("@")[0].strip().lower()
    collision_local = seed_local if is_collision_prone_localpart(seed_local) else None

    buckets = {"echo": 0, "account": [], "corroborating": [], "entity": [], "noise": 0}
    for f in findings:
        t = classify_finding(f, seed_email, seed_domain, collision_local)
        if t in ("account", "corroborating", "entity"):
            buckets[t].append(f)
        else:
            buckets[t] += 1

    corrob = len(buckets["corroborating"]) + len(buckets["entity"])
    corrob_score = min(0.65, 0.22 * corrob)                       # 3 corroborated → ~0.65
    acct_weight = sum(get_source_reliability(f.module) for f in buckets["account"])
    acct_score = min(0.30, 0.06 * acct_weight)                    # bare accounts saturate low
    clean = [n for n in profile_names if not is_junk_name_token(n.get("value", ""))]
    name_score = 0.20 if (clean and corrob > 0) else (0.10 if clean else 0.0)

    typed_overall = round(min(1.0, corrob_score + acct_score + name_score), 2)
    breakdown = {
        "echo": buckets["echo"],
        "account": len(buckets["account"]),
        "corroborating": len(buckets["corroborating"]),
        "entity": len(buckets["entity"]),
        "noise": buckets["noise"],
    }
    return typed_overall, breakdown
