"""Unit tests for RetailFlow data validation framework and quarantine engine."""

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from retailflow.config.settings import Settings
from retailflow.models.validation import ValidationStatus
from retailflow.pipeline.context import PipelineContext
from retailflow.validation.engine import ValidationEngine
from retailflow.validation.validators import (
    BusinessRuleValidator,
    DuplicateValidator,
    SchemaValidator,
)


@pytest.fixture
def sample_context(tmp_path: Path) -> PipelineContext:
    """Fixture providing PipelineContext instance."""
    settings = Settings()
    settings.paths.bad_records_dir = tmp_path / "bad_records"

    sample_file = tmp_path / "sample_sales.csv"
    sample_file.write_text("transaction_id,store_id,product_id,employee_id,quantity,unit_price,transaction_time\n")

    mock_db = MagicMock()
    mock_logger = MagicMock()

    return PipelineContext(
        configuration=settings,
        database=mock_db,
        logger=mock_logger,
        source_file=sample_file,
    )


def test_schema_validator_success(sample_context: PipelineContext) -> None:
    """Test SchemaValidator passes when all required columns are present."""
    df = pd.DataFrame(
        columns=[
            "transaction_id",
            "store_id",
            "product_id",
            "employee_id",
            "quantity",
            "unit_price",
            "transaction_time",
        ]
    )

    validator = SchemaValidator()
    result = validator.validate(df, sample_context)

    assert result.status == ValidationStatus.PASSED
    assert result.records_failed == 0


def test_schema_validator_missing_column(sample_context: PipelineContext) -> None:
    """Test SchemaValidator fails when a required column is missing."""
    df = pd.DataFrame(columns=["transaction_id", "store_id"])

    validator = SchemaValidator()
    result = validator.validate(df, sample_context)

    assert result.status == ValidationStatus.FAILED
    assert result.records_failed > 0
    assert "VAL001_MISSING_COLUMN" in result.error_summary


def test_business_rule_validator_negative_quantity(sample_context: PipelineContext) -> None:
    """Test BusinessRuleValidator catches negative quantities (VAL005)."""
    df = pd.DataFrame(
        {
            "quantity": [5, -2, 10],
            "unit_price": [10.0, 15.0, 20.0],
            "transaction_time": ["2026-01-01 10:00:00", "2026-01-01 10:00:00", "2026-01-01 10:00:00"],
        }
    )

    validator = BusinessRuleValidator()
    result = validator.validate(df, sample_context)

    assert result.status == ValidationStatus.FAILED
    assert 1 in result.failed_row_indices
    assert "VAL005_NEGATIVE_QUANTITY" in result.error_summary


def test_duplicate_validator(sample_context: PipelineContext) -> None:
    """Test DuplicateValidator flags duplicate primary keys (VAL003)."""
    df = pd.DataFrame(
        {
            "transaction_id": ["TX-100", "TX-100", "TX-101"],
            "product_id": ["P1", "P1", "P2"],
        }
    )

    validator = DuplicateValidator()
    result = validator.validate(df, sample_context)

    assert result.status == ValidationStatus.FAILED
    assert 1 in result.failed_row_indices
    assert "VAL003_DUPLICATE_PRIMARY_KEY" in result.error_summary


def test_validation_engine_quarantine_flow(sample_context: PipelineContext, tmp_path: Path) -> None:
    """Test ValidationEngine separates clean vs bad rows and generates per-run quarantine files."""
    df = pd.DataFrame(
        {
            "transaction_id": ["TX-1", "TX-2", "TX-3"],
            "store_id": ["STR-1", "STR-1", "STR-1"],
            "product_id": ["P-1", "P-1", "P-1"],
            "employee_id": ["EMP-1", "EMP-1", "EMP-1"],
            "quantity": [10, -5, 2],  # Index 1 is invalid
            "unit_price": [19.99, 19.99, 19.99],
            "transaction_time": ["2026-01-01 10:00:00", "2026-01-01 10:00:00", "2026-01-01 10:00:00"],
        }
    )

    engine = ValidationEngine()
    clean_df, report = engine.validate_feed(df, sample_context)

    assert len(clean_df) == 2
    assert report.failed_rows == 1
    assert report.passed_rows == 2

    # Check quarantine directory creation under data/bad_records/<run_id>/
    quarantine_dir = tmp_path / "bad_records" / sample_context.run_id
    assert quarantine_dir.exists()
    assert (quarantine_dir / "invalid_rows.csv").exists()
    assert (quarantine_dir / "validation_report.json").exists()
    assert (quarantine_dir / "summary.json").exists()
