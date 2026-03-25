"""PDF Identity Report Generator — dark-themed, branded, multi-tier."""

import io
import uuid
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
)
from reportlab.graphics.shapes import Drawing, Rect

from api.services.report.pdf_styles import COLORS, VERSION, axis_level, score_severity
from api.services.report.pdf_remediation import generate_remediation

W, H = A4  # 595.27 x 841.89 points


# ---------------------------------------------------------------------------
# Paragraph styles
# ---------------------------------------------------------------------------

def _styles():
    """Build reusable paragraph styles."""
    return {
        "title": ParagraphStyle(
            "title", fontName="Helvetica-Bold", fontSize=22,
            textColor=COLORS["text_primary"], leading=28,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName="Helvetica", fontSize=11,
            textColor=COLORS["text_secondary"], leading=15,
        ),
        "h2": ParagraphStyle(
            "h2", fontName="Helvetica-Bold", fontSize=14,
            textColor=COLORS["accent_cyan"], leading=20, spaceBefore=6,
        ),
        "h3": ParagraphStyle(
            "h3", fontName="Helvetica-Bold", fontSize=11,
            textColor=COLORS["text_primary"], leading=16, spaceBefore=4,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=9,
            textColor=COLORS["text_primary"], leading=13,
        ),
        "body_secondary": ParagraphStyle(
            "body_secondary", fontName="Helvetica", fontSize=9,
            textColor=COLORS["text_secondary"], leading=13,
        ),
        "small": ParagraphStyle(
            "small", fontName="Helvetica", fontSize=8,
            textColor=COLORS["text_muted"], leading=11,
        ),
        "bullet_high": ParagraphStyle(
            "bullet_high", fontName="Helvetica", fontSize=9,
            textColor=COLORS["accent_red"], leading=13, leftIndent=12,
        ),
        "bullet_medium": ParagraphStyle(
            "bullet_medium", fontName="Helvetica", fontSize=9,
            textColor=COLORS["accent_orange"], leading=13, leftIndent=12,
        ),
        "bullet_low": ParagraphStyle(
            "bullet_low", fontName="Helvetica", fontSize=9,
            textColor=COLORS["accent_green"], leading=13, leftIndent=12,
        ),
    }


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _score_bar(value: int, max_val: int = 100, width: float = 150, color=None):
    """Horizontal bar for exposure/threat score."""
    d = Drawing(width + 10, 12)
    d.add(Rect(0, 2, width, 8, fillColor=COLORS["score_bar_bg"], strokeColor=None))
    fill_w = max(0, min(value / max_val, 1.0)) * width
    bar_color = color or COLORS["accent_cyan"]
    if fill_w > 0:
        d.add(Rect(0, 2, fill_w, 8, fillColor=bar_color, strokeColor=None))
    return d


def _axis_bar(normalized: float, width: float = 120):
    """Bar for fingerprint axis."""
    d = Drawing(width + 10, 12)
    d.add(Rect(0, 2, width, 8, fillColor=COLORS["score_bar_bg"], strokeColor=None))
    fill_w = max(0, min(normalized, 1.0)) * width
    _, color = axis_level(normalized)
    if fill_w > 0:
        d.add(Rect(0, 2, fill_w, 8, fillColor=color, strokeColor=None))
    return d


def _divider():
    """Thin horizontal divider line."""
    d = Drawing(W - 30 * mm, 2)
    d.add(Rect(0, 0, W - 30 * mm, 0.5, fillColor=COLORS["border"], strokeColor=None))
    return d


def _card_table(data, col_widths=None, style_cmds=None):
    """Build a table with dark card styling."""
    available = W - 30 * mm
    t = Table(data, colWidths=col_widths or [available])
    base_style = [
        ("BACKGROUND", (0, 0), (-1, -1), COLORS["bg_card"]),
        ("TEXTCOLOR", (0, 0), (-1, -1), COLORS["text_primary"]),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, COLORS["border"]),
    ]
    if style_cmds:
        base_style.extend(style_cmds)
    t.setStyle(TableStyle(base_style))
    return t


