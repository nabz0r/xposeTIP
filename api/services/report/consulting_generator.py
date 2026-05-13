"""Consulting report Markdown generator (Sprint 112).

Pure functions — no DB, no I/O. Consumes `Target.profile_data` and returns
Markdown strings ready to be written to disk and handed to an analyst for
investigative narrative completion.

Three tiers (Play 1):
- build_quick_profile       — 1 identifier, 3-5 pages (Quick Profile, €2 500)
- build_identity_assessment — 2-3 identifiers, 10-15 pages (Identity Assessment, €6 500)
- build_deep_investigation  — 5-10 identifiers, 25-50 pages (Deep Investigation, €15 000)

All field access uses .get() with defaults. Missing sections render as
"_No data available._" — never a crash.
"""

from datetime import datetime
from typing import Iterable


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

_NO_DATA = "_No data available._"
_VERSION = "xposeTIP v1.1.11"


def _safe(value, default: str = "—") -> str:
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


def _pct(value) -> str:
    """0..1 → '83%'.  None → '—'."""
    if value is None:
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    if v <= 1.0:
        return f"{int(round(v * 100))}%"
    return f"{int(round(v))}%"


def _today() -> str:
    return datetime.utcnow().date().isoformat()


def _profile(target) -> dict:
    return getattr(target, "profile_data", None) or {}


def _short_id(target) -> str:
    tid = getattr(target, "id", None)
    return str(tid)[:8] if tid else "—"


def _label_id(target) -> str:
    """Human-readable identifier label for tables/headers."""
    email = getattr(target, "email", None)
    if email:
        return email
    return _short_id(target)


# ---------------------------------------------------------------------------
# Cover / front matter
# ---------------------------------------------------------------------------

def _cover(case_meta: dict, tier: str, target_count: int) -> list[str]:
    tier_labels = {
        "quick": "Quick Profile",
        "assessment": "Identity Assessment",
        "deep": "Deep Investigation",
    }
    out = [
        "# Identity Intelligence Report",
        f"## {tier_labels.get(tier, tier.title())}",
        "",
        "| | |",
        "|---|---|",
        f"| Client | {_safe(case_meta.get('client_name'))} |",
        f"| Case scope | {_safe(case_meta.get('scope'))} |",
        f"| Deadline | {_safe(case_meta.get('deadline'))} |",
        f"| Analyst | {_safe(case_meta.get('analyst'))} |",
        f"| Identifiers | {target_count} |",
        f"| Generated | {_today()} ({_VERSION}) |",
        "",
        "**CONFIDENTIAL — for the named client only.**",
        "",
    ]
    return out


# ---------------------------------------------------------------------------
# Executive summary
# ---------------------------------------------------------------------------

def _exec_summary(targets: list, tier: str) -> list[str]:
    out = ["## Executive summary", ""]
    if not targets:
        out += [_NO_DATA, ""]
        return out

    bullets: list[str] = []
    total_breaches = 0
    total_socials = 0
    creds_leaked = False
    highest_threat = 0
    highest_threat_id = None
    high_risk_count = 0

    for t in targets:
        p = _profile(t)
        bs = p.get("breach_summary") or {}
        total_breaches += int(bs.get("count") or 0)
        if bs.get("credentials_leaked"):
            creds_leaked = True
        total_socials += len(p.get("social_profiles") or [])
        tscore = getattr(t, "threat_score", None) or 0
        if tscore > highest_threat:
            highest_threat = tscore
            highest_threat_id = _label_id(t)
        fp_risk = ((p.get("fingerprint") or {}).get("risk_level") or "").upper()
        if fp_risk in ("HIGH", "CRITICAL"):
            high_risk_count += 1

    bullets.append(
        f"- **Scope** — {len(targets)} identifier(s) analysed; "
        f"tier: **{tier}**."
    )
    if total_breaches:
        bullets.append(
            f"- **Breach exposure** — {total_breaches} breach record(s) "
            f"across the case" + (" (credentials leaked)." if creds_leaked else ".")
        )
    else:
        bullets.append("- **Breach exposure** — no breach records detected.")
    bullets.append(
        f"- **Digital footprint** — {total_socials} social/platform account(s) total."
    )
    if highest_threat_id:
        bullets.append(
            f"- **Highest threat score** — {highest_threat}/100 ({highest_threat_id})."
        )
    if high_risk_count:
        bullets.append(
            f"- **HIGH/CRITICAL fingerprint risk** — {high_risk_count} identifier(s)."
        )

    out += bullets + [""]
    return out


