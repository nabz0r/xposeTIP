"""PivotStrategy — rule-based pivot query generator for Discovery Phase C.

Takes discovery leads from a completed round and generates follow-up
queries for the next round. Each rule targets a specific lead type
and generates queries designed to find deeper intelligence.

Pure function: no DB, no side effects, no state.
"""
from dataclasses import dataclass


@dataclass
class PivotQuery:
    query: str
    reason: str
    source_lead_id: str | None
    priority: float
    pivot_type: str


_MANAGED_DOMAINS = {
    "gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "protonmail.com",
    "proton.me", "icloud.com", "live.com", "aol.com", "mail.com", "ymail.com",
    "gmx.com", "zoho.com", "fastmail.com", "tutanota.com", "hey.com", "pm.me",
    "free.fr", "orange.fr", "wanadoo.fr", "sfr.fr", "laposte.net",
    "web.de", "t-online.de", "posteo.de", "mailbox.org",
}

_COUNTRY_NAMES = {
    "LU": "Luxembourg", "FR": "France", "DE": "Germany", "BE": "Belgium",
    "NL": "Netherlands", "CH": "Switzerland", "AT": "Austria", "IT": "Italy",
    "ES": "Spain", "PT": "Portugal", "GB": "United Kingdom", "US": "United States",
    "CA": "Canada", "AU": "Australia", "JP": "Japan", "IN": "India",
    "BR": "Brazil", "SE": "Sweden", "NO": "Norway", "DK": "Denmark",
    "FI": "Finland", "IE": "Ireland", "PL": "Poland", "CZ": "Czech Republic",
}


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if len(parts) >= 2:
        return parts[0], parts[-1]
    return full_name, ""


def _get_email_domain(email: str) -> str | None:
    if "@" not in email:
        return None
    domain = email.split("@")[1].lower()
    if domain in _MANAGED_DOMAINS:
        return None
    return domain


def _normalize_query(q: str) -> str:
    return " ".join(sorted(q.lower().split()))


