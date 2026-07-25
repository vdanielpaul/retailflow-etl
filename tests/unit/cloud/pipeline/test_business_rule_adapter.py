"""Unit tests for BusinessRuleAdapter.

These tests exercise the adapter in isolation — no Beam TestPipeline required.
The adapter is pure Python: it accepts a dict, invokes BusinessRuleValidator,
and returns a ValidationCheckResult. Tests verify both the routing logic and
the completeness of error collection.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from retailflow.cloud.pipeline.adapters.business_rule_adapter import (
    VALIDATOR_VERSION,
    BusinessRuleAdapter,
    ValidationCheckResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _valid_record(overrides: dict | None = None) -> dict:
    """Build a minimal canonical sale dict that passes all business rules."""
    record = {
        "transaction_id": "TXN-001",
        "store_id": "STR-01",
        "product_id": "PRD-01",
        "customer_id": "CST-01",
        "employee_id": "EMP-01",
        "quantity": 2,
        "unit_price": 19.99,
        "discount_amount": 0.0,
        "transaction_time": datetime.now(timezone.utc).isoformat(),
    }
    if overrides:
        record.update(overrides)
    return record


# ---------------------------------------------------------------------------
# Adapter construction
# ---------------------------------------------------------------------------


def test_adapter_instantiation_creates_validator():
    """BusinessRuleAdapter should initialise without errors."""
    adapter = BusinessRuleAdapter()
    assert adapter is not None
    assert adapter._validator is not None


# ---------------------------------------------------------------------------
# Valid record path
# ---------------------------------------------------------------------------


def test_valid_record_passes():
    """A well-formed canonical record should produce valid=True and no errors."""
    adapter = BusinessRuleAdapter()
    result = adapter.validate(_valid_record())

    assert isinstance(result, ValidationCheckResult)
    assert result.valid is True
    assert result.errors == []
    assert result.canonical_record is not None
    assert result.validation_timestamp is not None


def test_validation_timestamp_is_utc_iso():
    """validation_timestamp must be a non-empty ISO timestamp string."""
    adapter = BusinessRuleAdapter()
    result = adapter.validate(_valid_record())

    # Must parse as a valid datetime
    parsed = datetime.fromisoformat(result.validation_timestamp)
    assert parsed is not None


# ---------------------------------------------------------------------------
# Business rule violations — individual checks
# ---------------------------------------------------------------------------


def test_future_transaction_time_fails():
    """Records with transaction_time in the future should fail validation."""
    future_time = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    record = _valid_record({"transaction_time": future_time})

    adapter = BusinessRuleAdapter()
    result = adapter.validate(record)

    assert result.valid is False
    assert len(result.errors) > 0
    # At least one error must mention the future date code
    assert any("VAL006" in e for e in result.errors)


def test_zero_quantity_fails():
    """Records with quantity == 0 should fail the non-negative quantity rule."""
    record = _valid_record({"quantity": 0})

    adapter = BusinessRuleAdapter()
    result = adapter.validate(record)

    assert result.valid is False
    assert any("VAL005" in e for e in result.errors)


def test_negative_quantity_fails():
    """Records with quantity < 0 should fail."""
    record = _valid_record({"quantity": -5})

    adapter = BusinessRuleAdapter()
    result = adapter.validate(record)

    assert result.valid is False
    assert any("VAL005" in e for e in result.errors)


def test_negative_unit_price_fails():
    """Records with unit_price < 0 should fail."""
    record = _valid_record({"unit_price": -9.99})

    adapter = BusinessRuleAdapter()
    result = adapter.validate(record)

    assert result.valid is False
    assert any("VAL002" in e for e in result.errors)


# ---------------------------------------------------------------------------
# Error aggregation — all failures collected, not fail-fast
# ---------------------------------------------------------------------------


def test_multiple_violations_collected():
    """All validation failures must be collected and returned together.

    A record that violates both quantity and transaction_time rules should
    produce a result with both error codes — the adapter must not short-circuit
    on the first failure.
    """
    future_time = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    record = _valid_record({
        "quantity": -1,
        "transaction_time": future_time,
        "unit_price": -5.00,
    })

    adapter = BusinessRuleAdapter()
    result = adapter.validate(record)

    assert result.valid is False
    # Should have at least two distinct error codes present
    error_text = " ".join(result.errors)
    has_quantity_error = "VAL005" in error_text
    has_future_error = "VAL006" in error_text
    has_price_error = "VAL002" in error_text

    # At least two of the three expected categories must appear
    triggered = sum([has_quantity_error, has_future_error, has_price_error])
    assert triggered >= 2, f"Expected at least 2 distinct error categories, got errors: {result.errors}"


# ---------------------------------------------------------------------------
# Result model completeness
# ---------------------------------------------------------------------------


def test_invalid_result_preserves_original_record():
    """The original canonical record must be preserved on invalid results."""
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    record = _valid_record({"transaction_time": future_time})

    adapter = BusinessRuleAdapter()
    result = adapter.validate(record)

    assert result.valid is False
    assert result.canonical_record == record


def test_valid_result_preserves_original_record():
    """The original canonical record must be preserved on valid results."""
    record = _valid_record()
    adapter = BusinessRuleAdapter()
    result = adapter.validate(record)

    assert result.valid is True
    assert result.canonical_record == record


# ---------------------------------------------------------------------------
# Adapter reuse — same instance, multiple records
# ---------------------------------------------------------------------------


def test_adapter_reuse_across_records():
    """A single adapter instance must produce consistent results across calls.

    This validates the setup()-once semantics used by ValidateSaleRecordFn.
    """
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    adapter = BusinessRuleAdapter()

    result_valid = adapter.validate(_valid_record())
    result_invalid = adapter.validate(_valid_record({"transaction_time": future_time}))
    result_valid_again = adapter.validate(_valid_record())

    assert result_valid.valid is True
    assert result_invalid.valid is False
    assert result_valid_again.valid is True


# ---------------------------------------------------------------------------
# VALIDATOR_VERSION constant
# ---------------------------------------------------------------------------


def test_validator_version_constant_is_set():
    """VALIDATOR_VERSION must be a non-empty string for quarantine record tracing."""
    assert isinstance(VALIDATOR_VERSION, str)
    assert len(VALIDATOR_VERSION) > 0
    assert "BusinessRuleValidator" in VALIDATOR_VERSION