# ---------------------------------------------------------------------------
# Identity card
# ---------------------------------------------------------------------------

def _identity_card(target, heading_level: int = 2) -> list[str]:
    p = _profile(target)
    name = p.get("primary_name") or getattr(target, "display_name", None) or "Unknown"
    email = getattr(target, "email", None) or "—"
    country = getattr(target, "country_code", None) or "—"
    confidence = (p.get("confidence") or {}).get("overall")
    last_scanned = getattr(target, "last_scanned", None)
    last = last_scanned.isoformat()[:10] if last_scanned else "—"

    h = "#" * heading_level
    return [
        f"{h} Identity card — {_label_id(target)}",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Name | {_safe(name)} |",
        f"| Email | {_safe(email)} |",
        f"| Country | {_safe(country)} |",
        f"| Confidence (overall) | {_pct(confidence)} |",
        f"| Last scanned | {last} |",
        "",
    ]


# ---------------------------------------------------------------------------
# Scores
# ---------------------------------------------------------------------------

def _scores_single(target) -> list[str]:
    out = ["## Exposure & Threat scores", ""]
    exp = getattr(target, "exposure_score", None)
    thr = getattr(target, "threat_score", None)
    if exp is None and thr is None:
        out += [_NO_DATA, ""]
        return out
    out += [
        "| Metric | Score (0-100) |",
        "|---|---|",
        f"| Exposure | {_safe(exp, '—')} |",
        f"| Threat | {_safe(thr, '—')} |",
        "",
    ]
    return out


def _scores_comparative(targets: list) -> list[str]:
    out = ["## Exposure & Threat scores — comparative", ""]
    if not targets:
        out += [_NO_DATA, ""]
        return out
    header = "| Identifier | Exposure | Threat | FP risk |"
    sep = "|---|---|---|---|"
    rows = [header, sep]
    for t in targets:
        p = _profile(t)
        fp_risk = (p.get("fingerprint") or {}).get("risk_level") or "—"
        rows.append(
            f"| {_label_id(t)} "
            f"| {_safe(getattr(t, 'exposure_score', None))} "
            f"| {_safe(getattr(t, 'threat_score', None))} "
            f"| {fp_risk} |"
        )
    out += rows + [""]
    return out


# ---------------------------------------------------------------------------
# Behavioral fingerprint (9 axes)
# ---------------------------------------------------------------------------

_AXIS_LABELS = {
    "accounts": "Accounts",
    "platforms": "Platforms",
    "username_reuse": "Username reuse",
    "breaches": "Breaches",
    "geo_spread": "Geo spread",
    "data_leaked": "Data leaked",
    "email_age": "Email age",
    "security": "Security",
    "public_exposure": "Public exposure",
}


def _fingerprint_top3(target, heading_level: int = 2) -> list[str]:
    p = _profile(target)
    axes = (p.get("fingerprint") or {}).get("axes") or {}
    h = "#" * heading_level
    out = [f"{h} Behavioral fingerprint — top axes", ""]
    if not axes:
        out += [_NO_DATA, ""]
        return out
    ranked = sorted(axes.items(), key=lambda kv: float(kv[1] or 0), reverse=True)[:3]
    out += ["| Axis | Normalised (0-1) |", "|---|---|"]
    for key, val in ranked:
        out.append(f"| {_AXIS_LABELS.get(key, key)} | {float(val or 0):.2f} |")
    risk = (p.get("fingerprint") or {}).get("risk_level") or "—"
    out += ["", f"Overall risk level: **{risk}**.", ""]
    return out