# ---------------------------------------------------------------------------
# Page sections
# ---------------------------------------------------------------------------

def _build_executive_summary(target, profile, tier, styles):
    """Page 1 — Executive Summary."""
    story = []

    # Header
    story.append(Paragraph("IDENTITY INTELLIGENCE REPORT", styles["title"]))
    story.append(Paragraph("CONFIDENTIAL", styles["small"]))
    story.append(Spacer(1, 6 * mm))

    # Identity card
    name = profile.get("primary_name") or target.display_name or "Unknown"
    email = target.email or ""
    country = target.country_code or ""
    confidence = (profile.get("confidence") or {}).get("overall", 0)
    conf_pct = f"{int(confidence * 100)}%" if confidence else "N/A"

    identity_data = [
        [Paragraph(f'<b>{_esc(name)}</b>', styles["h2"])],
        [Paragraph(_esc(email), styles["body"])],
    ]
    if country:
        flag = _flag_emoji(country)
        identity_data.append([Paragraph(f"{flag} {country}", styles["body"])])
    identity_data.append([
        Paragraph(f"{conf_pct} confidence", styles["body_secondary"]),
    ])
    story.append(_card_table(identity_data))
    story.append(Spacer(1, 6 * mm))

    # Scores
    exposure = target.exposure_score
    threat = target.threat_score
    exp_label, exp_color = score_severity(exposure)
    thr_label, thr_color = score_severity(threat)

    score_rows = [
        [
            Paragraph("<b>Metric</b>", styles["body"]),
            Paragraph("<b>Score</b>", styles["body"]),
            Paragraph("<b>Level</b>", styles["body"]),
            "",
        ],
        [
            Paragraph("EXPOSURE", styles["body"]),
            Paragraph(f"<b>{exposure if exposure is not None else '-'}</b>", styles["body"]),
            Paragraph(exp_label, ParagraphStyle("s", parent=styles["body"], textColor=exp_color)),
            _score_bar(exposure or 0, color=exp_color),
        ],
        [
            Paragraph("THREAT", styles["body"]),
            Paragraph(f"<b>{threat if threat is not None else '-'}</b>", styles["body"]),
            Paragraph(thr_label, ParagraphStyle("s", parent=styles["body"], textColor=thr_color)),
            _score_bar(threat or 0, color=thr_color),
        ],
    ]
    risk_level = (profile.get("fingerprint") or {}).get("risk_level", "unknown")
    score_rows.append([
        Paragraph(f"<b>Risk Level: {_esc(risk_level.upper())}</b>", styles["body"]),
        "", "", "",
    ])
    cw = [90, 50, 70, 160]
    story.append(_card_table(score_rows, col_widths=cw))
    story.append(Spacer(1, 6 * mm))

    # Key Findings
    story.append(Paragraph("KEY FINDINGS", styles["h2"]))
    story.append(Spacer(1, 2 * mm))

    findings_bullets = _key_findings_bullets(target, profile, tier)
    for bullet in findings_bullets:
        story.append(Paragraph(bullet, styles["body"]))
        story.append(Spacer(1, 1 * mm))

    story.append(Spacer(1, 6 * mm))
    story.append(_divider())
    story.append(Spacer(1, 3 * mm))

    # Report metadata
    report_id = str(uuid.uuid4())[:8]
    story.append(Paragraph(
        f"Generated by xposeTIP {VERSION} &middot; {date.today()} &middot; Report ID: {report_id}",
        styles["small"],
    ))

    if tier == "free":
        story.append(Spacer(1, 8 * mm))
        story.append(Paragraph(
            "This is a preview report. Upgrade to Pro for the full identity analysis, "
            "breach timeline, digital footprint, and remediation plan.",
            ParagraphStyle("promo", parent=styles["body"], textColor=COLORS["accent_cyan"]),
        ))

    return story


