"""Reusable ETL assertion helpers for unit and integration testing."""

from __future__ import annotations

from retailflow.models.loader import LoadReport
from retailflow.models.validation import ValidationReport


def assert_reconciled(load_report: LoadReport) -> None:
    """Assert load report reconciliation summary is valid and reconciled."""
    assert load_report.reconciliation_summary is not None, "Reconciliation summary is missing."
    assert load_report.reconciliation_summary.is_reconciled is True, (
        f"Row count reconciliation failed: {load_report.reconciliation_summary}"
    )


def assert_validation_passed(val_report: ValidationReport) -> None:
    """Assert validation report is valid."""
    assert val_report.is_valid is True, f"Validation report failed: {val_report}"
    assert val_report.failed_rows == 0, f"Expected 0 failed rows, got {val_report.failed_rows}"
