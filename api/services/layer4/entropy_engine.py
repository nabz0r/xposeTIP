"""S265 — Entropy layer v0 (identifying-bits, shadow).

Information-theoretic resolution power. A random human's identity ≈ 33 bits
(2^33 ≈ world population); each learned fact removes ΔS = -log2(Pr(X=x)) bits.
xposeTIP turns the metric that condemns mass fingerprinting (Clearview) into a way
to BOUND and HONESTLY DISCLOSE its own resolution power.

This is a PURE function — no DB writes. The aggregator stores the result as a
SHADOW field (`identifying_bits`); it does NOT feed confidence["overall"] in v0.

The five governors (the rigorous spine — non-negotiable):
  1. bits per axis = -log2(p), p = prevalence of the observed value on that axis.
  2. sum across DISTINCT axes only; ONE most-specific value per axis; correlated
     axes are pick-one / discounted — never double-counted (summing correlated bits
     = over-claiming uniqueness, the exact error we refuse).
  3. conservative prior: uncertain p → round toward COMMON (fewer bits → under-claim);
     unknown axis → 0 bits, never a guess. False-negative on uniqueness is safe;
     over-claim is the overreach.
  4. global-unique cap: total is strictly capped below log2(world_pop)≈33; OSINT-only
     data caps at cap_bits (~20, anonymity-set ~1M). We NEVER assert global uniqueness
     without network-layer signals (WiFi/MAC/JA3/ASN — a mathematical necessity, BFP).
  5. descriptive, not a flip — output is bits + breakdown + verdict; overall untouched.

v0 axes: country, email_provider, name(coarse). company-anonymity-set = v1 (needs
headcount via AR-1 register). Adding an axis = add a prior + a contributor.
"""
import json
import logging
import math
import os

logger = logging.getLogger(__name__)

_PRIORS = None

# ccTLD → ISO, for the governor-2 country↔email correlation discount (kept local —
# the core scoring layer must not depend on the discovery layer).
_CCTLD_TO_ISO = {
    "lu": "LU", "fr": "FR", "de": "DE", "be": "BE", "nl": "NL", "ch": "CH",
    "it": "IT", "es": "ES", "at": "AT", "se": "SE", "no": "NO", "dk": "DK",
    "ie": "IE", "pt": "PT", "uk": "GB", "jp": "JP", "au": "AU", "ca": "CA",
    "in": "IN", "br": "BR", "fi": "FI", "cz": "CZ", "pl": "PL", "gr": "GR",
    "hu": "HU", "ro": "RO", "sk": "SK", "ee": "EE", "cy": "CY", "mt": "MT", "is": "IS",
}


def load_priors() -> dict:
    global _PRIORS
    if _PRIORS is None:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entropy_priors.json")
        try:
            _PRIORS = json.loads(open(p).read())
        except Exception as e:
            logger.warning("entropy_priors.json unreadable: %s", e)
            _PRIORS = {}
    return _PRIORS


def _bits(p: float) -> float:
    """Governor 1 — bits = -log2(p), clamped to [0, ∞). p≥1 → 0 bits (no info)."""
    if not p or p <= 0:
        return 0.0
    p = min(1.0, p)
    return max(0.0, -math.log2(p))


def _extract_country(profile: dict) -> str | None:
    geo = profile.get("geo_consistency") or {}
    if isinstance(geo, dict) and geo.get("primary_country"):
        return str(geo["primary_country"]).upper()
    cc = profile.get("country_code") or profile.get("country")
    return str(cc).upper() if cc else None


def _extract_email_domain(profile: dict, findings) -> str | None:
    """Most-frequent email domain across email-type findings = the seed domain."""
    counts = {}
    for f in findings or []:
        if (getattr(f, "indicator_type", "") or "") == "email":
            v = (getattr(f, "indicator_value", "") or "").strip().lower()
            if "@" in v:
                dom = v.split("@", 1)[1]
                if dom:
                    counts[dom] = counts.get(dom, 0) + 1
    if counts:
        return max(counts, key=counts.get)
    # fallback: profile email if present
    for k in ("email", "primary_email"):
        v = (profile.get(k) or "")
        if "@" in v:
            return v.split("@", 1)[1].lower()
    return None