def _key_findings_bullets(target, profile, tier):
    """Generate key finding bullet lines."""
    bullets = []
    breach_summary = profile.get("breach_summary") or {}
    social_profiles = profile.get("social_profiles") or []
    usernames = profile.get("usernames") or []
    email_security = profile.get("email_security") or {}

    breach_count = breach_summary.get("count", 0)
    if breach_count > 0:
        if tier == "free":
            bullets.append(f"&#x2022; Found in {breach_count} data breaches [upgrade to see details]")
        else:
            bullets.append(f"&#x2022; Found in {breach_count} data breaches")
    else:
        bullets.append("&#x2022; No known data breaches detected")

    platform_count = len(social_profiles)
    if tier == "free":
        bullets.append(f"&#x2022; Active on {platform_count} platforms [upgrade to see list]")
    else:
        bullets.append(f"&#x2022; Active on {platform_count} platforms")

    if usernames:
        bullets.append(f"&#x2022; {len(usernames)} username variants detected")

    # Email security
    sec_parts = []
    for check in ("spf", "dkim", "dmarc"):
        val = email_security.get(check)
        if val is True:
            sec_parts.append(f"{check.upper()} &#x2713;")
        elif val is False:
            sec_parts.append(f"{check.upper()} &#x2717;")
    if sec_parts:
        bullets.append(f"&#x2022; Email security: {' '.join(sec_parts)}")

    creds = breach_summary.get("credentials_leaked", False)
    if creds:
        bullets.append("&#x2022; &#x26A0; Credentials leaked in at least one breach")
    else:
        bullets.append("&#x2022; No credentials leaked")

    return bullets


def _build_fingerprint_table(profile, styles):
    """Page 2 — Behavioral Fingerprint as table with bars."""
    story = []
    fp = profile.get("fingerprint") or {}

    story.append(Paragraph("BEHAVIORAL FINGERPRINT", styles["h2"]))
    fp_hash = fp.get("hash", "")[:12]
    if fp_hash:
        story.append(Paragraph(f"Hash: {fp_hash}", styles["small"]))
    story.append(Spacer(1, 4 * mm))

    axes = fp.get("axes") or {}
    raw_values = fp.get("raw_values") or {}

    axis_labels = [
        "accounts", "platforms", "username_reuse", "breaches",
        "geo_spread", "data_leaked", "email_age", "security", "public_exposure",
    ]
    display_names = {
        "accounts": "Accounts",
        "platforms": "Platforms",
        "username_reuse": "Username Reuse",
        "breaches": "Breaches",
        "geo_spread": "Geo Spread",
        "data_leaked": "Data Leaked",
        "email_age": "Email Age",
        "security": "Security",
        "public_exposure": "Public Exposure",
    }

    # Header row
    rows = [[
        Paragraph("<b>Axis</b>", styles["body"]),
        Paragraph("<b>Raw</b>", styles["body"]),
        Paragraph("<b>Level</b>", styles["body"]),
        "",
    ]]

    for axis_key in axis_labels:
        norm = axes.get(axis_key, 0)
        raw = raw_values.get(f"{axis_key}_raw", raw_values.get(axis_key, ""))
        level_label, level_color = axis_level(norm)

        # Format raw value
        if isinstance(raw, float):
            raw_str = f"{raw:.1f}" if raw != int(raw) else str(int(raw))
        else:
            raw_str = str(raw) if raw else "0"

        rows.append([
            Paragraph(display_names.get(axis_key, axis_key), styles["body"]),
            Paragraph(raw_str, styles["body"]),
            Paragraph(level_label, ParagraphStyle("lvl", parent=styles["body"], textColor=level_color)),
            _axis_bar(norm),
        ])

    cw = [110, 60, 50, 140]
    story.append(_card_table(rows, col_widths=cw))
    story.append(Spacer(1, 4 * mm))

    # Overall score + label
    fp_score = fp.get("score", 0)
    fp_label = fp.get("label", "")
    if fp_score or fp_label:
        story.append(Paragraph(
            f"<b>Overall: {fp_score}/100</b> — \"{_esc(fp_label)}\"",
            styles["body"],
        ))
    story.append(Spacer(1, 4 * mm))

    # Scars
    scars = fp.get("scars") or []
    if scars:
        story.append(Paragraph("VULNERABILITY PATTERNS (SCARS)", styles["h3"]))
        story.append(Spacer(1, 2 * mm))
        for scar in scars[:6]:
            label = scar if isinstance(scar, str) else scar.get("label", str(scar))
            story.append(Paragraph(f"&#x2022; {_esc(label)}", styles["body"]))
            story.append(Spacer(1, 1 * mm))

    return story


