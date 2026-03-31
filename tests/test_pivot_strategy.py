"""Tests for PivotStrategy rule-based pivot engine."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.discovery.pivot_strategy import generate_pivots


def test_username_expansion():
    leads = [{"lead_type": "username", "lead_value": "mariogrotz", "confidence": 0.85}]
    pivots = generate_pivots(leads, {"organization": "Luxinnovation"}, "mario@lux.lu", 10, [])
    assert any("mariogrotz" in p.query and "github" in p.query for p in pivots)


def test_org_staff_lookup():
    leads = [{"lead_type": "username", "lead_value": "Luxinnovation", "confidence": 0.90, "lead_type": "name"}]
    # Fix: use proper lead_type
    leads = [{"lead_type": "name", "lead_value": "Luxinnovation", "confidence": 0.90}]
    profile = {"country_code": "LU", "organization": "Luxinnovation"}
    pivots = generate_pivots(leads, profile, "x@luxinnovation.lu", 10, [])
    assert any("staff" in p.query.lower() or "team" in p.query.lower() for p in pivots)


def test_low_confidence_skipped():
    leads = [{"lead_type": "username", "lead_value": "TelegramTips", "confidence": 0.50}]
    pivots = generate_pivots(leads, {}, "x@y.com", 10, [])
    assert len(pivots) == 0


def test_dedup_previous_queries():
    leads = [{"lead_type": "username", "lead_value": "mariogrotz", "confidence": 0.85}]
    previous = ['"mariogrotz" site:github.com OR site:medium.com OR site:dev.to']
    pivots = generate_pivots(leads, {}, "x@y.com", 10, previous)
    # The exact github/medium/dev.to query should be deduped
    assert not any("github" in p.query and "medium" in p.query and "dev.to" in p.query for p in pivots)


def test_budget_cap():
    leads = [
        {"lead_type": "username", "lead_value": f"user{i}", "confidence": 0.90}
        for i in range(20)
    ]
    pivots = generate_pivots(leads, {}, "x@y.com", 4, [])
    assert len(pivots) <= 2  # 4 // 2 = 2


def test_managed_domain_no_pivot():
    leads = [{"lead_type": "email", "lead_value": "someone@gmail.com", "confidence": 0.85}]
    pivots = generate_pivots(leads, {}, "x@gmail.com", 10, [])
    assert not any("site:gmail.com" in p.query for p in pivots)


def test_rcs_luxembourg():
    leads = [{"lead_type": "name", "lead_value": "Luxinnovation", "confidence": 0.90}]
    profile = {"country_code": "LU", "organization": "Luxinnovation"}
    pivots = generate_pivots(leads, profile, "x@luxinnovation.lu", 10, [])
    assert any("RCS" in p.query for p in pivots)


def test_email_variant_generation():
    leads = [{"lead_type": "name", "lead_value": "Jean-Michel Gaudron", "confidence": 0.85}]
    profile = {"organization": "Luxinnovation"}
    pivots = generate_pivots(leads, profile, "x@luxinnovation.lu", 10, [])
    assert any(p.pivot_type == "email_variant" for p in pivots)


def test_leaked_data_pivot():
    leads = [{"lead_type": "email", "lead_value": "info@luxinnovation.lu", "confidence": 0.85}]
    pivots = generate_pivots(leads, {}, "x@luxinnovation.lu", 10, [])
    assert any("leak" in p.query.lower() or "breach" in p.query.lower() for p in pivots)


if __name__ == "__main__":
    for name, func in list(globals().items()):
        if name.startswith("test_") and callable(func):
            try:
                func()
                print(f"  ✅ {name}")
            except AssertionError as e:
                print(f"  ❌ {name}: {e}")
            except Exception as e:
                print(f"  💥 {name}: {e}")
    print("\nDone.")