def _fingerprint_full(target, heading_level: int = 2) -> list[str]:
    p = _profile(target)
    fp = p.get("fingerprint") or {}
    axes = fp.get("axes") or {}
    h = "#" * heading_level
    out = [f"{h} Behavioral fingerprint (9 axes) — {_label_id(target)}", ""]
    if not axes:
        out += [_NO_DATA, ""]
        return out
    out += ["| Axis | Normalised (0-1) |", "|---|---|"]
    for key, label in _AXIS_LABELS.items():
        val = axes.get(key)
        if val is None:
            out.append(f"| {label} | — |")
        else:
            try:
                out.append(f"| {label} | {float(val):.2f} |")
            except (TypeError, ValueError):
                out.append(f"| {label} | {_safe(val)} |")
    risk = fp.get("risk_level") or "—"
    score = fp.get("score")
    score_str = f"{score}/100" if score is not None else "—"
    out += [
        "",
        f"Overall fingerprint score: **{score_str}** — risk level **{risk}**.",
        "",
    ]
    return out


def _fingerprint_delta(targets: list) -> list[str]:
    """Pairwise axis delta vs. first target (Deep tier)."""
    out = ["## Fingerprint — per-identifier delta", ""]
    if len(targets) < 2:
        out += [_NO_DATA, ""]
        return out
    baseline = _profile(targets[0]).get("fingerprint", {}).get("axes") or {}
    if not baseline:
        out += [_NO_DATA, ""]
        return out

    header = ["Axis", f"baseline ({_label_id(targets[0])})"] + [
        f"Δ {_label_id(t)}" for t in targets[1:]
    ]
    out.append("| " + " | ".join(header) + " |")
    out.append("|" + "---|" * len(header))

    for key, label in _AXIS_LABELS.items():
        base_val = baseline.get(key)
        try:
            base_f = float(base_val) if base_val is not None else None
        except (TypeError, ValueError):
            base_f = None
        row = [label, f"{base_f:.2f}" if base_f is not None else "—"]
        for t in targets[1:]:
            v = (_profile(t).get("fingerprint", {}).get("axes") or {}).get(key)
            try:
                vf = float(v) if v is not None else None
            except (TypeError, ValueError):
                vf = None
            if base_f is None or vf is None:
                row.append("—")
            else:
                delta = vf - base_f
                sign = "+" if delta >= 0 else ""
                row.append(f"{sign}{delta:.2f}")
        out.append("| " + " | ".join(row) + " |")

    out.append("")
    return out


# ---------------------------------------------------------------------------
# Breach summary
# ---------------------------------------------------------------------------

def _breach_summary_line(target) -> list[str]:
    p = _profile(target)
    bs = p.get("breach_summary") or {}
    out = ["## Breach summary", ""]
    if not bs:
        out += [_NO_DATA, ""]
        return out
    count = bs.get("count", 0)
    sources = bs.get("sources") or []
    out.append(f"- Count: **{count}**")
    if sources:
        out.append(f"- Sources: {', '.join(str(s) for s in sources[:10])}")
    if bs.get("credentials_leaked"):
        out.append("- :warning: **Credentials leaked** in at least one breach.")
    else:
        out.append("- No credentials leaked.")
    out.append("")
    return out


def _breach_timeline(target, heading_level: int = 2) -> list[str]:
    p = _profile(target)
    fp = p.get("fingerprint") or {}
    bs = p.get("breach_summary") or {}
    events = fp.get("timeline_events") or []
    breaches = [e for e in events if (e.get("type") == "breach")]
    h = "#" * heading_level
    out = [f"{h} Breach timeline — {_label_id(target)}", ""]
    creds = bs.get("credentials_leaked")
    out.append(f"- Count: **{bs.get('count', 0)}**")
    out.append(f"- Credentials leaked: **{'yes' if creds else 'no'}**")
    if not breaches:
        out += ["", "_No timeline events available._", ""]
        return out
    out += ["", "| Year | Breach |", "|---|---|"]
    sorted_breaches = sorted(
        breaches,
        key=lambda e: (e.get("year") or (e.get("date") or "0")[:4] or "0"),
        reverse=True,
    )
    for e in sorted_breaches[:20]:
        year = e.get("year") or (e.get("date") or "")[:4] or "?"
        label = e.get("label") or e.get("title") or "Unknown"
        out.append(f"| {year} | {label} |")
    out.append("")
    return out