def _build_breach_timeline(profile, styles):
    """Page 3 — Breach Timeline + Email Security."""
    story = []
    fp = profile.get("fingerprint") or {}
    breach_summary = profile.get("breach_summary") or {}
    email_security = profile.get("email_security") or {}
    email_provider = profile.get("email_provider") or ""
    timeline_events = fp.get("timeline_events") or []
    life_timeline = profile.get("life_timeline") or []

    breach_count = breach_summary.get("count", 0)
    story.append(Paragraph("BREACH TIMELINE", styles["h2"]))

    # Get breach events
    breaches = [e for e in timeline_events if e.get("type") == "breach"]
    if not breaches:
        # Fallback to life_timeline
        breaches = [e for e in life_timeline if e.get("type") == "breach"]

    if breaches:
        earliest = min(
            (e.get("year") or e.get("date", "")[:4] for e in breaches if e.get("year") or e.get("date")),
            default="?",
        )
        story.append(Paragraph(
            f"{len(breaches)} breaches detected &middot; earliest: {earliest}",
            styles["body_secondary"],
        ))
        story.append(Spacer(1, 4 * mm))

        rows = [[
            Paragraph("<b>Year</b>", styles["body"]),
            Paragraph("<b>Breach</b>", styles["body"]),
        ]]
        # Sort by year descending
        sorted_breaches = sorted(
            breaches,
            key=lambda e: e.get("year") or e.get("date", "0")[:4],
            reverse=True,
        )
        for b in sorted_breaches[:15]:
            year = str(b.get("year") or b.get("date", "?")[:4])
            label = b.get("label") or b.get("title") or "Unknown breach"
            rows.append([
                Paragraph(year, styles["body"]),
                Paragraph(_esc(label), styles["body"]),
            ])

        cw = [60, W - 30 * mm - 60]
        story.append(_card_table(rows, col_widths=cw))
    else:
        story.append(Spacer(1, 2 * mm))
        if breach_count > 0:
            story.append(Paragraph(
                f"{breach_count} breaches detected (no timeline data available)",
                styles["body"],
            ))
        else:
            story.append(Paragraph("No known breaches detected.", styles["body"]))

    story.append(Spacer(1, 4 * mm))

    # Credentials
    creds = breach_summary.get("credentials_leaked", False)
    story.append(Paragraph(
        f"Credentials leaked: <b>{'YES' if creds else 'NO'}</b>",
        ParagraphStyle(
            "c", parent=styles["body"],
            textColor=COLORS["accent_red"] if creds else COLORS["accent_green"],
        ),
    ))

    # Sources
    sources = breach_summary.get("sources") or []
    if sources:
        story.append(Paragraph(
            f"Sources: {', '.join(_esc(s) for s in sources[:10])}",
            styles["small"],
        ))

    story.append(Spacer(1, 8 * mm))
    story.append(_divider())
    story.append(Spacer(1, 4 * mm))

    # Email Security
    story.append(Paragraph("EMAIL SECURITY", styles["h2"]))
    story.append(Spacer(1, 2 * mm))

    sec_rows = []
    if email_provider:
        sec_rows.append([
            Paragraph("Provider", styles["body_secondary"]),
            Paragraph(_esc(email_provider), styles["body"]),
        ])
    for check in ("spf", "dkim", "dmarc"):
        val = email_security.get(check)
        if val is True:
            symbol = "&#x2713;"
            color = COLORS["accent_green"]
        elif val is False:
            symbol = "&#x2717;"
            color = COLORS["accent_red"]
        else:
            symbol = "?"
            color = COLORS["text_muted"]
        sec_rows.append([
            Paragraph(check.upper(), styles["body_secondary"]),
            Paragraph(
                f"<b>{symbol}</b>",
                ParagraphStyle("s", parent=styles["body"], textColor=color),
            ),
        ])
    sec_level = email_security.get("security_level", "unknown")
    sec_rows.append([
        Paragraph("Security level", styles["body_secondary"]),
        Paragraph(_esc(sec_level), styles["body"]),
    ])

    if sec_rows:
        cw = [120, W - 30 * mm - 120]
        story.append(_card_table(sec_rows, col_widths=cw))

    return story


