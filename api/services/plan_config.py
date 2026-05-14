"""Plan definitions and enforcement for xpose.

Four SaaS tiers: free, starter, team, enterprise. Pricing locked May 2026.
Rule: superadmin role bypasses ALL plan limits. Always. Everywhere.
Plan lives on Workspace, not on User.
"""

PLANS = {
    "free": {
        "label": "Free",
        "price": 0,
        "max_targets": 1,
        "max_scans_per_month": 25,
        "max_modules_per_scan": 7,
        "max_seats": 1,
        "allowed_layers": [1],
        "features": {
            "intelligence_pipeline": False,
            "persona_clustering": False,
            "fingerprint_history": False,
            "bulk_import": False,
            "api_access": False,
            "shared_targets": False,
            "export_pdf": False,
            "custom_scrapers": False,
            "sso": False,
            "audit_log": False,
            "multi_tenant": False,
        },
        "description": "Check your own exposure.",
    },
    "starter": {
        "label": "Starter",
        "price": 49,
        "max_targets": 25,
        "max_scans_per_month": 250,
        "max_modules_per_scan": -1,
        "max_seats": 1,
        "allowed_layers": [1, 2],
        "features": {
            "intelligence_pipeline": True,
            "persona_clustering": True,
            "fingerprint_history": True,
            "bulk_import": True,
            "api_access": False,
            "shared_targets": False,
            "export_pdf": True,
            "custom_scrapers": False,
            "sso": False,
            "audit_log": False,
            "multi_tenant": False,
        },
        "description": "For individual professionals.",
    },
    "team": {
        "label": "Team",
        "price": 299,
        "max_targets": 200,
        "max_scans_per_month": 2000,
        "max_modules_per_scan": -1,
        "max_seats": 5,
        "allowed_layers": [1, 2, 3],
        "features": {
            "intelligence_pipeline": True,
            "persona_clustering": True,
            "fingerprint_history": True,
            "bulk_import": True,
            "api_access": True,
            "shared_targets": True,
            "export_pdf": True,
            "custom_scrapers": False,
            "sso": False,
            "audit_log": False,
            "multi_tenant": False,
        },
        "description": "For security teams.",
    },
    "enterprise": {
        "label": "Enterprise",
        "price": 2500,
        "max_targets": -1,  # unlimited
        "max_scans_per_month": -1,
        "max_modules_per_scan": -1,
        "max_seats": -1,
        "allowed_layers": [1, 2, 3, 4],
        "features": {
            "intelligence_pipeline": True,
            "persona_clustering": True,
            "fingerprint_history": True,
            "bulk_import": True,
            "api_access": True,
            "shared_targets": True,
            "export_pdf": True,
            "custom_scrapers": True,
            "sso": True,
            "audit_log": True,
            "multi_tenant": True,
        },
        "description": "For organizations.",
    },
}


def get_plan(plan_name: str) -> dict:
    """Get plan config by name, default to free."""
    return PLANS.get(plan_name, PLANS["free"])


def is_superadmin(role: str) -> bool:
    return role == "superadmin"


def check_target_limit(plan_name: str, current_count: int, role: str) -> tuple[bool, str]:
    """Check if workspace can add another target. Returns (allowed, message)."""
    if is_superadmin(role):
        return True, ""
    plan = get_plan(plan_name)
    limit = plan["max_targets"]
    if limit == -1:
        return True, ""
    if current_count >= limit:
        return False, f"{plan['label']} plan allows {limit} target(s). Upgrade to add more."
    return True, ""


def check_scan_limit(plan_name: str, scans_this_month: int, role: str) -> tuple[bool, str]:
    """Check if workspace can run another scan."""
    if is_superadmin(role):
        return True, ""
    plan = get_plan(plan_name)
    limit = plan["max_scans_per_month"]
    if limit == -1:
        return True, ""
    if scans_this_month >= limit:
        return False, f"{plan['label']} plan allows {limit} scans/month. Upgrade for more."
    return True, ""


def filter_modules_by_plan(modules: list[str], plan_name: str, role: str, module_layers: dict) -> list[str]:
    """Filter scan modules to only those allowed by plan. Superadmin bypasses."""
    if is_superadmin(role):
        return modules
    plan = get_plan(plan_name)
    allowed_layers = plan["allowed_layers"]
    max_modules = plan["max_modules_per_scan"]
    filtered = [m for m in modules if module_layers.get(m, 1) in allowed_layers]
    if max_modules != -1:
        filtered = filtered[:max_modules]
    return filtered


def check_feature(plan_name: str, feature: str, role: str) -> bool:
    """Check if a feature is available on this plan. Superadmin bypasses."""
    if is_superadmin(role):
        return True
    plan = get_plan(plan_name)
    return plan["features"].get(feature, False)
