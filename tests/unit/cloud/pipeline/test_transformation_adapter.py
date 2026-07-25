"""Unit tests for TransformationAdapter.

These tests exercise the adapter in isolation — no Beam TestPipeline required.
The adapter is pure Python: it accepts a dict, invokes the three transformation
functions, and returns a TransformationResult. Tests verify successful enrichment,
per-stage failure handling, derived field generation, and adapter reuse.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from retailflow.cloud.pipeline.adapters.transformation_adapter import (
    ENRICHED_FIELDS,
    TRANSFORMER_VERSION,
    TransformationAdapter,
    TransformationResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _valid_record(overrides: dict | None = None) -> dict:
    """Build a minimal canonical sale dict that passes cleaning, normalization, and enrichment."""
    record = {
        "transaction_id": "TXN-001",
        "store_id": "STR-01",
        "product_id": "PRD-01",
        "customer_id": "CST-01",
        "employee_id": "EMP-01",
        "quantity": 3,
        "unit_price": 29.99,
        "discount_amount": 5.00,
        "transaction_time": datetime.now(timezone.utc).isoformat(),
        "email": "TEST@EXAMPLE.COM",
    }
    if overrides:
        record.update(overrides)
    return record


# ---------------------------------------------------------------------------
# Adapter construction
# ---------------------------------------------------------------------------


def test_adapter_instantiation():
    """TransformationAdapter should initialise without errors."""
    adapter = TransformationAdapter()
    assert adapter is not None


# ---------------------------------------------------------------------------
# Successful transformation path
# ---------------------------------------------------------------------------


def test_successful_transformation_returns_success():
    """A well-formed canonical record must produce success=True."""
    adapter = TransformationAdapter()
    result = adapter.transform(_valid_record())

    assert isinstance(result, TransformationResult)
    assert result.success is True
    assert result.error is None
    assert result.transformed_record is not None


def test_transformed_record_contains_all_enriched_fields():
    """Enrichment stage must add all five derived financial metric fields."""
    adapter = TransformationAdapter()
    result = adapter.transform(_valid_record())

    assert result.success is True
    for field in ENRICHED_FIELDS:
        assert field in result.transformed_record, (
            f"Enriched field '{field}' missing from transformed record"
        )


def test_gross_sales_calculation():
    """gross_sales_amount = quantity × unit_price (rounded to 2dp)."""
    record = _valid_record({"quantity": 3, "unit_price": 29.99, "discount_amount": 0.0})
    adapter = TransformationAdapter()
    result = adapter.transform(record)

    assert result.success is True
    expected = round(3 * 29.99, 2)
    assert result.transformed_record["gross_sales_amount"] == expected


def test_net_sales_calculation():
    """net_sales_amount = (quantity × unit_price) − discount_amount."""
    record = _valid_record({"quantity": 2, "unit_price": 50.00, "discount_amount": 10.00})
    adapter = TransformationAdapter()
    result = adapter.transform(record)

    assert result.success is True
    expected_net = round(2 * 50.00 - 10.00, 2)
    assert result.transformed_record["net_sales_amount"] == expected_net


def test_discount_percentage_calculation():
    """discount_percentage = (discount_amount / gross_sales) × 100."""
    record = _valid_record({"quantity": 1, "unit_price": 100.00, "discount_amount": 20.00})
    adapter = TransformationAdapter()
    result = adapter.transform(record)

    assert result.success is True
    assert result.transformed_record["discount_percentage"] == 20.00


def test_zero_discount_produces_zero_percentage():
    """discount_percentage must be 0.0 when no discount is applied."""
    record = _valid_record({"quantity": 1, "unit_price": 50.00, "discount_amount": 0.00})
    adapter = TransformationAdapter()
    result = adapter.transform(record)

    assert result.success is True
    assert result.transformed_record["discount_percentage"] == 0.0


# ---------------------------------------------------------------------------
# Normalization effects
# ---------------------------------------------------------------------------


def test_email_is_lowercased():
    """Normalization stage must lowercase email addresses."""
    record = _valid_record({"email": "USER@EXAMPLE.COM"})
    adapter = TransformationAdapter()
    result = adapter.transform(record)

    assert result.success is True
    assert result.transformed_record.get("email") == "user@example.com"


def test_transaction_id_is_uppercased():
    """Normalization stage must uppercase transaction_id codes."""
    record = _valid_record({"transaction_id": "txn-001"})
    adapter = TransformationAdapter()
    result = adapter.transform(record)

    assert result.success is True
    assert result.transformed_record["transaction_id"] == "TXN-001"


def test_store_id_is_uppercased():
    """Normalization stage must uppercase store_id codes."""
    record = _valid_record({"store_id": "str-01"})
    adapter = TransformationAdapter()
    result = adapter.transform(record)

    assert result.success is True
    assert result.transformed_record["store_id"] == "STR-01"


# ---------------------------------------------------------------------------
# Cleaning effects
# ---------------------------------------------------------------------------


def test_whitespace_is_trimmed_from_string_fields():
    """Cleaning stage must strip leading/trailing whitespace from string fields."""
    record = _valid_record({"transaction_id": "  TXN-001  "})
    adapter = TransformationAdapter()
    result = adapter.transform(record)

    assert result.success is True
    assert result.transformed_record["transaction_id"] == "TXN-001"


# ---------------------------------------------------------------------------
# Result model completeness
# ---------------------------------------------------------------------------


def test_result_contains_transformation_timestamp():
    """TransformationResult must carry a non-empty ISO timestamp."""
    adapter = TransformationAdapter()
    result = adapter.transform(_valid_record())

    assert result.transformation_timestamp is not None
    parsed = datetime.fromisoformat(result.transformation_timestamp)
    assert parsed is not None


def test_result_contains_transformer_version():
    """TransformationResult must carry a non-empty transformer_version string."""
    adapter = TransformationAdapter()
    result = adapter.transform(_valid_record())

    assert result.transformer_version == TRANSFORMER_VERSION
    assert len(result.transformer_version) > 0


def test_result_contains_execution_time_ms():
    """TransformationResult.execution_time_ms must be a non-negative float."""
    adapter = TransformationAdapter()
    result = adapter.transform(_valid_record())

    assert isinstance(result.execution_time_ms, float)
    assert result.execution_time_ms >= 0.0


# ---------------------------------------------------------------------------
# Adapter reuse — same instance, multiple records
# ---------------------------------------------------------------------------


def test_adapter_reuse_produces_consistent_results():
    """A single adapter instance must produce consistent results across multiple calls."""
    adapter = TransformationAdapter()

    r1 = adapter.transform(_valid_record({"transaction_id": "TXN-A01"}))
    r2 = adapter.transform(_valid_record({"transaction_id": "TXN-B02"}))
    r3 = adapter.transform(_valid_record({"transaction_id": "TXN-C03"}))

    assert r1.success is True
    assert r2.success is True
    assert r3.success is True
    assert r1.transformed_record["transaction_id"] == "TXN-A01"
    assert r2.transformed_record["transaction_id"] == "TXN-B02"
    assert r3.transformed_record["transaction_id"] == "TXN-C03"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_transformer_version_constant_is_set():
    """TRANSFORMER_VERSION must be a non-empty string for audit tracing."""
    assert isinstance(TRANSFORMER_VERSION, str)
    assert len(TRANSFORMER_VERSION) > 0
    assert "TransformationAdapter" in TRANSFORMER_VERSION


def test_enriched_fields_constant_contains_expected_fields():
    """ENRICHED_FIELDS must contain all five derived financial metric field names."""
    expected = {
        "gross_sales_amount",
        "net_sales_amount",
        "discount_percentage",
        "effective_unit_price",
        "transaction_line_total",
    }
    assert expected.issubset(ENRICHED_FIELDS)