def _build_accounts_table(profile, styles):
    """Page 4 — Digital Footprint (accounts + username reuse)."""
    story = []
    social_profiles = profile.get("social_profiles") or []
    usernames = profile.get("usernames") or []

    platform_count = len(social_profiles)
    # Count unique platforms
    unique_platforms = {(sp.get("platform") or "").lower() for sp in social_profiles}

    story.append(Paragraph("DIGITAL FOOTPRINT", styles["h2"]))
    story.append(Paragraph(
        f"{platform_count} accounts across {len(unique_platforms)} platforms",
        styles["body_secondary"],
    ))
    story.append(Spacer(1, 4 * mm))

    if social_profiles:
        rows = [[
            Paragraph("<b>Platform</b>", styles["body"]),
            Paragraph("<b>Username</b>", styles["body"]),
            Paragraph("<b>Source</b>", styles["body"]),
        ]]
        shown = 0
        for sp in social_profiles:
            if shown >= 25:
                break
            platform = sp.get("platform") or "Unknown"
            username = sp.get("username") or "-"
            source = sp.get("source") or "detected"
            rows.append([
                Paragraph(_esc(platform), styles["body"]),
                Paragraph(_esc(username), styles["body"]),
                Paragraph(_esc(source), styles["body_secondary"]),
            ])
            shown += 1

        remaining = platform_count - shown
        if remaining > 0:
            rows.append([
                Paragraph(f"... and {remaining} more", styles["body_secondary"]),
                "", "",
            ])

        cw = [130, 140, W - 30 * mm - 270]
        story.append(_card_table(rows, col_widths=cw))

    story.append(Spacer(1, 6 * mm))

    # Username Reuse Analysis
    story.append(Paragraph("USERNAME REUSE ANALYSIS", styles["h3"]))
    story.append(Spacer(1, 2 * mm))

    # Group platforms by username
    uname_platforms: dict[str, list[str]] = {}
    for sp in social_profiles:
        u = sp.get("username") or ""
        p = sp.get("platform") or ""
        if u and p:
            uname_platforms.setdefault(u.lower(), {"display": u, "platforms": []})
            uname_platforms[u.lower()]["platforms"].append(p)

    reuse_rows = []
    for key in sorted(uname_platforms, key=lambda k: -len(uname_platforms[k]["platforms"])):
        entry = uname_platforms[key]
        display = entry["display"]
        platforms = entry["platforms"]
        reused_tag = " (REUSED)" if len(platforms) >= 2 else ""
        reuse_rows.append([
            Paragraph(f"<b>{_esc(display)}</b>{reused_tag}", styles["body"]),
            Paragraph(", ".join(_esc(p) for p in platforms[:8]), styles["body_secondary"]),
        ])
        if len(reuse_rows) >= 10:
            break

    if reuse_rows:
        story.append(Paragraph(
            f"{len(usernames)} usernames &middot; "
            f"{sum(1 for v in uname_platforms.values() if len(v['platforms']) >= 2)} reused across platforms",
            styles["body_secondary"],
        ))
        story.append(Spacer(1, 2 * mm))
        cw2 = [160, W - 30 * mm - 160]
        story.append(_card_table(reuse_rows, col_widths=cw2))

    return story