def _name_first_token(profile: dict) -> str | None:
    nm = (profile.get("primary_name") or "").strip()
    if not nm:
        return None
    parts = nm.split()
    return parts[0].lower() if parts else None


def compute_identifying_bits(profile: dict, findings, priors: dict):
    """Return (total_bits, breakdown). Pure, governed, shadow-only."""
    priors = priors or {}
    world = priors.get("world_population", 8_100_000_000)
    global_bits = priors.get("global_unique_bits", 33)
    cap = priors.get("cap_bits", 20)

    by_axis = {}
    axes_unknown = ["company_anonymity_set"]  # v1, always disclosed as not-yet-measured

    # --- axis: country (governor 1; unknown → 0 bits, governor 3) ---
    country = _extract_country(profile)
    if country:
        pops = priors.get("country_population", {})
        pop = pops.get(country, pops.get("_default", 100_000_000))
        p = min(1.0, pop / world)
        by_axis["country"] = {"value": country, "p": round(p, 8), "bits": round(_bits(p), 2)}
    else:
        axes_unknown.append("country")

    # --- axis: email_provider (free-mail share, or conservative corporate floor) ---
    dom = _extract_email_domain(profile, findings)
    if dom:
        shares = priors.get("email_provider_share", {})
        if dom in shares:
            p = shares[dom]
            label = dom
        else:
            # not a known free-mail provider → corporate/custom domain. Conservative
            # floor (governor 3) — the REAL identifying power (company headcount) is
            # the v1 company-anonymity-set axis, deliberately NOT claimed here.
            p = shares.get("_corporate", 0.03)
            label = "corporate"
        by_axis["email_provider"] = {"value": label, "p": round(p, 8), "bits": round(_bits(p), 2)}
    else:
        axes_unknown.append("email_provider")

    # --- axis: name (coarse v0 — common/rare via collision_guard list) ---
    first = _name_first_token(profile)
    if first:
        from api.services.layer4.collision_guard import COMMON_GIVEN_NAMES
        ncfg = priors.get("name", {})
        if first in COMMON_GIVEN_NAMES:
            p = ncfg.get("common_p", 0.10)
            val = "common"
        else:
            p = ncfg.get("rare_p_floor", 0.04)   # conservative floor — not a true freq
            val = "rare"
        by_axis["name"] = {"value": val, "p": round(p, 8), "bits": round(_bits(p), 2), "coarse": True}
    else:
        axes_unknown.append("name")

    # --- governor 2: correlation discount (pick-one) ---
    # A corporate email on a ccTLD domain (helene@aca.LU) makes country and
    # email_provider CORRELATED: the .lu TLD IS the country signal, so summing
    # country(LU)+corporate double-counts the "LU corporate entity" information —
    # the over-claim governor 2 forbids. When the domain ccTLD maps to the country
    # axis, keep ONLY the higher-bits axis (pick-one) and discount the other to 0.
    if dom and "country" in by_axis and "email_provider" in by_axis:
        tld = dom.rsplit(".", 1)[-1].lower()
        if _CCTLD_TO_ISO.get(tld) == by_axis["country"]["value"]:
            lo = min(("country", "email_provider"), key=lambda k: by_axis[k]["bits"])
            by_axis[lo]["bits"] = 0.0
            by_axis[lo]["correlated_with"] = "country" if lo == "email_provider" else "email_provider"

    raw_bits = sum(a["bits"] for a in by_axis.values())

    # --- governor 4: global-unique cap ---
    capped = raw_bits > cap
    total = round(min(raw_bits, cap), 2)

    anonymity_set = max(1, int(round(2 ** max(0.0, global_bits - total))))
    if total <= 1:
        verdict = "near-zero resolution (cold start — almost nothing known)"
    elif anonymity_set >= 1_000_000:
        verdict = f"narrows to ~{anonymity_set // 1_000_000}M+ people (weakly identifying)"
    elif anonymity_set >= 1000:
        verdict = f"narrows to ~{anonymity_set // 1000}k people"
    else:
        verdict = f"narrows to ~{anonymity_set} people (strongly identifying — but not globally unique)"

    breakdown = {
        "identifying_bits": total,
        "anonymity_set": anonymity_set,
        "verdict": verdict,
        "by_axis": by_axis,
        "capped": capped,
        "axes_unknown": axes_unknown,
        "global_unique_bits": global_bits,
    }
    return total, breakdown