def _breach_overlap(targets: list) -> list[str]:
    """Cross-ID overlap on breach source names (Deep)."""
    out = ["## Breach overlaps (cross-identifier)", ""]
    if len(targets) < 2:
        out += [_NO_DATA, ""]
        return out
    sets = {
        _label_id(t): {
            str(s).lower()
            for s in ((_profile(t).get("breach_summary") or {}).get("sources") or [])
        }
        for t in targets
    }
    pairs_found = False
    rows = ["| ID A | ID B | Shared breach sources |", "|---|---|---|"]
    keys = list(sets.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            shared = sets[keys[i]] & sets[keys[j]]
            if shared:
                pairs_found = True
                rows.append(f"| {keys[i]} | {keys[j]} | {', '.join(sorted(shared))} |")
    if not pairs_found:
        out += ["_No shared breach sources detected._", ""]
        return out
    out += rows + [""]
    return out


# ---------------------------------------------------------------------------
# Social presence
# ---------------------------------------------------------------------------

def _social_top(target, limit: int = 5) -> list[str]:
    p = _profile(target)
    socials = p.get("social_profiles") or []
    out = ["## Social presence", ""]
    if not socials:
        out += [_NO_DATA, ""]
        return out
    out += [f"Total: **{len(socials)}** account(s). Top {limit}:", "",
            "| Platform | Username | Source |", "|---|---|---|"]
    for s in socials[:limit]:
        out.append(
            f"| {_safe(s.get('platform'))} | {_safe(s.get('username'))} | {_safe(s.get('source'), 'detected')} |"
        )
    out.append("")
    return out


def _social_full(target, heading_level: int = 2, with_clusters: bool = False) -> list[str]:
    p = _profile(target)
    socials = p.get("social_profiles") or []
    h = "#" * heading_level
    out = [f"{h} Social presence — {_label_id(target)}", ""]
    if not socials:
        out += [_NO_DATA, ""]
        return out

    by_platform: dict[str, list[dict]] = {}
    for s in socials:
        key = (s.get("platform") or "Unknown").lower()
        by_platform.setdefault(key, []).append(s)

    out.append(f"Total: **{len(socials)}** account(s) across **{len(by_platform)}** platform(s).")
    out.append("")
    out += ["| Platform | Username | Source | URL |",
            "|---|---|---|---|"]
    for plat in sorted(by_platform):
        for s in by_platform[plat]:
            url = s.get("url") or ""
            out.append(
                f"| {_safe(s.get('platform'))} | {_safe(s.get('username'))} "
                f"| {_safe(s.get('source'), 'detected')} | {url} |"
            )
    out.append("")

    if with_clusters:
        # Username reuse hint: group platforms by username
        uname_platforms: dict[str, list[str]] = {}
        for s in socials:
            u = (s.get("username") or "").strip()
            p_ = s.get("platform") or ""
            if u:
                uname_platforms.setdefault(u, []).append(p_)
        reused = [(u, plats) for u, plats in uname_platforms.items() if len(plats) >= 2]
        if reused:
            out += ["### Persona clustering hints", "",
                    "Usernames appearing on multiple platforms (persona cluster candidates):", "",
                    "| Username | Platforms |", "|---|---|"]
            reused.sort(key=lambda kv: -len(kv[1]))
            for u, plats in reused[:15]:
                out.append(f"| {u} | {', '.join(plats)} |")
            out.append("")
    return out


# ---------------------------------------------------------------------------
# Discovered emails / usernames
# ---------------------------------------------------------------------------

def _discovered(target, heading_level: int = 2) -> list[str]:
    p = _profile(target)
    emails = p.get("emails") or []
    usernames = p.get("usernames") or []
    h = "#" * heading_level
    out = [f"{h} Discovered alternates — {_label_id(target)}", ""]
    if not emails and not usernames:
        out += [_NO_DATA, ""]
        return out

    def _val(item):
        return item if isinstance(item, str) else (item.get("value") or item.get("email") or item.get("username") or "")

    if emails:
        out += [f"**Emails ({len(emails)})**", ""]
        for e in emails[:25]:
            v = _val(e)
            if v:
                out.append(f"- {v}")
        out.append("")
    if usernames:
        out += [f"**Usernames ({len(usernames)})**", ""]
        for u in usernames[:25]:
            v = _val(u)
            if v:
                out.append(f"- {v}")
        out.append("")
    return out


# ---------------------------------------------------------------------------
# Phones / crypto wallets (A1.5)
# ---------------------------------------------------------------------------

def _phones_crypto(target, heading_level: int = 2, flagged_only: bool = False) -> list[str]:
    p = _profile(target)
    phones = p.get("phones") or []
    wallets = p.get("crypto_wallets") or []
    h = "#" * heading_level
    out = [f"{h} Phones & crypto wallets — {_label_id(target)}", ""]

    if flagged_only:
        # Quick tier: only flag presence, not values
        if not phones and not wallets:
            out += ["No phone or crypto-wallet indicators detected.", ""]
            return out
        flags = []
        if phones:
            flags.append(f"**{len(phones)} phone number(s) detected** — see Assessment/Deep tier for values.")
        if wallets:
            flags.append(f"**{len(wallets)} crypto wallet(s) detected** — see Assessment/Deep tier for values.")
        out += flags + [""]
        return out

    if not phones and not wallets:
        out += [_NO_DATA, ""]
        return out

    if phones:
        out += [f"**Phones ({len(phones)})**", ""]
        for ph in phones[:20]:
            out.append(f"- `{ph}`")
        out.append("")
    if wallets:
        out += [f"**Crypto wallets ({len(wallets)})**", "",
                "| Chain | Address |", "|---|---|"]
        for w in wallets[:20]:
            if isinstance(w, dict):
                out.append(f"| {_safe(w.get('chain'))} | `{_safe(w.get('address'))}` |")
            else:
                out.append(f"| ? | `{w}` |")
        out.append("")
    return out


# ---------------------------------------------------------------------------
# Identity estimation
# ---------------------------------------------------------------------------

def _identity_estimation(target, heading_level: int = 2) -> list[str]:
    p = _profile(target)
    est = p.get("identity_estimation") or {}
    h = "#" * heading_level
    out = [f"{h} Identity estimation — {_label_id(target)}", ""]
    if not est:
        out += [_NO_DATA, ""]
        return out

    gender = est.get("gender")
    gender_prob = est.get("gender_probability")
    age = est.get("age")
    age_samples = est.get("age_sample_count")
    nats = est.get("nationalities") or []

    out += [
        "| Attribute | Estimate | Confidence |",
        "|---|---|---|",
        f"| Gender | {_safe(gender)} | {_pct(gender_prob)} |",
        f"| Age | {_safe(age)} | {_safe(age_samples, '—')} sample(s) |",
    ]
    if nats:
        top_nat = nats[0]
        out.append(
            f"| Top nationality | {_safe(top_nat.get('country_code'))} | {_pct(top_nat.get('probability'))} |"
        )
        for n in nats[1:3]:
            out.append(
                f"| Alt. nationality | {_safe(n.get('country_code'))} | {_pct(n.get('probability'))} |"
            )
    out.append("")
    return out


# ---------------------------------------------------------------------------
# Email security
# ---------------------------------------------------------------------------

def _email_security(target, heading_level: int = 2) -> list[str]:
    p = _profile(target)
    sec = p.get("email_security") or {}
    provider = p.get("email_provider") or "—"
    dns_provider = p.get("dns_provider") or "—"
    h = "#" * heading_level
    out = [f"{h} Email security — {_label_id(target)}", ""]
    if not sec and provider == "—" and dns_provider == "—":
        out += [_NO_DATA, ""]
        return out

    def _check(v):
        if v is True:
            return "✓"
        if v is False:
            return "✗"
        return "?"

    out += [
        "| Field | Value |",
        "|---|---|",
        f"| Email provider | {provider} |",
        f"| DNS provider | {dns_provider} |",
        f"| SPF | {_check(sec.get('spf'))} |",
        f"| DKIM | {_check(sec.get('dkim'))} |",
        f"| DMARC | {_check(sec.get('dmarc'))} |",
        f"| Security level | {_safe(sec.get('security_level'))} |",
        "",
    ]
    return out


# ---------------------------------------------------------------------------
# Overlap matrix (Deep)
# ---------------------------------------------------------------------------

def _id_set(t) -> dict[str, set]:
    p = _profile(t)
    socials = p.get("social_profiles") or []
    unames = {
        (s.get("username") or "").strip().lower()
        for s in socials
        if (s.get("username") or "").strip()
    }
    # also include profile.usernames[]
    for u in p.get("usernames") or []:
        v = u if isinstance(u, str) else (u.get("value") or u.get("username") or "")
        if v:
            unames.add(v.strip().lower())
    emails = set()
    for e in p.get("emails") or []:
        v = e if isinstance(e, str) else (e.get("value") or e.get("email") or "")
        if v:
            emails.add(v.strip().lower())
    if getattr(t, "email", None):
        emails.add(t.email.strip().lower())
    return {"usernames": unames, "emails": emails}


def _overlap_matrix(targets: list) -> list[str]:
    out = ["## Cross-identifier overlap matrix", ""]
    if len(targets) < 2:
        out += [_NO_DATA, ""]
        return out
    sets = [(t, _id_set(t)) for t in targets]
    labels = [_label_id(t) for t, _ in sets]
    header = "| | " + " | ".join(labels) + " |"
    sep = "|---" * (len(labels) + 1) + "|"
    out += [
        "Each cell = `|usernames_i ∩ usernames_j| + |emails_i ∩ emails_j|`. "
        "Diagonal = total unique identifiers held by that row's target.",
        "",
        header,
        sep,
    ]
    for i, (t_i, s_i) in enumerate(sets):
        row = [labels[i]]
        for j, (t_j, s_j) in enumerate(sets):
            if i == j:
                total = len(s_i["usernames"]) + len(s_i["emails"])
                row.append(f"**{total}**")
            else:
                inter = len(s_i["usernames"] & s_j["usernames"]) + len(
                    s_i["emails"] & s_j["emails"]
                )
                row.append(str(inter))
        out.append("| " + " | ".join(row) + " |")
    out.append("")
    return out


# ---------------------------------------------------------------------------
# Investigative narrative stubs (analyst writes here)
# ---------------------------------------------------------------------------

def _narrative_stub(label: str | None = None) -> list[str]:
    suffix = f" — {label}" if label else ""
    return [
        f"## [ANALYST NARRATIVE — write here]{suffix}",
        "",
        "_Replace this block with case-specific analytic narrative: hypotheses,"
        " linkage rationale, attribution confidence, recommended next moves._",
        "",
    ]


# ---------------------------------------------------------------------------
# Remediation
# ---------------------------------------------------------------------------

def _remediation_quick(target) -> list[str]:
    p = _profile(target)
    bs = p.get("breach_summary") or {}
    socials = p.get("social_profiles") or []
    sec = p.get("email_security") or {}
    out = ["## Remediation — priority actions", ""]
    bullets = []
    if bs.get("credentials_leaked"):
        bullets.append("- **Rotate password and enable 2FA** on any account reusing the leaked credential set.")
    if (bs.get("count") or 0) > 0:
        bullets.append(
            "- **Review breach sources** below and remove the account or change credentials for each."
        )
    if not sec.get("dmarc"):
        bullets.append("- **Enable DMARC** (and SPF/DKIM if missing) on the email domain.")
    if len(socials) >= 5:
        bullets.append("- **Audit social profiles** — close or harden the 5+ accounts surfaced in this report.")
    while len(bullets) < 3:
        bullets.append("- **Enable 2FA** on every primary account; use a password manager.")
    out += bullets[:3] + [""]
    return out


def _remediation_full(target) -> list[str]:
    p = _profile(target)
    bs = p.get("breach_summary") or {}
    socials = p.get("social_profiles") or []
    sec = p.get("email_security") or {}
    fp_risk = ((p.get("fingerprint") or {}).get("risk_level") or "").upper()

    out = ["## Remediation recommendations", ""]
    high: list[str] = []
    medium: list[str] = []
    low: list[str] = []

    if bs.get("credentials_leaked"):
        high.append(
            "Rotate passwords across all accounts that reused the leaked credential set; "
            "enable 2FA wherever supported."
        )
    if (bs.get("count") or 0) > 5:
        high.append(
            f"High breach exposure ({bs.get('count')}). Walk through each breach source and "
            "either close the account or rotate credentials."
        )
    if not sec.get("dmarc"):
        medium.append("Enable DMARC on the email domain (p=quarantine then p=reject).")
    if not sec.get("spf") or not sec.get("dkim"):
        medium.append("Ensure SPF and DKIM are configured and aligned with DMARC policy.")
    if len(socials) >= 10:
        medium.append(
            f"Large public footprint ({len(socials)} accounts). Audit, prune unused profiles, "
            "lock down visibility settings."
        )
    if fp_risk in ("HIGH", "CRITICAL"):
        high.append(
            "Fingerprint risk is HIGH/CRITICAL — schedule a structured digital-hygiene review "
            "within 30 days."
        )

    low.append("Subscribe to breach-alert services (HIBP / FF Monitor) for the primary email.")
    low.append("Periodically re-scan to detect new leaks and platform appearances.")

    def _emit(level: str, items: list[str]) -> list[str]:
        if not items:
            return []
        return [f"### {level}", ""] + [f"- {x}" for x in items] + [""]

    out += _emit("High priority", high)
    out += _emit("Medium priority", medium)
    out += _emit("Low priority", low)
    if len(out) == 2:
        out += [_NO_DATA, ""]
    return out


def _remediation_strategic(targets: list) -> list[str]:
    """Cross-identifier strategic recommendations (Deep)."""
    out = ["## Strategic recommendations (case-level)", ""]
    if not targets:
        out += [_NO_DATA, ""]
        return out
    out += [
        "- **Operational profile** — treat each identifier as a separate attack surface; "
        "prioritise high-threat IDs first.",
        "- **Cross-account hygiene** — usernames reused across identifiers create pivot risk; "
        "rename or close shared handles.",
        "- **Continuous monitoring** — re-run the scan at a defined cadence (monthly recommended) "
        "and compare fingerprint deltas.",
        "- **Legal/compliance** — if breach data includes regulated PII, notify the relevant "
        "client stakeholder per applicable obligations.",
        "",
    ]
    return out


# ---------------------------------------------------------------------------
# Evidence appendix index (Deep)
# ---------------------------------------------------------------------------

def _evidence_appendix(targets: list) -> list[str]:
    out = ["## Evidence appendix — index", ""]
    if not targets:
        out += [_NO_DATA, ""]
        return out
    out += [
        "The following per-identifier PDF identity reports are available via the platform "
        "(`GET /api/v1/targets/{id}/report/pdf`) and should be attached to this case file:",
        "",
        "| # | Identifier | Target ID | PDF endpoint |",
        "|---|---|---|---|",
    ]
    for i, t in enumerate(targets, 1):
        tid = getattr(t, "id", None)
        out.append(
            f"| {i} | {_label_id(t)} | `{tid}` | `/api/v1/targets/{tid}/report/pdf` |"
        )
    out.append("")
    return out


# ---------------------------------------------------------------------------
# Methodology / sources
# ---------------------------------------------------------------------------

def _methodology_footer() -> list[str]:
    return [
        "---",
        "",
        f"_Methodology: xposeTIP two-phase scan pipeline (gather → compute), "
        f"graph PageRank + Markov confidence, 9-axis behavioural fingerprint. "
        f"Generated by {_VERSION}._",
        "",
    ]


def _methodology_section(profile: dict, with_scrapers: bool = False) -> list[str]:
    sources = profile.get("data_sources") or []
    out = ["## Methodology & sources", "",
           "xposeTIP runs a two-phase pipeline:",
           "",
           "1. **Phase A — gather** (cross-verify → A1.5 phone/crypto extraction → "
           "A1.6 secondary enrichment → Pass 1.5 username expansion → Pass 2).",
           "2. **Phase B — compute** (graph build → PageRank confidence → exposure/threat "
           "scoring → profile aggregation → persona clustering → 9 intelligence analyzers → "
           "9-axis fingerprint).",
           "",
           f"Sources contributing to this profile: **{len(sources)}**.",
           ""]
    if with_scrapers and sources:
        out += ["<details><summary>Source list</summary>", ""]
        for s in sources[:200]:
            out.append(f"- {s}")
        out += ["", "</details>", ""]
    return out


# ---------------------------------------------------------------------------
# Confidentiality notice
# ---------------------------------------------------------------------------

def _confidentiality() -> list[str]:
    return [
        "---",
        "",
        "## Confidentiality notice",
        "",
        "This report is **CONFIDENTIAL** and intended solely for the named client and their "
        "authorised representatives. Findings are derived from publicly available data and "
        "consented OSINT scanning performed by xposeTIP. Redistribution, reproduction, or "
        "use beyond the stated case scope is prohibited without written authorisation.",
        "",
    ]


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------

def build_quick_profile(target, case_meta: dict) -> str:
    """Quick Profile — 1 identifier, 3-5p Markdown. €2 500 tier.

    case_meta: {client_name, scope, deadline, analyst}
    """
    lines: list[str] = []
    lines += _cover(case_meta, "quick", 1)
    lines += _exec_summary([target], "Quick Profile")
    lines += _identity_card(target)
    lines += _scores_single(target)
    lines += _fingerprint_top3(target)
    lines += _breach_summary_line(target)
    lines += _social_top(target, limit=5)
    lines += _phones_crypto(target, flagged_only=True)
    lines += _remediation_quick(target)
    lines += _methodology_footer()
    lines += _confidentiality()
    return "\n".join(lines).rstrip() + "\n"


def build_identity_assessment(targets: list, case_meta: dict) -> str:
    """Identity Assessment — 2-3 identifiers, 10-15p Markdown. €6 500 tier.

    case_meta: {client_name, scope, deadline, primary_target_id, analyst}
    """
    if not targets:
        targets = []
    primary_id = case_meta.get("primary_target_id")
    primary = next(
        (t for t in targets if str(getattr(t, "id", "")) == str(primary_id)),
        targets[0] if targets else None,
    )
    ordered = ([primary] if primary else []) + [t for t in targets if t is not primary]

    lines: list[str] = []
    lines += _cover(case_meta, "assessment", len(ordered))
    lines += _exec_summary(ordered, "Identity Assessment")

    for t in ordered:
        lines += _identity_card(t)
        lines += _fingerprint_full(t)
        lines += _breach_summary_line(t)
        lines += _social_full(t)
        lines += _discovered(t)
        lines += _phones_crypto(t)
        lines += _identity_estimation(t)
        lines += _email_security(t)

    lines += _scores_comparative(ordered)
    lines += _narrative_stub("primary identifier")
    lines += _remediation_full(primary if primary else (ordered[0] if ordered else None))
    lines += _methodology_section(_profile(primary) if primary else {}, with_scrapers=False)
    lines += _confidentiality()
    return "\n".join(lines).rstrip() + "\n"


def build_deep_investigation(targets: list, case_meta: dict) -> str:
    """Deep Investigation — 5-10 identifiers, 25-50p Markdown narrative. €15 000 tier.

    case_meta: {client_name, scope, deadline, primary_target_id, analyst}
    """
    if not targets:
        targets = []
    primary_id = case_meta.get("primary_target_id")
    primary = next(
        (t for t in targets if str(getattr(t, "id", "")) == str(primary_id)),
        targets[0] if targets else None,
    )
    ordered = ([primary] if primary else []) + [t for t in targets if t is not primary]

    lines: list[str] = []
    lines += _cover(case_meta, "deep", len(ordered))
    lines += _exec_summary(ordered, "Deep Investigation")
    lines += _scores_comparative(ordered)

    # Per-identifier deep blocks
    for t in ordered:
        lines += [f"## Identifier — {_label_id(t)}", ""]
        lines += _identity_card(t, heading_level=3)
        lines += _fingerprint_full(t, heading_level=3)
        lines += _breach_timeline(t, heading_level=3)
        lines += _social_full(t, heading_level=3, with_clusters=True)
        lines += _discovered(t, heading_level=3)
        lines += _phones_crypto(t, heading_level=3)
        lines += _identity_estimation(t, heading_level=3)
        lines += _email_security(t, heading_level=3)

    # Cross-identifier sections
    lines += _fingerprint_delta(ordered)
    lines += _breach_overlap(ordered)
    lines += _overlap_matrix(ordered)

    # Analyst narrative stubs (3 for Deep)
    lines += _narrative_stub("attribution & linkage hypotheses")
    lines += _narrative_stub("persona reconstruction")
    lines += _narrative_stub("recommended next investigative moves")

    # Remediation
    lines += _remediation_full(primary if primary else (ordered[0] if ordered else None))
    lines += _remediation_strategic(ordered)

    # Evidence + methodology
    lines += _evidence_appendix(ordered)
    lines += _methodology_section(_profile(primary) if primary else {}, with_scrapers=True)
    lines += _confidentiality()
    return "\n".join(lines).rstrip() + "\n"