def generate_pivots(
    leads: list[dict],
    profile: dict,
    email: str,
    budget_remaining: int,
    previous_queries: list[str],
) -> list[PivotQuery]:
    """Generate ranked follow-up queries from discovery leads."""
    all_pivots = []
    known_usernames = set(u.lower() for u in (profile.get("usernames") or []))
    org = profile.get("organization") or ""
    country = (profile.get("country_code") or "").upper()
    country_name = _COUNTRY_NAMES.get(country, country)
    corp_domain = _get_email_domain(email)

    for lead in leads:
        lt = lead.get("lead_type", "")
        lv = lead.get("lead_value", "")
        conf = lead.get("confidence", 0)
        lid = lead.get("id")

        if conf < 0.70 or not lv:
            continue

        # Rule 1 — Username platform expansion
        if lt == "username" and conf >= 0.70:
            all_pivots.append(PivotQuery(
                query=f'"{lv}" site:github.com OR site:medium.com OR site:dev.to',
                reason=f"Expanding username {lv} to dev/professional platforms",
                source_lead_id=lid, priority=0.9, pivot_type="username_expansion",
            ))
            all_pivots.append(PivotQuery(
                query=f'"{lv}" site:linkedin.com',
                reason=f"Expanding username {lv} to LinkedIn",
                source_lead_id=lid, priority=0.9, pivot_type="username_expansion",
            ))

        # Rule 2 — Name + Organization role search
        if lt == "name" and conf >= 0.75 and org:
            all_pivots.append(PivotQuery(
                query=f'"{lv}" "{org}" role OR title OR position',
                reason=f"Searching professional role for {lv} at {org}",
                source_lead_id=lid, priority=0.85, pivot_type="role_search",
            ))

        # Rule 3 — Name + Location search
        if lt == "name" and conf >= 0.75 and country:
            all_pivots.append(PivotQuery(
                query=f'"{lv}" {country_name} conference OR speaker OR interview',
                reason=f"Searching public appearances for {lv} in {country_name}",
                source_lead_id=lid, priority=0.6, pivot_type="name_search",
            ))

        # Rule 4 — Organization staff directory
        if lt in ("name", "mention") and "organization" in lt.lower() or (
            lt == "name" and conf >= 0.80 and lv.lower() == org.lower() and org
        ):
            pass  # handled below for explicit org leads

        if lt == "organization" or (lt == "name" and conf >= 0.90 and org and lv.lower() == org.lower()):
            org_name = lv if lt == "organization" else org
            if corp_domain:
                all_pivots.append(PivotQuery(
                    query=f"site:{corp_domain} team OR staff OR about-us",
                    reason=f"Looking for staff directory at {org_name}",
                    source_lead_id=lid, priority=0.8, pivot_type="org_lookup",
                ))
            if country:
                all_pivots.append(PivotQuery(
                    query=f'"{org_name}" employees {country_name}',
                    reason=f"Looking for {org_name} employees in {country_name}",
                    source_lead_id=lid, priority=0.8, pivot_type="org_lookup",
                ))

        # Rule 5 — Email domain recon
        if lt == "email" and conf >= 0.75 and "@" in lv:
            domain = lv.split("@")[1].lower()
            if domain not in _MANAGED_DOMAINS:
                all_pivots.append(PivotQuery(
                    query=f"site:{domain} contact OR team OR staff",
                    reason=f"Exploring email domain {domain} for colleagues",
                    source_lead_id=lid, priority=0.7, pivot_type="domain_recon",
                ))

        # Rule 6 — Email variant generation (generates leads, not web queries)
        if lt == "name" and conf >= 0.80 and corp_domain:
            first, last = _split_name(lv)
            if first and last:
                all_pivots.append(PivotQuery(
                    query=f'"{first}.{last}@{corp_domain}" OR "{first[0]}{last}@{corp_domain}"',
                    reason=f"Testing email variants for {lv} at {corp_domain}",
                    source_lead_id=lid, priority=0.5, pivot_type="email_variant",
                ))

        # Rule 7 — Corporate registry (Luxembourg)
        if (lt == "organization" or (lt == "name" and org and lv.lower() == org.lower())) and conf >= 0.80:
            if country == "LU" or "luxembourg" in lv.lower():
                org_name = lv if lt == "organization" else org
                all_pivots.append(PivotQuery(
                    query=f'"{org_name}" RCS Luxembourg',
                    reason=f"Searching Luxembourg corporate registry for {org_name}",
                    source_lead_id=lid, priority=0.75, pivot_type="org_lookup",
                ))

        # Rule 8 — Associate discovery
        if lt == "name" and conf >= 0.80 and org:
            all_pivots.append(PivotQuery(
                query=f'"{org}" CEO OR CTO OR director OR founder',
                reason=f"Searching for associates at {org}",
                source_lead_id=lid, priority=0.4, pivot_type="associate_search",
            ))

        # Rule 9 — Leaked data pivot
        if lt == "email" and conf >= 0.80:
            all_pivots.append(PivotQuery(
                query=f'"{lv}" paste OR leak OR breach',
                reason=f"Checking for leaked data mentioning {lv}",
                source_lead_id=lid, priority=0.65, pivot_type="leaked_data",
            ))

        # Rule 10 — Deep username search (non-mainstream)
        if lt == "username" and conf >= 0.80 and lv.lower() not in known_usernames:
            all_pivots.append(PivotQuery(
                query=f'"{lv}" forum OR blog OR comment',
                reason=f"Deep searching username {lv} on forums",
                source_lead_id=lid, priority=0.55, pivot_type="platform_search",
            ))

    # Dedup against previous queries
    prev_normalized = {_normalize_query(q) for q in previous_queries}
    deduped = [p for p in all_pivots if _normalize_query(p.query) not in prev_normalized]

    # Sort by priority descending
    deduped.sort(key=lambda p: p.priority, reverse=True)

    # Budget cap: at most half remaining budget
    max_queries = max(1, budget_remaining // 2)
    return deduped[:max_queries]