def _build_remediation(target, profile, styles):
    """Page 5 — Remediation actions."""
    story = []
    story.append(Paragraph("RECOMMENDED ACTIONS", styles["h2"]))
    story.append(Paragraph("Prioritized by impact", styles["body_secondary"]))
    story.append(Spacer(1, 4 * mm))

    actions = generate_remediation(profile)

    priority_styles = {
        "high": styles["bullet_high"],
        "medium": styles["bullet_medium"],
        "low": styles["bullet_low"],
    }
    priority_labels = {
        "high": "HIGH PRIORITY",
        "medium": "MEDIUM PRIORITY",
        "low": "LOW PRIORITY",
    }
    priority_colors = {
        "high": COLORS["accent_red"],
        "medium": COLORS["accent_orange"],
        "low": COLORS["accent_green"],
    }

    current_priority = None
    idx = 0
    for priority, action, detail in actions:
        if priority != current_priority:
            current_priority = priority
            story.append(Spacer(1, 3 * mm))
            story.append(Paragraph(
                f"<b>{priority_labels.get(priority, priority.upper())}</b>",
                ParagraphStyle(
                    "pl", parent=styles["body"],
                    textColor=priority_colors.get(priority, COLORS["text_primary"]),
                ),
            ))
            story.append(Spacer(1, 1 * mm))

        idx += 1
        story.append(Paragraph(
            f"{idx}. {_esc(action)}",
            priority_styles.get(priority, styles["body"]),
        ))
        if detail:
            story.append(Paragraph(
                f"&nbsp;&nbsp;&nbsp;&nbsp;{_esc(detail)}",
                styles["small"],
            ))
        story.append(Spacer(1, 1 * mm))

    # Impact estimate
    story.append(Spacer(1, 6 * mm))
    story.append(_divider())
    story.append(Spacer(1, 3 * mm))

    high_count = sum(1 for p, _, _ in actions if p == "high")
    story.append(Paragraph("ESTIMATED IMPACT", styles["h3"]))
    if high_count:
        story.append(Paragraph(
            f"Completing HIGH items: exposure -{min(high_count * 15, 50)}%",
            styles["body"],
        ))
    story.append(Paragraph(
        f"Completing ALL items: exposure -{min(len(actions) * 10, 70)}%",
        styles["body"],
    ))

    return story


# ---------------------------------------------------------------------------
# Footer / page background
# ---------------------------------------------------------------------------

def _add_page_bg(canvas, doc):
    """Draw dark background and footer on every page."""
    canvas.saveState()
    # Full page dark background
    canvas.setFillColor(COLORS["bg_dark"])
    canvas.rect(0, 0, W, H, fill=True, stroke=False)
    # Footer
    canvas.setFillColor(COLORS["text_muted"])
    canvas.setFont("Helvetica", 7)
    canvas.drawString(
        15 * mm, 7 * mm,
        f"xposeTIP {VERSION}  \u00b7  CONFIDENTIAL  \u00b7  Page {doc.page}",
    )
    canvas.drawRightString(
        W - 15 * mm, 7 * mm,
        "github.com/nabz0r/xposeTIP",
    )
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _esc(text):
    """Escape HTML entities for ReportLab Paragraph."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _flag_emoji(code: str) -> str:
    """Country code to flag emoji."""
    if not code or len(code) != 2:
        return ""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_identity_report(target, profile: dict, tier: str = "pro") -> bytes:
    """Generate a branded PDF identity report.

    Args:
        target: Target SQLAlchemy model instance
        profile: target.profile_data dict
        tier: 'free', 'pro', or 'enterprise' (from workspace plan)

    Returns:
        PDF bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    styles = _styles()
    story = []

    # Page 1 — Executive Summary (all tiers)
    story += _build_executive_summary(target, profile, tier, styles)

    if tier in ("pro", "enterprise", "consultant"):
        story.append(PageBreak())
        # Page 2 — Behavioral Fingerprint
        story += _build_fingerprint_table(profile, styles)

        story.append(PageBreak())
        # Page 3 — Breach Timeline + Email Security
        story += _build_breach_timeline(profile, styles)

        story.append(PageBreak())
        # Page 4 — Accounts & Platforms
        story += _build_accounts_table(profile, styles)

        story.append(PageBreak())
        # Page 5 — Remediation
        story += _build_remediation(target, profile, styles)

    doc.build(story, onFirstPage=_add_page_bg, onLaterPages=_add_page_bg)
    buffer.seek(0)
    return buffer.read()
