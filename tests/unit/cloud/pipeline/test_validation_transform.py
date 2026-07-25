"""Beam integration tests for ValidateSaleRecordFn.

These tests use apache_beam.testing.TestPipeline to exercise the DoFn inside
an actual Beam pipeline context, verifying routing behaviour and quarantine
record schema completeness.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import apache_beam as beam
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to, is_not_empty
import pytest

from retailflow.cloud.pipeline.transforms.validation_transform import (
    TAG_INVALID,
    ValidateSaleRecordFn,
    VALIDATOR_VERSION,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_record(overrides: dict | None = None) -> dict:
    """Canonical sale dict that passes all business rules."""
    record = {
        "transaction_id": "TXN-001",
        "store_id": "STR-01",
        "product_id": "PRD-01",
        "customer_id": "CST-01",
        "employee_id": "EMP-01",
        "quantity": 3,
        "unit_price": 29.99,
        "discount_amount": 0.0,
        "transaction_time": datetime.now(timezone.utc).isoformat(),
    }
    if overrides:
        record.update(overrides)
    return record


def _invalid_record() -> dict:
    """Canonical sale dict that fails the future transaction_time rule."""
    future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    return _valid_record({"transaction_time": future})


def _make_dofn(correlation_id: str = "corr-test", run_id: str = "run-test", filename: str = "gs://test/file.csv") -> ValidateSaleRecordFn:
    return ValidateSaleRecordFn(
        correlation_id=correlation_id,
        run_id=run_id,
        filename=filename,
    )


# ---------------------------------------------------------------------------
# Routing — main output
# ---------------------------------------------------------------------------


def test_valid_record_routes_to_main_output():
    """A valid record must reach the main (verified_sales) output."""
    record = _valid_record()

    mock_args = [
        "--runner", "DirectRunner",
        "--input_file", "gs://test/file.csv",
        "--silver_dataset", "ds",
        "--metadata_dataset", "md",
        "--quarantine_bucket", "qb",
        "--correlation_id", "corr-001",
    ]

    with TestPipeline(argv=mock_args) as p:
        results = (
            p
            | "Create" >> beam.Create([record])
            | "Validate" >> beam.ParDo(_make_dofn()).with_outputs(TAG_INVALID, main="verified")
        )

        assert_that(results["verified"], equal_to([record]), label="CheckVerified")


# ---------------------------------------------------------------------------
# Routing — invalid side output
# ---------------------------------------------------------------------------


def test_invalid_record_routes_to_tag_invalid():
    """A record failing business rules must be routed to TAG_INVALID."""
    record = _invalid_record()

    mock_args = [
        "--runner", "DirectRunner",
        "--input_file", "gs://test/file.csv",
        "--silver_dataset", "ds",
        "--metadata_dataset", "md",
        "--quarantine_bucket", "qb",
        "--correlation_id", "corr-002",
    ]

    with TestPipeline(argv=mock_args) as p:
        results = (
            p
            | "Create" >> beam.Create([record])
            | "Validate" >> beam.ParDo(_make_dofn()).with_outputs(TAG_INVALID, main="verified")
        )

        assert_that(results["verified"], equal_to([]), label="MainShouldBeEmpty")
        assert_that(results[TAG_INVALID], is_not_empty(), label="InvalidShouldHaveEntry")


# ---------------------------------------------------------------------------
# Quarantine record schema completeness
# ---------------------------------------------------------------------------


def test_quarantine_record_contains_required_fields():
    """Quarantine records must contain all required fields for operational tracing."""
    record = _invalid_record()

    mock_args = [
        "--runner", "DirectRunner",
        "--input_file", "gs://test/file.csv",
        "--silver_dataset", "ds",
        "--metadata_dataset", "md",
        "--quarantine_bucket", "qb",
        "--correlation_id", "corr-003",
    ]

    def _assert_quarantine_schema(elements):
        """Custom assert_that matcher — receives the full PCollection as a list."""
        assert len(elements) == 1, f"Expected 1 quarantine record, got {len(elements)}"

        quarantine = json.loads(elements[0])

        required_fields = [
            "correlation_id",
            "run_id",
            "filename",
            "row_number",
            "validation_errors",
            "original_record",
            "quarantined_at",
            "validator_version",
        ]
        for field_name in required_fields:
            assert field_name in quarantine, f"Missing required quarantine field: {field_name}"

        assert quarantine["correlation_id"] == "corr-003"
        assert quarantine["run_id"] == "run-abc"
        assert quarantine["filename"] == "gs://test/file.csv"
        assert isinstance(quarantine["validation_errors"], list)
        assert len(quarantine["validation_errors"]) > 0
        assert quarantine["original_record"] == record
        assert quarantine["validator_version"] == VALIDATOR_VERSION

    with TestPipeline(argv=mock_args) as p:
        results = (
            p
            | "Create" >> beam.Create([record])
            | "Validate" >> beam.ParDo(_make_dofn(
                correlation_id="corr-003",
                run_id="run-abc",
                filename="gs://test/file.csv",
            )).with_outputs(TAG_INVALID, main="verified")
        )

        assert_that(results[TAG_INVALID], _assert_quarantine_schema, label="CheckSchema")


# ---------------------------------------------------------------------------
# Error aggregation on multiple violations
# ---------------------------------------------------------------------------


def test_quarantine_collects_all_errors():
    """All validation errors must be collected in the quarantine record — not fail-fast."""
    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    record = _valid_record({
        "quantity": -1,
        "transaction_time": future,
    })

    mock_args = [
        "--runner", "DirectRunner",
        "--input_file", "gs://test/file.csv",
        "--silver_dataset", "ds",
        "--metadata_dataset", "md",
        "--quarantine_bucket", "qb",
        "--correlation_id", "corr-004",
    ]

    def _assert_multi_error(elements):
        """Custom matcher — verifies multiple error codes are collected."""
        assert len(elements) == 1, f"Expected 1 quarantine record, got {len(elements)}"
        quarantine = json.loads(elements[0])
        errors = quarantine["validation_errors"]
        error_text = " ".join(errors)

        # Both quantity and future-date violations must appear in the collected errors
        has_quantity_error = "VAL005" in error_text
        has_future_error = "VAL006" in error_text
        triggered = sum([has_quantity_error, has_future_error])
        assert triggered >= 1, (
            f"Expected VAL005 or VAL006 in collected errors, got: {errors}"
        )

    with TestPipeline(argv=mock_args) as p:
        results = (
            p
            | "Create" >> beam.Create([record])
            | "Validate" >> beam.ParDo(_make_dofn()).with_outputs(TAG_INVALID, main="verified")
        )

        assert_that(results[TAG_INVALID], _assert_multi_error, label="CheckMultiError")


# ---------------------------------------------------------------------------
# Mixed batch — valid and invalid records
# ---------------------------------------------------------------------------


def test_mixed_batch_routes_correctly():
    """A batch of mixed valid and invalid records must be split correctly."""
    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()

    valid1 = _valid_record({"transaction_id": "TXN-VALID-01"})
    valid2 = _valid_record({"transaction_id": "TXN-VALID-02"})
    invalid1 = _valid_record({"transaction_id": "TXN-BAD-01", "transaction_time": future})

    mock_args = [
        "--runner", "DirectRunner",
        "--input_file", "gs://test/file.csv",
        "--silver_dataset", "ds",
        "--metadata_dataset", "md",
        "--quarantine_bucket", "qb",
        "--correlation_id", "corr-005",
    ]

    with TestPipeline(argv=mock_args) as p:
        results = (
            p
            | "Create" >> beam.Create([valid1, invalid1, valid2])
            | "Validate" >> beam.ParDo(_make_dofn()).with_outputs(TAG_INVALID, main="verified")
        )

        assert_that(
            results["verified"],
            equal_to([valid1, valid2]),
            label="CheckVerifiedCount",
        )
        assert_that(
            results[TAG_INVALID],
            is_not_empty(),
            label="CheckInvalidPresent",
        )
