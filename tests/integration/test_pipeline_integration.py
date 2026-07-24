"""End-to-end integration test suite verifying validation, transformation, and warehouse loading orchestration."""

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from retailflow.config.settings import Settings
from retailflow.loader.engine import WarehouseLoaderEngine
from retailflow.pipeline.context import PipelineContext
from retailflow.transformation.engine import TransformationEngine
from retailflow.validation.engine import ValidationEngine


@pytest.fixture
def integration_context(tmp_path: Path) -> PipelineContext:
    """Fixture providing PipelineContext for integration testing."""
    settings = Settings()
    settings.paths.bad_records_dir = tmp_path / "bad_records"

    sample_file = tmp_path / "daily_sales_feed.csv"
    sample_file.write_text("transaction_id,store_id,product_id,employee_id,quantity,unit_price,transaction_time\n")

    mock_db = MagicMock()
    mock_conn = MagicMock()
    mock_conn.encoding = "UTF8"
    mock_cursor = MagicMock()
    mock_db.get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = [1]  # Audit run ID 1

    mock_logger = MagicMock()

    return PipelineContext(
        configuration=settings,
        database=mock_db,
        logger=mock_logger,
        source_file=sample_file,
    )


def test_full_etl_pipeline_integration(integration_context: PipelineContext) -> None:
    """Test full end-to-end integration flow: Validation -> Transformation -> Warehouse Load -> Reconciliation."""
    raw_df = pd.DataFrame(
        {
            "transaction_id": ["TX-101", "TX-102", "TX-103"],
            "store_id": ["STR-001", "STR-001", "STR-001"],
            "product_id": ["PROD-001", "PROD-002", "PROD-001"],
            "employee_id": ["EMP-001", "EMP-001", "EMP-001"],
            "quantity": [2, -1, 5],  # TX-102 is invalid (negative quantity)
            "unit_price": [15.00, 10.00, 20.00],
            "transaction_time": ["2026-01-15 10:00:00", "2026-01-15 10:00:00", "2026-01-15 10:00:00"],
        }
    )

    # Step 1: Validation Stage
    validation_engine = ValidationEngine()
    clean_df, val_report = validation_engine.validate_feed(raw_df, integration_context)

    assert val_report.total_rows == 3
    assert val_report.passed_rows == 2
    assert val_report.failed_rows == 1
    assert len(clean_df) == 2

    # Step 2: Transformation Stage
    transform_engine = TransformationEngine()
    transform_engine.key_resolver._store_cache = {"STR-001": 1}
    transform_engine.key_resolver._product_cache = {"PROD-001": 10, "PROD-002": 20}
    transform_engine.key_resolver._employee_cache = {"EMP-001": 100}

    fact_df, trans_report = transform_engine.transform_sales_feed(clean_df, integration_context)

    assert trans_report.rows_transformed == 2
    assert fact_df["store_sk"][0] == 1
    assert fact_df["net_sales_amount"][0] == 30.00

    # Step 3: Warehouse Load Stage
    loader_engine = WarehouseLoaderEngine()
    load_report = loader_engine.load_warehouse(fact_df, integration_context)

    assert load_report.facts_loaded == 2
    assert load_report.reconciliation_summary is not None
    assert load_report.reconciliation_summary.source_rows == 3
    assert load_report.reconciliation_summary.validated_rows == 2
    assert load_report.reconciliation_summary.loaded_rows == 2
    assert load_report.reconciliation_summary.is_reconciled is True
