"""Characterization tests for A1.5 secondary identifier extraction."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from api.services.secondary_identifiers import (
    _extract_phones,
    _extract_wallets,
    PHONE_SKIP_MODULES,
)
from api.services.secondary_identifier_enricher import SECONDARY_INPUT_TYPES


class MockFinding:
    """Minimal Finding-like object matching the attributes _extract_phones/_extract_wallets read."""
    def __init__(self, data=None, module="test_module", description=None):
        self.data = data or {}
        self.module = module
        self.description = description


# ─── Phone extraction tests ──────────────────────────────────────────────

def test_extract_phone_from_data_key():
    pytest.importorskip("phonenumbers")
    f = MockFinding(data={"phone": "+33612345678"})
    result = _extract_phones([f])
    assert "+33612345678" in result


def test_extract_phone_from_nested_details_key():
    pytest.importorskip("phonenumbers")
    f = MockFinding(data={"details": {"phone": "+33612345678"}})
    result = _extract_phones([f])
    assert "+33612345678" in result


def test_extract_phone_skipped_on_blacklisted_module():
    pytest.importorskip("phonenumbers")
    if not PHONE_SKIP_MODULES:
        pytest.skip("PHONE_SKIP_MODULES is empty")
    blacklisted = next(iter(PHONE_SKIP_MODULES))
    f = MockFinding(data={"phone": "+33612345678"}, module=blacklisted)
    result = _extract_phones([f])
    assert result == []


def test_extract_phone_empty_findings_returns_empty_list():
    assert _extract_phones([]) == []


# ─── Wallet extraction tests ─────────────────────────────────────────────

def test_extract_btc_address_from_data_key():
    f = MockFinding(data={"btc_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"})
    result = _extract_wallets([f])
    assert any(
        w["chain"] == "btc" and w["address"] == "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        for w in result
    )


def test_extract_eth_address_normalized_lowercase():
    addr = "0x742d35Cc6634C0532925a3b844Bc9e7595f8e8E5"
    f = MockFinding(data={"eth_address": addr})
    result = _extract_wallets([f])
    eths = [w for w in result if w["chain"] == "eth"]
    assert eths, "no eth wallet extracted"
    assert eths[0]["address"] == addr.lower()


def test_extract_wallets_deduplicates_across_findings():
    btc = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    f1 = MockFinding(data={"btc_address": btc})
    f2 = MockFinding(data={"details": {"wallet": btc}})
    result = _extract_wallets([f1, f2])
    matches = [w for w in result if w["address"] == btc]
    assert len(matches) == 1


# ─── Contract test ───────────────────────────────────────────────────────

def test_secondary_input_types_contract():
    assert "phone" in SECONDARY_INPUT_TYPES
    assert "crypto_wallet" in SECONDARY_INPUT_TYPES
