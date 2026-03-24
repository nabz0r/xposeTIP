import hashlib
import json
import math
import random
import re
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Timestamp harvesting helpers (used by _extract_raw_values for email_age +
# life timeline generation)
# ---------------------------------------------------------------------------

_TIMESTAMP_FIELDS = [
    "BreachDate", "breach_date", "date", "AddedDate", "added_date",
    "created_at", "createdAt", "created", "creation_date",
    "ModifiedDate", "modified_date", "updated_at",
    "first_seen", "last_seen", "registered", "registration_date",
    "joined", "joined_date", "signup_date",
    "timestamp", "snapshot_date", "earliest_snapshot",
    "published_at", "pub_date",
]

# Modules whose timestamps refer to DOMAIN age, not USER account age
_DOMAIN_AGE_MODULES = {"dns_deep", "whois_lookup", "domain_analyzer", "crt_sh"}

# Caps: no email account can predate the service launch
_DOMAIN_LAUNCH_DATES = {
    "gmail.com": 2004, "googlemail.com": 2004,
    "outlook.com": 2012, "hotmail.com": 1996, "live.com": 2005,
    "yahoo.com": 1997, "protonmail.com": 2014, "proton.me": 2022,
    "icloud.com": 2011, "me.com": 2008,
    "tutanota.com": 2011, "fastmail.com": 1999,
}


def _parse_timestamp(value) -> datetime | None:
    """Parse a timestamp from various formats found in OSINT findings."""
    if value is None:
        return None

    # Already a datetime
    if isinstance(value, datetime):
        return value

    # Numeric — unix epoch (seconds or milliseconds)
    if isinstance(value, (int, float)):
        try:
            if value > 1e12:
                return datetime.fromtimestamp(value / 1000)
            if value > 1e8:
                return datetime.fromtimestamp(value)
        except (OSError, ValueError):
            pass
        return None

    if not isinstance(value, str):
        return None

    s = value.strip()
    if not s:
        return None

    # Wayback Machine 14-digit format: 20150301120000
    if re.match(r"^\d{14}$", s):
        try:
            return datetime.strptime(s, "%Y%m%d%H%M%S")
        except ValueError:
            pass

    # ISO-ish formats
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue

    # Partial date: just a year like "2014" or "2014-06"
    m = re.match(r"^(\d{4})(?:-(\d{1,2}))?$", s)
    if m:
        year = int(m.group(1))
        month = int(m.group(2)) if m.group(2) else 1
        if 1990 <= year <= 2100 and 1 <= month <= 12:
            return datetime(year, month, 1)

    return None


def _classify_event(field: str, source: str, title: str) -> str:
    """Classify a timeline event by type based on field name and source."""
    field_l = field.lower()
    source_l = source.lower()
    title_l = title.lower()

    if "breach" in field_l or "breach" in source_l or "breach" in title_l:
        return "breach"
    if field_l in ("created_at", "createdAt", "created", "creation_date",
                   "registered", "registration_date", "joined", "joined_date",
                   "signup_date"):
        return "account_created"
    if "snapshot" in field_l or "wayback" in source_l or "archive" in source_l:
        return "archive"
    if field_l in ("first_seen",):
        return "first_seen"
    return "activity"


def _event_label(field: str, source: str, title: str, data: dict) -> str:
    """Generate a human-readable label for a timeline event."""
    platform = data.get("platform", data.get("network", data.get("service", "")))
    breach_name = data.get("Name", data.get("name", data.get("breach_name", "")))

    etype = _classify_event(field, source, title)

    if etype == "breach" and breach_name:
        return f"Exposed in {breach_name} breach"
    if etype == "account_created" and platform:
        return f"Account created on {platform}"
    if etype == "archive":
        return f"Archived by {source or 'Wayback Machine'}"
    if etype == "first_seen" and platform:
        return f"First seen on {platform}"
    if platform:
        return f"Activity on {platform}"
    if title:
        return title
    return f"{source}: {field}"


class FingerprintEngine:
    """
    Generates a unique digital fingerprint from target findings.
    9-axis radar polygon: accounts, platforms, username_reuse, breaches,
    geo_spread, data_leaked, email_age, security, public_exposure.
    """

    AXIS_ORDER = [
        "accounts", "platforms", "username_reuse", "breaches",
        "geo_spread", "data_leaked", "email_age", "security",
        "public_exposure",
    ]

    AXIS_MAX = {
        "accounts": 15,
        "platforms": 10,
        "username_reuse": 5,
        "breaches": 5,
        "geo_spread": 5,
        "data_leaked": 8,
        "email_age_years": 15,
        "security_weak": 4,
        "public_exposure_raw": 1.0,  # Already 0-1 from compute_public_exposure_score
    }

    SCORE_WEIGHTS = {
        "accounts": 0.09,
        "platforms": 0.07,
        "username_reuse": 0.13,
        "breaches": 0.22,
        "geo_spread": 0.05,
        "data_leaked": 0.18,
        "email_age": 0.04,
        "security": 0.10,
        "public_exposure": 0.12,
    }

    SEMANTIC_LABELS = {
        ("high_accounts", "high_breaches"): "Sprawling digital presence at risk",
        ("high_security", "low_breaches"): "Weak perimeter, not yet exploited",
        ("high_username_reuse",): "Predictable pattern across platforms",
        ("high_email_age", "high_data_leaked"): "Long-term exposure veteran",
        ("high_breaches", "high_data_leaked"): "Breach-heavy profile",
        ("high_accounts", "high_platforms"): "Account sprawl across platforms",
        ("high_accounts", "high_geo_spread"): "Global digital footprint",
        ("high_security", "high_breaches"): "Compromised and still vulnerable",
        ("high_data_leaked", "high_username_reuse"): "Highly targetable identity",
        ("high_public_exposure", "high_breaches"): "High-profile breach victim",
        ("high_public_exposure", "high_accounts"): "Publicly visible digital presence",
    }

    @staticmethod
    def compute_public_exposure_score(findings: list) -> tuple[float, dict]:
        """Compute public_exposure axis from media, sanctions, and corporate findings.

        Returns (score 0.0-1.0, breakdown dict with sub-scores).
        """
        media_findings = []
        sanctions_findings = []
        pep_findings = []
        corporate_findings = []

        for f in findings:
            cat = getattr(f, "category", "") or ""
            ind = getattr(f, "indicator_type", "") or ""
            if cat == "public_exposure" or ind == "media_mention":
                media_findings.append(f)
            elif cat == "compliance" or ind in ("sanctions_match", "pep_match"):
                if ind == "pep_match":
                    pep_findings.append(f)
                else:
                    sanctions_findings.append(f)
            elif cat == "corporate" or ind == "corporate_officer":
                corporate_findings.append(f)

        # --- Media component: 0.0 to 0.35 ---
        media_score = 0.0
        if media_findings:
            count = len(media_findings)
            # Log-scale: 1 article=0.10, 3=0.20, 8=0.28, 15+=0.35
            media_score = min(0.35, 0.10 * math.log2(count + 1))
            # Diversity bonus: 3+ unique sources
            sources = set()
            for f in media_findings:
                data = f.data if isinstance(f.data, dict) else {}
                src = data.get("source_name") or data.get("source", {}).get("name", "") if isinstance(data.get("source"), dict) else data.get("source_name", "")
                if src:
                    sources.add(src.lower())
            if len(sources) >= 3:
                media_score = min(0.35, media_score + 0.05)

        # --- Sanctions component: 0.0 to 0.35 ---
        sanctions_score = 0.0
        if sanctions_findings or pep_findings:
            if sanctions_findings:
                # Average confidence of sanctions findings
                confs = [f.confidence for f in sanctions_findings if f.confidence is not None]
                avg_conf = sum(confs) / len(confs) if confs else 0.7
                # Check if any Interpol
                has_interpol = any(
                    "interpol" in (getattr(f, "title", "") or "").lower()
                    for f in sanctions_findings
                )
                if has_interpol:
                    sanctions_score = min(0.35, 0.35 * avg_conf)
                else:
                    sanctions_score = min(0.30, 0.30 * avg_conf)
            if pep_findings:
                confs = [f.confidence for f in pep_findings if f.confidence is not None]
                avg_conf = sum(confs) / len(confs) if confs else 0.7
                pep_score = min(0.18, 0.18 * avg_conf)
                sanctions_score = max(sanctions_score, pep_score)

        # --- Corporate component: 0.0 to 0.30 ---
        corporate_score = 0.0
        if corporate_findings:
            active_count = 0
            inactive_count = 0
            has_identity_confirmed = False
            for f in corporate_findings:
                data = f.data if isinstance(f.data, dict) else {}
                status = (data.get("status") or data.get("company_status") or "active").lower()
                if "inactive" in status or "dissolved" in status or "struck" in status:
                    inactive_count += 1
                else:
                    active_count += 1
                if data.get("match_type") == "confirmed":
                    has_identity_confirmed = True
            # Active roles worth 1.0, inactive worth 0.3
            weighted = active_count * 1.0 + inactive_count * 0.3
            # Scale: 1 role=0.08, 3=0.15, 5+=0.25, 8+=0.30
            corporate_score = min(0.27, 0.08 * math.log2(weighted + 1))
            if has_identity_confirmed:
                corporate_score = min(0.30, corporate_score + 0.03)

        total = round(min(1.0, media_score + sanctions_score + corporate_score), 3)
        breakdown = {
            "media": round(media_score, 3),
            "sanctions": round(sanctions_score, 3),
            "corporate": round(corporate_score, 3),
            "media_count": len(media_findings),
            "sanctions_count": len(sanctions_findings),
            "pep_count": len(pep_findings),
            "corporate_count": len(corporate_findings),
        }
        return total, breakdown

    def compute(self, findings: list, identities: list, profile_data: dict = None, email: str = "", links=None, graph_context=None, country_code: str = None) -> dict:
        raw = self._extract_raw_values(findings, identities, profile_data, email=email, country_code=country_code)

        # Compute 9th axis: public_exposure
        pe_score, pe_breakdown = self.compute_public_exposure_score(findings)
        raw["public_exposure_raw"] = pe_score

        axes = self._normalize(raw)
        score = self._compute_score(axes)
        color, fill, risk = self._color_from_score(score)
        n_axes = len(self.AXIS_ORDER)
        points = self._axes_to_polygon(axes, center=(340, 320), radius=180)
        scars = self._detect_scars(axes, raw)

        # Graph eigenvalues for topology signature
        eigen = self._compute_graph_signature(identities, links or [])

        # Enhanced hash: includes both axes AND graph topology
        fp_hash = self._compute_enhanced_hash(axes, raw, email, eigen)
        label = self._semantic_label(axes)

        # Avatar seed from eigenvalues + axes
        avatar_seed = self._compute_avatar_seed(axes, eigen, email)

        result = {
            "axes": axes,
            "points": points,
            "color": color,
            "fill_color": fill,
            "risk_level": risk,
            "hash": fp_hash,
            "score": score,
            "scars": scars,
            "label": label,
            "raw_values": raw,
            "eigenvalues": eigen,
            "avatar_seed": avatar_seed,
            "timeline_events": raw.pop("timeline_events", []),
            "public_exposure_breakdown": pe_breakdown,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

        # Graph intelligence metrics (when graph_context is available)
        if graph_context:
            clusters = graph_context.get("clusters", [])
            ns = graph_context.get("node_scores", {})
            if clusters:
                avg_cluster_conf = sum(c["confidence"] for c in clusters) / len(clusters)
            else:
                avg_cluster_conf = 0
            result["graph_intelligence"] = {
                "cluster_count": len(clusters),
                "avg_cluster_confidence": round(avg_cluster_conf, 4),
                "max_cluster_density": round(max((c["density"] for c in clusters), default=0), 4),
                "total_nodes": len(ns),
                "total_edges": graph_context.get("edge_count", 0),
                "avg_node_confidence": round(sum(ns.values()) / len(ns), 4) if ns else 0,
            }

        return result

    def _extract_raw_values(self, findings, identities, profile_data, email="", country_code=None):
        accounts = set()
        platforms = set()
        for f in findings:
            data = f.data if isinstance(f.data, dict) else {}
            cat = getattr(f, "category", "") or ""
            title = getattr(f, "title", "") or ""
            if cat in ("social_account", "social"):
                platform = data.get("platform", data.get("network", data.get("service", "")))
                if platform:
                    platforms.add(platform.lower())
                    accounts.add(f"{platform.lower()}:{data.get('username', title)}")
                else:
                    accounts.add(title.lower())

        # Username reuse — computed from findings (each finding has username + platform pair)
        # The identities table has a unique constraint (workspace, target, type, value)
        # so username "stheis" can only store ONE platform. Findings have all of them.
        usernames = {}
        for f in findings:
            fdata = f.data if isinstance(f.data, dict) else {}
            cat = getattr(f, "category", "") or ""

            # Extract username from finding data
            username = (
                fdata.get("username") or
                fdata.get("handle") or
                fdata.get("login") or
                ""
            ).strip().lower()

            # Also check extracted dict
            if not username:
                extracted = fdata.get("extracted")
                if isinstance(extracted, dict):
                    username = (
                        extracted.get("username") or
                        extracted.get("handle") or
                        ""
                    ).strip().lower()

            # Fall back to indicator_value for username-type indicators
            if not username and getattr(f, "indicator_type", "") == "username":
                username = (getattr(f, "indicator_value", "") or "").strip().lower()

            if not username or len(username) < 2:
                continue

            # Skip non-social categories
            if cat not in ("social_account", "social"):
                continue

            # Extract platform
            platform = (
                fdata.get("platform") or
                fdata.get("name") or  # holehe
                fdata.get("network") or
                fdata.get("service") or
                ""
            ).strip().lower()

            if not platform or platform in ("scraper_engine", "unknown"):
                continue

            # Clean platform name
            platform = platform.replace("_profile", "").replace("_scraper", "").replace("_search", "").strip()

            if platform:
                usernames.setdefault(username, set()).add(platform)

        # Fallback: also check identities (for backward compat)
        for i in identities:
            if getattr(i, "type", "") == "username":
                val = (getattr(i, "value", "") or "").strip().lower()
                plat = (getattr(i, "platform", "") or "").strip().lower()
                if val and plat and plat not in ("unknown", "scraper_engine", "graph_builder"):
                    usernames.setdefault(val, set()).add(plat)

        reused = sum(1 for _u, p in usernames.items() if len(p) > 1)

        # Breaches
        breaches = 0
        for f in findings:
            cat = getattr(f, "category", "") or ""
            title = getattr(f, "title", "") or ""
            if cat == "breach" and "not configured" not in title.lower():
                breaches += 1

        # Geo spread — prioritize self-reported locations over server locations
        countries_user = set()    # From profiles, scrapers — HIGH value
        countries_server = set()  # From geoip — LOW value
        for f in findings:
            data = f.data if isinstance(f.data, dict) else {}
            source = getattr(f, "module", "") or ""

            country = data.get("country") or data.get("countryCode") or ""
            if not country:
                extracted = data.get("extracted")
                if isinstance(extracted, dict):
                    country = extracted.get("country") or extracted.get("location") or ""

            if country and isinstance(country, str) and len(country.strip()) >= 2:
                # Skip URLs and XML
                if country.startswith("http") or country.startswith("<"):
                    continue

                if source in ("geoip", "maxmind_geo"):
                    countries_server.add(country.strip().lower())
                else:
                    countries_user.add(country.strip().lower())

        # Ground truth: operator-set country_code boosts matching locations
        # Matching countries get weight 1.0, GeoIP mismatches get weight 0.2
        if country_code:
            gt = country_code.strip().lower()
            matching_user = sum(1 for c in countries_user if c == gt)
            other_user = len(countries_user) - matching_user
            matching_server = sum(1 for c in countries_server if c == gt)
            other_server = len(countries_server) - matching_server
            # Ground truth country always counts as 1 even if not in findings
            gt_base = 1.0 if gt not in countries_user else 0
            geo_spread_value = gt_base + matching_user * 1.0 + other_user * 0.5 + matching_server * 0.25 + other_server * 0.05
        else:
            # User-reported countries worth 1 each, server countries worth 0.25
            geo_spread_value = len(countries_user) + len(countries_server) * 0.25

        # Data types leaked
        data_types = set()
        for f in findings:
            data = f.data if isinstance(f.data, dict) else {}
            if "data_classes" in data:
                data_types.update(data["data_classes"])
            if "DataClasses" in data:
                data_types.update(data["DataClasses"])

            # Parse LeakCheck-style breach findings
            # extracted.sources is a Python repr string: "[{'name': 'X', 'date': 'Y'}]"
            extracted = data.get("extracted")
            if isinstance(extracted, dict):
                sources_str = extracted.get("sources", "")
                if isinstance(sources_str, str) and sources_str.startswith("["):
                    try:
                        import ast
                        sources_list = ast.literal_eval(sources_str)
                        if isinstance(sources_list, list):
                            for src in sources_list:
                                if isinstance(src, dict) and src.get("name"):
                                    data_types.add(f"breach:{src['name']}")
                    except (ValueError, SyntaxError):
                        pass

            # Holehe: confirmed registration = email exposed on that platform
            if getattr(f, "module", "") == "holehe" and data.get("exists") is True:
                platform_name = data.get("name", "")
                if platform_name:
                    data_types.add(f"email_registered:{platform_name}")

        # Email age — infer from ALL timestamps in findings
        email_age = 0
        timeline_events = []
        now = datetime.now()

        for f in findings:
            data = f.data if isinstance(f.data, dict) else {}
            source = getattr(f, "module", "") or ""
            title = getattr(f, "title", "") or ""

            # Skip domain-related modules — their dates are domain registration, not user activity
            if source in _DOMAIN_AGE_MODULES:
                continue

            # Skip findings about the DOMAIN, not the USER (e.g. "Domain reputation: ...")
            title_lower = title.lower()
            if "domain reputation" in title_lower or "domain age" in title_lower or "domain registr" in title_lower:
                continue

            for field in _TIMESTAMP_FIELDS:
                if field in data:
                    dt = _parse_timestamp(data[field])
                    if dt and dt < now and dt.year >= 1990:
                        age = (now - dt).days / 365.25
                        email_age = max(email_age, age)
                        timeline_events.append({
                            "date": dt.isoformat(),
                            "type": _classify_event(field, source, title),
                            "source": source,
                            "label": _event_label(field, source, title, data),
                        })

                if "details" in data and isinstance(data["details"], dict):
                    if field in data["details"]:
                        dt = _parse_timestamp(data["details"][field])
                        if dt and dt < now and dt.year >= 1990:
                            age = (now - dt).days / 365.25
                            email_age = max(email_age, age)
                            timeline_events.append({
                                "date": dt.isoformat(),
                                "type": _classify_event(field, source, title),
                                "source": source,
                                "label": _event_label(field, source, title, data),
                            })

            # Fallback: extract dates from finding TITLES
            # e.g. "Found in Dailymotion breach (2019-10-20)"
            title_dates = re.findall(r'(\d{4}-\d{2}-\d{2})', title)
            for td in title_dates:
                dt = _parse_timestamp(td)
                if dt and dt < now and dt.year >= 1990:
                    age = (now - dt).days / 365.25
                    email_age = max(email_age, age)
                    timeline_events.append({
                        "date": dt.isoformat(),
                        "type": "breach" if "breach" in title.lower() else "activity",
                        "source": source,
                        "label": title[:60],
                    })

            # Fallback: year-only from titles: "Found in X breach (2019)"
            if not title_dates:
                year_matches = re.findall(r'\b(20[0-2]\d)\b', title)
                for ym in year_matches:
                    dt = _parse_timestamp(ym)
                    if dt and dt < now:
                        age = (now - dt).days / 365.25
                        email_age = max(email_age, age)
                        timeline_events.append({
                            "date": dt.isoformat(),
                            "type": "breach" if "breach" in title.lower() else "activity",
                            "source": source,
                            "label": title[:60],
                        })

            # Check 'extracted' field (IntelX, scraper results) for timestamps
            extracted = data.get("extracted")
            if isinstance(extracted, dict):
                for ek, ev in extracted.items():
                    if isinstance(ev, str):
                        dt = _parse_timestamp(ev)
                        if dt and dt < now and dt.year >= 1990:
                            age = (now - dt).days / 365.25
                            email_age = max(email_age, age)
                            timeline_events.append({
                                "date": dt.isoformat(),
                                "type": "activity",
                                "source": source,
                                "label": f"Data from {source}: {ek}",
                            })

                # Parse LeakCheck-style sources for breach dates
                # sources is a Python repr string: "[{'name': 'X', 'date': '2024-08'}]"
                sources_str = extracted.get("sources", "")
                if isinstance(sources_str, str) and sources_str.startswith("["):
                    try:
                        import ast
                        sources_list = ast.literal_eval(sources_str)
                        if isinstance(sources_list, list):
                            for src in sources_list:
                                if isinstance(src, dict) and src.get("date"):
                                    dt = _parse_timestamp(src["date"])
                                    if dt and dt < now and dt.year >= 1990:
                                        age = (now - dt).days / 365.25
                                        email_age = max(email_age, age)
                                        breach_name = src.get("name", "Unknown")
                                        timeline_events.append({
                                            "date": dt.isoformat(),
                                            "type": "breach",
                                            "source": source,
                                            "label": f"Exposed in {breach_name} breach",
                                        })
                    except (ValueError, SyntaxError):
                        pass

        # Cap email_age by domain launch date (no Gmail account before 2004, etc.)
        domain = email.split("@")[-1].lower() if "@" in email else ""
        if domain in _DOMAIN_LAUNCH_DATES:
            max_age = now.year - _DOMAIN_LAUNCH_DATES[domain]
            email_age = min(email_age, max_age)
        # Global sanity cap: no email account is older than 30 years
        email_age = min(email_age, 30)

        # Security posture weaknesses
        security_issues = 0
        for f in findings:
            title = (getattr(f, "title", "") or "").lower()
            if "no spf" in title or "spf: not" in title or "spf not found" in title:
                security_issues += 1
            if "no dmarc" in title or "dmarc: not" in title or "dmarc not found" in title:
                security_issues += 1
            if "no dkim" in title or "dkim: not" in title:
                security_issues += 1
            if "spoofable" in title:
                security_issues += 1
            if "security: weak" in title:
                security_issues += 2

        # Deduplicate and sort timeline events
        seen_events = set()
        unique_events = []
        for ev in sorted(timeline_events, key=lambda e: e["date"]):
            key = (ev["date"][:10], ev["type"], ev["source"])
            if key not in seen_events:
                seen_events.add(key)
                unique_events.append(ev)

        return {
            "accounts": len(accounts),
            "platforms": len(platforms),
            "username_reuse": reused,
            "breaches": breaches,
            "geo_spread": geo_spread_value,
            "data_leaked": len(data_types),
            "email_age_years": round(email_age, 1),
            "security_weak": security_issues,
            "timeline_events": unique_events,
        }

    def _normalize(self, raw):
        mapping = {
            "accounts": "accounts",
            "platforms": "platforms",
            "username_reuse": "username_reuse",
            "breaches": "breaches",
            "geo_spread": "geo_spread",
            "data_leaked": "data_leaked",
            "email_age_years": "email_age",
            "security_weak": "security",
            "public_exposure_raw": "public_exposure",
        }
        axes = {}
        for raw_key, axis_name in mapping.items():
            max_val = self.AXIS_MAX.get(raw_key, 10)
            axes[axis_name] = round(min(1.0, (raw.get(raw_key, 0) or 0) / max_val), 3)
        return axes

    def _compute_score(self, axes):
        score = sum(axes.get(k, 0) * w for k, w in self.SCORE_WEIGHTS.items()) * 100
        return round(min(100, score))

    def _color_from_score(self, score):
        if score <= 20:
            return "#1D9E75", "rgba(29,158,117,0.12)", "LOW"
        elif score <= 50:
            return "#EF9F27", "rgba(239,159,39,0.10)", "MODERATE"
        elif score <= 75:
            return "#D85A30", "rgba(216,90,48,0.08)", "HIGH"
        else:
            return "#E24B4A", "rgba(225,50,50,0.08)", "CRITICAL"

    def _axes_to_polygon(self, axes, center=(340, 320), radius=180):
        n = len(self.AXIS_ORDER)
        points = []
        for i, axis in enumerate(self.AXIS_ORDER):
            angle = (2 * math.pi * i / n) - (math.pi / 2)
            value = axes.get(axis, 0)
            r = radius * max(0.08, value)
            x = center[0] + r * math.cos(angle)
            y = center[1] + r * math.sin(angle)
            points.append([round(x, 1), round(y, 1)])
        return points

    def _detect_scars(self, axes, raw):
        scars = []

        if axes.get("username_reuse", 0) > 0.3 and axes.get("breaches", 0) > 0.2:
            scars.append({
                "from": 2, "to": 3,
                "type": "credential_stuffing",
                "label": "credential stuffing risk",
            })

        if axes.get("breaches", 0) > 0.2 and axes.get("data_leaked", 0) > 0.3:
            scars.append({
                "from": 3, "to": 5,
                "type": "identity_theft",
                "label": "identity theft risk",
            })

        if axes.get("security", 0) > 0.5 and axes.get("accounts", 0) > 0.3:
            scars.append({
                "from": 7, "to": 0,
                "type": "phishing",
                "label": "phishing attack surface",
            })

        if axes.get("accounts", 0) > 0.5 and axes.get("geo_spread", 0) > 0.3:
            scars.append({
                "from": 0, "to": 4,
                "type": "monitoring_gap",
                "label": "monitoring blind spots",
            })

        if axes.get("email_age", 0) > 0.5 and axes.get("breaches", 0) > 0.2:
            scars.append({
                "from": 6, "to": 3,
                "type": "chronic_exposure",
                "label": "chronic exposure",
            })

        # public_exposure is axis index 8
        if axes.get("public_exposure", 0) > 0.4 and axes.get("breaches", 0) > 0.2:
            scars.append({
                "from": 8, "to": 3,
                "type": "public_breach_victim",
                "label": "publicly known breach victim",
            })

        if axes.get("public_exposure", 0) > 0.3 and axes.get("accounts", 0) > 0.4:
            scars.append({
                "from": 8, "to": 0,
                "type": "public_figure",
                "label": "high public visibility",
            })

        return scars

    def _compute_hash(self, axes, raw, email=""):
        data = json.dumps({
            "email": email,
            "axes": {k: round(v, 1) for k, v in sorted(axes.items())},
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:8]

    def _compute_enhanced_hash(self, axes, raw, email, eigenvalues):
        """Hash that includes graph topology, not just axis values."""
        sig = "|".join([
            email.lower(),
            "|".join(f"{k}:{v:.3f}" for k, v in sorted(axes.items())),
            "|".join(f"{v:.4f}" for v in eigenvalues[:5]),
        ])
        return hashlib.sha256(sig.encode()).hexdigest()[:12]

    def _compute_graph_signature(self, identities, links):
        """Compute eigenvalue-based signature of the identity graph topology.

        Returns a sorted list of top eigenvalues that uniquely characterize
        the graph structure. Two people with different connection patterns
        will have different eigenvalues.
        """
        if not identities or len(identities) < 2:
            return []

        # Build adjacency matrix
        id_list = [i.id for i in identities if hasattr(i, 'id')]
        n = len(id_list)
        if n < 2 or n > 200:  # Safety cap
            return []

        id_to_idx = {id_: idx for idx, id_ in enumerate(id_list)}

        # Initialize matrix as list of lists (avoid numpy dependency)
        matrix = [[0.0] * n for _ in range(n)]

        id_set = set(id_list)
        relevant_links = []
        for l in links:
            src = getattr(l, 'source_id', None)
            dst = getattr(l, 'dest_id', None)
            if src in id_set and dst in id_set:
                relevant_links.append(l)

        for l in relevant_links:
            i = id_to_idx.get(l.source_id)
            j = id_to_idx.get(l.dest_id)
            if i is not None and j is not None:
                weight = getattr(l, 'confidence', 0.5) or 0.5
                matrix[i][j] = weight
                matrix[j][i] = weight  # Undirected for eigenvalues

        # Power iteration to find top eigenvalues (no numpy needed)
        eigenvalues = self._power_iteration_eigenvalues(matrix, n, k=min(5, n))

        return eigenvalues

    def _power_iteration_eigenvalues(self, matrix, n, k=5, iterations=50):
        """Simple power iteration to approximate top-k eigenvalues.
        No numpy dependency. Works for small graphs (<200 nodes).
        """
        random.seed(42)  # Deterministic

        eigenvalues = []
        # Work on a copy so deflation doesn't corrupt the original
        mat = [row[:] for row in matrix]

        for _eigen_idx in range(k):
            # Random initial vector
            v = [random.gauss(0, 1) for _ in range(n)]
            norm = math.sqrt(sum(x * x for x in v))
            v = [x / norm for x in v] if norm > 0 else v

            eigenvalue = 0.0
            for _ in range(iterations):
                # Matrix-vector multiply
                new_v = [0.0] * n
                for i in range(n):
                    for j in range(n):
                        new_v[i] += mat[i][j] * v[j]

                norm = math.sqrt(sum(x * x for x in new_v))
                if norm < 1e-10:
                    break

                eigenvalue = norm
                v = [x / norm for x in new_v]

            eigenvalues.append(round(eigenvalue, 4))

            # Deflate matrix for next eigenvalue
            for i in range(n):
                for j in range(n):
                    mat[i][j] -= eigenvalue * v[i] * v[j]

        return sorted(eigenvalues, reverse=True)

    def _compute_avatar_seed(self, axes, eigenvalues, email):
        """Compute a deterministic seed for avatar generation.
        Returns a dict of parameters that feed the SVG generator.
        """
        # Use eigenvalues to determine shape complexity
        complexity = len([e for e in eigenvalues if e > 0.1])

        # Use axes to determine color hue and saturation
        # High threat = warm colors, high exposure = saturated
        threat_axes = axes.get("breaches", 0) + axes.get("data_leaked", 0)
        exposure_axes = axes.get("accounts", 0) + axes.get("platforms", 0)

        # Hash email for deterministic but unique base
        email_hash = int(hashlib.md5(email.lower().encode()).hexdigest()[:8], 16)

        # Generate shape parameters
        num_points = max(3, min(12, complexity + 3))
        rotation = (email_hash % 360)
        inner_radius = 0.3 + (axes.get("security", 0) * 0.3)

        # Color from graph density
        hue = (email_hash % 60) + 120  # Green-cyan range (identity = cool)
        if threat_axes > 0.5:
            hue = (email_hash % 60) + 0  # Red-orange range (threatened)
        elif exposure_axes > 0.6:
            hue = (email_hash % 60) + 200  # Blue-purple range (exposed)

        saturation = 40 + int(min(1.0, len(eigenvalues) / 5) * 40)
        lightness = 45 + int(axes.get("accounts", 0) * 20)

        return {
            "num_points": num_points,
            "rotation": rotation,
            "inner_radius": round(inner_radius, 3),
            "hue": hue,
            "saturation": saturation,
            "lightness": lightness,
            "eigenvalues": eigenvalues[:5],
            "complexity": complexity,
            "email_hash": email_hash % 10000,
        }

    def _semantic_label(self, axes):
        traits = set()
        for axis, val in axes.items():
            if val >= 0.6:
                traits.add(f"high_{axis}")
            elif val <= 0.15:
                traits.add(f"low_{axis}")

        if all(v <= 0.15 for v in axes.values()):
            return "Digital ghost — minimal exposure"

        if all(v >= 0.5 for v in axes.values()):
            return "Maximum exposure across all axes"

        for keys, label in self.SEMANTIC_LABELS.items():
            if all(k in traits for k in keys):
                return label

        # Fallback based on dominant axis
        dominant = max(axes, key=axes.get)
        dominant_labels = {
            "accounts": "Wide digital footprint",
            "platforms": "Spread across many platforms",
            "username_reuse": "Predictable identity pattern",
            "breaches": "Breach-exposed profile",
            "geo_spread": "Globally distributed presence",
            "data_leaked": "Significant data exposure",
            "email_age": "Long-established digital identity",
            "security": "Weak security perimeter",
            "public_exposure": "Publicly exposed identity",
        }
        return dominant_labels.get(dominant, "Identity mapped")

    def to_standalone_svg(self, fingerprint: dict, email: str = "", width: int = 680, height: int = 680) -> str:
        """Generate a standalone SVG string for export/PDF embedding."""
        axes = fingerprint["axes"]
        color = fingerprint["color"]
        fill = fingerprint["fill_color"]
        points = fingerprint["points"]
        fp_hash = fingerprint["hash"]
        score = fingerprint["score"]
        risk = fingerprint["risk_level"]
        cx, cy, radius = 340, 320, 180

        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
            f'<rect width="{width}" height="{height}" fill="#0a0a0f" rx="16"/>',
        ]

        # Grid circles
        for pct in [0.25, 0.5, 0.75, 1.0]:
            r = radius * pct
            lines.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.0f}" fill="none" stroke="#1e1e2e" stroke-width="1"/>')

        # Axis lines + labels
        n_axes = len(self.AXIS_ORDER)
        for i, axis in enumerate(self.AXIS_ORDER):
            angle = (2 * math.pi * i / n_axes) - (math.pi / 2)
            ex = cx + radius * math.cos(angle)
            ey = cy + radius * math.sin(angle)
            lines.append(f'<line x1="{cx}" y1="{cy}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="#1e1e2e" stroke-width="1"/>')
            lx = cx + (radius + 24) * math.cos(angle)
            ly = cy + (radius + 24) * math.sin(angle)
            anchor = "middle"
            if lx < cx - 10:
                anchor = "end"
            elif lx > cx + 10:
                anchor = "start"
            val = axes.get(axis, 0)
            lines.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#888" font-size="11" '
                f'font-family="Inter,sans-serif" text-anchor="{anchor}" dominant-baseline="middle">'
                f'{axis.replace("_", " ")}</text>'
            )

        # Polygon
        pts_str = " ".join(f"{p[0]},{p[1]}" for p in points)
        lines.append(f'<polygon points="{pts_str}" fill="{fill}" stroke="{color}" stroke-width="2"/>')

        # Vertex dots
        for p in points:
            lines.append(f'<circle cx="{p[0]}" cy="{p[1]}" r="4" fill="{color}"/>')

        # Center dot
        lines.append(f'<circle cx="{cx}" cy="{cy}" r="3" fill="{color}" opacity="0.6"/>')

        # Scars
        for scar in fingerprint.get("scars", []):
            fi, ti = scar["from"], scar["to"]
            if fi < len(points) and ti < len(points):
                fp, tp = points[fi], points[ti]
                lines.append(
                    f'<line x1="{fp[0]}" y1="{fp[1]}" x2="{tp[0]}" y2="{tp[1]}" '
                    f'stroke="{color}" stroke-width="1.5" stroke-dasharray="6,4" opacity="0.5"/>'
                )

        # Footer text
        lines.append(
            f'<text x="{cx}" y="{cy + radius + 55}" fill="{color}" font-size="13" '
            f'font-family="JetBrains Mono,monospace" text-anchor="middle">'
            f'fingerprint: {fp_hash}</text>'
        )
        lines.append(
            f'<text x="{cx}" y="{cy + radius + 75}" fill="#666" font-size="11" '
            f'font-family="Inter,sans-serif" text-anchor="middle">'
            f'{email} · score {score} · {risk}</text>'
        )

        lines.append('</svg>')
        return "\n".join(lines)
