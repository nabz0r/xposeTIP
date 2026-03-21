import hashlib
import json
import math
from datetime import datetime, timezone


class FingerprintEngine:
    """
    Generates a unique digital fingerprint from target findings.
    8-axis radar polygon: accounts, platforms, username_reuse, breaches,
    geo_spread, data_leaked, email_age, security.
    """

    AXIS_ORDER = [
        "accounts", "platforms", "username_reuse", "breaches",
        "geo_spread", "data_leaked", "email_age", "security",
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
    }

    SCORE_WEIGHTS = {
        "accounts": 0.10,
        "platforms": 0.08,
        "username_reuse": 0.15,
        "breaches": 0.25,
        "geo_spread": 0.05,
        "data_leaked": 0.20,
        "email_age": 0.05,
        "security": 0.12,
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
    }

    def compute(self, findings: list, identities: list, profile_data: dict = None, email: str = "") -> dict:
        raw = self._extract_raw_values(findings, identities, profile_data)
        axes = self._normalize(raw)
        score = self._compute_score(axes)
        color, fill, risk = self._color_from_score(score)
        points = self._axes_to_polygon(axes, center=(340, 320), radius=180)
        scars = self._detect_scars(axes, raw)
        fp_hash = self._compute_hash(axes, raw, email)
        label = self._semantic_label(axes)

        return {
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
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _extract_raw_values(self, findings, identities, profile_data):
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

        # Username reuse from identities
        usernames = {}
        for i in identities:
            if getattr(i, "type", "") == "username":
                val = getattr(i, "value", "")
                plat = getattr(i, "platform", "unknown") or "unknown"
                usernames.setdefault(val.lower(), set()).add(plat)
        reused = sum(1 for _u, p in usernames.items() if len(p) > 1)

        # Breaches
        breaches = 0
        for f in findings:
            cat = getattr(f, "category", "") or ""
            title = getattr(f, "title", "") or ""
            if cat == "breach" and "not configured" not in title.lower():
                breaches += 1

        # Geo spread
        countries = set()
        for f in findings:
            data = f.data if isinstance(f.data, dict) else {}
            if "country" in data:
                countries.add(str(data["country"]))
            if "countryCode" in data:
                countries.add(str(data["countryCode"]))

        # Data types leaked
        data_types = set()
        for f in findings:
            data = f.data if isinstance(f.data, dict) else {}
            if "data_classes" in data:
                data_types.update(data["data_classes"])
            if "DataClasses" in data:
                data_types.update(data["DataClasses"])

        # Email age
        email_age = 0
        for f in findings:
            data = f.data if isinstance(f.data, dict) else {}
            if "first_seen" in data:
                try:
                    first = datetime.strptime(str(data["first_seen"]), "%m/%d/%Y")
                    email_age = max(email_age, (datetime.now() - first).days / 365)
                except (ValueError, TypeError):
                    pass
            if "details" in data and isinstance(data["details"], dict):
                fs = data["details"].get("first_seen")
                if fs:
                    try:
                        first = datetime.strptime(str(fs), "%m/%d/%Y")
                        email_age = max(email_age, (datetime.now() - first).days / 365)
                    except (ValueError, TypeError):
                        pass

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

        return {
            "accounts": len(accounts),
            "platforms": len(platforms),
            "username_reuse": reused,
            "breaches": breaches,
            "geo_spread": len(countries),
            "data_leaked": len(data_types),
            "email_age_years": round(email_age, 1),
            "security_weak": security_issues,
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
        points = []
        for i, axis in enumerate(self.AXIS_ORDER):
            angle = (2 * math.pi * i / 8) - (math.pi / 2)
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

        return scars

    def _compute_hash(self, axes, raw, email=""):
        data = json.dumps({
            "email": email,
            "axes": {k: round(v, 1) for k, v in sorted(axes.items())},
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:8]

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
        for i, axis in enumerate(self.AXIS_ORDER):
            angle = (2 * math.pi * i / 8) - (math.pi / 2)
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
