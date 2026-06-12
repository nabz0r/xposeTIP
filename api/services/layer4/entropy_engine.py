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


def compute_cluster_bits(bfp_hash: str, bucket_count: int, corpus_total: int) -> dict:
    """S271 — H(cluster) = -log2(p_bucket): the BFP 'belonging' half of the chain rule.
    p_bucket = how common this behavioral bucket is in the corpus. Small by design in
    cold-start (a dominant mono-bucket → p high → few bits) — that is clustering-not-
    uniqueness made arithmetic, not a defect. Never a uniqueness claim."""
    if not bfp_hash or corpus_total <= 0 or bucket_count <= 0:
        return {"cluster_bits": 0.0, "cluster_bucket": bfp_hash,
                "cluster_corpus_fraction": None, "cluster_note": "no corpus signal"}
    p = min(1.0, bucket_count / corpus_total)
    return {
        "cluster_bits": round(_bits(p), 2),
        "cluster_bucket": bfp_hash,
        "cluster_corpus_fraction": f"{bucket_count}/{corpus_total}",
        "cluster_p": round(p, 4),
        "cluster_note": "cold-start" if p > 0.5 else "differentiated",
    }


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


def _extract_gender(profile: dict) -> tuple:
    """(label, probability) or (None, None). Reads the already-computed
    genderize result — no new scraper. probability gates the bits."""
    g = (profile.get("gender") or "").strip().lower()
    if g not in ("male", "female"):
        return None, None
    est = profile.get("identity_estimation") or {}
    prob = est.get("gender_probability")
    try:
        prob = float(prob) if prob is not None else None
    except (TypeError, ValueError):
        prob = None
    return g, prob


def _name_first_token(profile: dict) -> str | None:
    nm = (profile.get("primary_name") or "").strip()
    if not nm:
        return None
    parts = nm.split()
    return parts[0].lower() if parts else None


def _name_prevalence(name_token: str, priors: dict) -> tuple:
    """Coarse name prevalence p + label (common/rare). Single source for the resolved
    name axis AND the S272 password-derived candidate_name fallback."""
    from api.services.layer4.collision_guard import COMMON_GIVEN_NAMES
    ncfg = (priors or {}).get("name", {})
    tok = (name_token or "").strip().lower().split()[0] if (name_token or "").strip() else ""
    if tok in COMMON_GIVEN_NAMES:
        return ncfg.get("common_p", 0.10), "common"
    return ncfg.get("rare_p_floor", 0.04), "rare"


def _apply_correlations(by_axis: dict, dom: str | None, priors: dict) -> None:
    """Generalized governor-2 (S281). Mutates by_axis in place.

    For each declared {from,to,lambda,mode} in priors['axis_correlations']:
      - both axes must be present in by_axis, else skip
      - if a 'mode' gate is named, it must pass, else skip
      - discount the DEPENDENT axis 'to': bits *= (1 - lambda)   [decision (a)]
      - tag: to.correlated_with = from ; to.correlation_lambda = lambda (only λ<1)

    Single-level only (decision b): we read the ORIGINAL bits snapshot, so a
    discounted axis never cascades into another discount in the same pass.
    """
    correlations = (priors or {}).get("axis_correlations") or []
    if not correlations:
        return
    # snapshot BEFORE any mutation — guarantees single-level (decision b)
    orig = {k: v["bits"] for k, v in by_axis.items()}
    for corr in correlations:
        frm, to = corr.get("from"), corr.get("to")
        if not frm or not to or frm not in by_axis or to not in by_axis:
            continue
        mode = corr.get("mode")
        if mode == "ccTLD_match":
            # reproduces the pre-S281 hard-coded gate exactly
            if not dom:
                continue
            tld = dom.rsplit(".", 1)[-1].lower()
            if _CCTLD_TO_ISO.get(tld) != by_axis[frm]["value"]:
                continue
        elif mode:
            continue  # unknown named gate → fail closed (no discount applied)
        lam = corr.get("lambda", 0.0) or 0.0
        by_axis[to]["bits"] = round(orig[to] * (1 - lam), 2)
        by_axis[to]["correlated_with"] = frm
        if lam < 1:
            # residual state (S282 plumbing) — never tagged on the λ=1 pick-one
            # case so the existing UI render stays byte-identical
            by_axis[to]["correlation_lambda"] = lam


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

    # --- axis: gender (S282 — reads pre-computed genderize, ~1 bit, gated) ---
    gval, gprob = _extract_gender(profile)
    gcfg = priors.get("gender", {})
    floor = gcfg.get("prob_floor", 0.70)
    if gval and (gprob is None or gprob >= floor):
        p = gcfg.get("p_base", 0.5)
        by_axis["gender"] = {"value": gval, "p": round(p, 6),
                             "bits": round(_bits(p), 2), "coarse": True,
                             "prob": gprob}
    else:
        axes_unknown.append("gender")

    # --- governor 2 (generalized, S281): data-driven correlation discount ---
    # gender is set above so the name→gender correlation (S282) applies here.
    _apply_correlations(by_axis, dom, priors)

    # --- L1: breach-derived composition candidates (S272), COARSE, GOVERNED ---
    # Read the password/host-name shape candidates S270 attached to hudsonrock findings
    # (findings already passed in). The cleartext never reached here — only candidates.
    cand = []
    for f in (findings or []):
        if getattr(f, "module", "") == "hudsonrock_search":
            d = getattr(f, "data", None)
            if isinstance(d, dict):
                cand.extend(d.get("composition_candidates") or [])

    # candidate_year → birth_year axis (new, coarse). One value, most-specific per axis.
    yr = next((c.get("value") for c in cand if c.get("attribute") == "candidate_year"), None)
    if yr is not None and "birth_year" not in by_axis:
        yp = (priors.get("birth_year_prevalence") or {}).get(str(yr)) or priors.get("birth_year_default_p", 0.013)
        by_axis["birth_year"] = {"value": yr, "p": round(yp, 6), "bits": round(_bits(yp), 2),
                                 "coarse": True, "source": "password_composition"}

    # candidate_name → name axis ONLY as a coarse fallback (governor 2: most-specific
    # wins). A resolved primary_name already owns the name axis → the password-name
    # does NOT add (no double-count).
    if "name" not in by_axis and not (profile.get("primary_name") or "").strip():
        nm = next((c.get("value") for c in cand if c.get("attribute") == "candidate_name"), None)
        if nm:
            np_, _lbl = _name_prevalence(nm, priors)
            by_axis["name"] = {"value": nm, "p": round(np_, 6), "bits": round(_bits(np_), 2),
                               "coarse": True, "source": "password_composition"}
            if "name" in axes_unknown:
                axes_unknown.remove("name")

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
