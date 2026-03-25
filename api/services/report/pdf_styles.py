"""PDF report style constants — dark theme matching xposeTIP UI."""

from reportlab.lib.colors import HexColor

COLORS = {
    "bg_dark": HexColor("#0F1923"),
    "bg_card": HexColor("#1A2332"),
    "bg_header": HexColor("#141E2B"),
    "text_primary": HexColor("#E8EAED"),
    "text_secondary": HexColor("#8B95A5"),
    "text_muted": HexColor("#5A6577"),
    "accent_cyan": HexColor("#00D4AA"),
    "accent_orange": HexColor("#F59E0B"),
    "accent_red": HexColor("#EF4444"),
    "accent_green": HexColor("#10B981"),
    "score_bar_bg": HexColor("#2A3444"),
    "border": HexColor("#2A3444"),
    "white": HexColor("#FFFFFF"),
}

VERSION = "v0.74.0"

# Page layout (A4)
PAGE_MARGIN = 15  # mm
SECTION_GAP = 8   # mm


def axis_level(normalized_value: float) -> tuple[str, HexColor]:
    """Map a 0.0-1.0 normalized fingerprint axis to level label + color."""
    if normalized_value >= 0.8:
        return "HIGH", COLORS["accent_red"]
    if normalized_value >= 0.4:
        return "MOD", COLORS["accent_orange"]
    if normalized_value > 0:
        return "LOW", COLORS["accent_green"]
    return "NONE", COLORS["text_muted"]


def score_severity(score: int | None) -> tuple[str, HexColor]:
    """Map an exposure/threat score (0-100) to label + color."""
    if score is None:
        return "Unknown", COLORS["text_muted"]
    if score >= 80:
        return "Critical", COLORS["accent_red"]
    if score >= 60:
        return "High", COLORS["accent_orange"]
    if score >= 40:
        return "Moderate", COLORS["accent_orange"]
    if score >= 20:
        return "Low", COLORS["accent_green"]
    return "Minimal", COLORS["accent_green"]
