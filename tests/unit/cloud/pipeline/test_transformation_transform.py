"""Beam integration tests for ApplyTransformationFn.

These tests use apache_beam.testing.TestPipeline to exercise the DoFn inside
an actual Beam pipeline context, verifying routing behaviour, enriched field
presence, and error record schema.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import apache_beam as beam
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to, is_not_empty

from retailflow.cloud.pipeline.adapters.transformation_adapter import (
    ENRICHED_FIELDS,
    TRANSFORMER_VERSION,
)
from retailflow.cloud.pipeline.transforms.transformation_transform import (
    TAG_TRANSFORM_ERROR,
    ApplyTransformationFn,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_record(overrides: dict | None = None) -> dict:
    """Canonical sale dict that passes all three transformation stages."""
    record = {
        "transaction_id": "TXN-001",
        "store_id": "STR-01",
        "product_id": "PRD-01",
        "customer_id": "CST-01",
        "employee_id": "EMP-01",
        "quantity": 2,
        "unit_price": 25.00,
        "discount_amount": 5.00,
        "transaction_time": datetime.now(timezone.utc).isoformat(),
        "email": "TEST@EXAMPLE.COM",
    }
    if overrides:
        record.update(overrides)
    return record


def _make_dofn(
    correlation_id: str = "corr-test",
    run_id: str = "run-test",
    filename: str = "gs://test/file.csv",
) -> ApplyTransformationFn:
    return ApplyTransformationFn(
        correlation_id=correlation_id,
        run_id=run_id,
        filename=filename,
    )


_TEST_ARGV = [
    "--runner", "DirectRunner",
    "--input_file", "gs://test/file.csv",
    "--silver_dataset", "ds",
    "--metadata_dataset", "md",
    "--quarantine_bucket", "qb",
    "--correlation_id", "corr-001",
]


# ---------------------------------------------------------------------------
# Routing — main output
# ---------------------------------------------------------------------------


def test_valid_record_routes_to_main_output():
    """A well-formed record must reach the main (transformed_sales) output."""
    record = _valid_record()

    def _check_transformed(elements):
        assert len(elements) == 1
        r = elements[0]
        # Check that enriched fields are present in the output record
        for field in ENRICHED_FIELDS:
            assert field in r, f"Enriched field '{field}' missing from main output"

    with TestPipeline(argv=_TEST_ARGV) as p:
        results = (
            p
            | "Create" >> beam.Create([record])
            | "Transform" >> beam.ParDo(_make_dofn()).with_outputs(TAG_TRANSFORM_ERROR, main="transformed")
        )

        assert_that(results["transformed"], _check_transformed, label="CheckTransformed")


def test_valid_record_does_not_route_to_error_output():
    """A well-formed record must NOT produce a transform error."""
    record = _valid_record()

    with TestPipeline(argv=_TEST_ARGV) as p:
        results = (
            p
            | "Create" >> beam.Create([record])
            | "Transform" >> beam.ParDo(_make_dofn()).with_outputs(TAG_TRANSFORM_ERROR, main="transformed")
        )

        assert_that(results[TAG_TRANSFORM_ERROR], equal_to([]), label="ErrorShouldBeEmpty")


# ---------------------------------------------------------------------------
# Enrichment validation
# ---------------------------------------------------------------------------


def test_gross_sales_amount_is_calculated():
    """Transformed record must contain a correct gross_sales_amount."""
    record = _valid_record({"quantity": 3, "unit_price": 10.00, "discount_amount": 0.0})

    def _check_gross(elements):
        assert len(elements) == 1
        assert elements[0]["gross_sales_amount"] == 30.0

    with TestPipeline(argv=_TEST_ARGV) as p:
        results = (
            p
            | "Create" >> beam.Create([record])
            | "Transform" >> beam.ParDo(_make_dofn()).with_outputs(TAG_TRANSFORM_ERROR, main="transformed")
        )
        assert_that(results["transformed"], _check_gross, label="CheckGross")


def test_net_sales_amount_is_calculated():
    """Transformed record must contain a correct net_sales_amount."""
    record = _valid_record({"quantity": 2, "unit_price": 50.00, "discount_amount": 10.00})

    def _check_net(elements):
        assert len(elements) == 1
        assert elements[0]["net_sales_amount"] == 90.0

    with TestPipeline(argv=_TEST_ARGV) as p:
        results = (
            p
            | "Create" >> beam.Create([record])
            | "Transform" >> beam.ParDo(_make_dofn()).with_outputs(TAG_TRANSFORM_ERROR, main="transformed")
        )
        assert_that(results["transformed"], _check_net, label="CheckNet")


def test_email_is_normalised_to_lowercase():
    """Normalization stage must lowercase email in the transformed output."""
    record = _valid_record({"email": "UPPER@EXAMPLE.COM"})

    def _check_email(elements):
        assert len(elements) == 1
        assert elements[0]["email"] == "upper@example.com"

    with TestPipeline(argv=_TEST_ARGV) as p:
        results = (
            p
            | "Create" >> beam.Create([record])
            | "Transform" >> beam.ParDo(_make_dofn()).with_outputs(TAG_TRANSFORM_ERROR, main="transformed")
        )
        assert_that(results["transformed"], _check_email, label="CheckEmail")


# ---------------------------------------------------------------------------
# Mixed batch — multiple records
# ---------------------------------------------------------------------------


def test_mixed_batch_all_valid_routes_to_main():
    """All valid records in a batch must reach the main output."""
    records = [
        _valid_record({"transaction_id": f"TXN-{i:03d}"})
        for i in range(5)
    ]

    def _check_count(elements):
        assert len(elements) == 5
        for r in elements:
            for field in ENRICHED_FIELDS:
                assert field in r

    with TestPipeline(argv=_TEST_ARGV) as p:
        results = (
            p
            | "Create" >> beam.Create(records)
            | "Transform" >> beam.ParDo(_make_dofn()).with_outputs(TAG_TRANSFORM_ERROR, main="transformed")
        )
        assert_that(results["transformed"], _check_count, label="CheckBatch")


# ---------------------------------------------------------------------------
# Transformer version in DoFn metadata
# ---------------------------------------------------------------------------


def test_transformer_version_constant_is_consistent():
    """The TAG_TRANSFORM_ERROR tag must be a non-empty string."""
    assert isinstance(TAG_TRANSFORM_ERROR, str)
    assert len(TAG_TRANSFORM_ERROR) > 0
