"""Comprehensive End-to-End (E2E) integration test suite executing full pipeline scenarios."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from retailflow.config.settings import Settings
from retailflow.loader.engine import WarehouseLoaderEngine
from retailflow.pipeline.context import PipelineContext
from retailflow.transformation.engine import TransformationEngine
from retailflow.validation.engine import ValidationEngine
from retailflow.validation.scorecard import ScorecardGenerator
from tests.harness.assertions import assert_reconciled
from tests.harness.scenario_builder import ScenarioBuilder


@pytest.fixture
def e2e_context(tmp_path: Path) -> PipelineContext:
    """Fixture providing PipelineContext for E2E testing."""
    settings = Settings()
    settings.paths.raw_dir = tmp_path / "raw"
    settings.paths.processed_dir = tmp_path / "processed"
    settings.paths.bad_records_dir = tmp_path / "bad_records"
    settings.paths.log_dir = tmp_path / "logs"

    feed_file = tmp_path / "raw" / "sales_feed.csv"
    ScenarioBuilder.build_clean_scenario(feed_file, row_count=50)

    mock_db = MagicMock()
    mock_conn = MagicMock()
    mock_conn.encoding = "UTF8"
    mock_cursor = MagicMock()
    mock_db.get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = [1]

    mock_logger = MagicMock()

    return PipelineContext(
        configuration=settings,
        database=mock_db,
        logger=mock_logger,
        source_file=feed_file,
    )


def test_e2e_clean_execution(e2e_context: PipelineContext) -> None:
    """Test full end-to-end pipeline execution with clean synthetic dataset."""
    import pandas as pd
    raw_df = pd.read_csv(e2e_context.source_file)

    # 1. Validation Stage
    val_engine = ValidationEngine()
    clean_df, val_report = val_engine.validate_feed(raw_df, e2e_context)
    assert val_report.is_valid is True

    # Compute Data Quality Scorecard
    scorecard_gen = ScorecardGenerator()
    scorecard = scorecard_gen.generate_scorecard(raw_df, val_report)
    assert scorecard.overall_quality_score >= 90.0

    # 2. Transformation Stage
    trans_engine = TransformationEngine()
    fact_df, trans_report = trans_engine.transform_sales_feed(clean_df, e2e_context)
    assert trans_report.rows_transformed == 50

    # 3. Warehouse Bulk Load Stage
    loader_engine = WarehouseLoaderEngine()
    load_report = loader_engine.load_warehouse(fact_df, e2e_context)
    assert load_report.facts_loaded == 50
    assert_reconciled(load_report)


def test_e2e_anomaly_dataset_execution(e2e_context: PipelineContext, tmp_path: Path) -> None:
    """Test full end-to-end pipeline execution with anomaly dataset containing duplicates and invalid prices."""
    import pandas as pd

    anomaly_file = tmp_path / "raw" / "anomaly_sales.csv"
    ScenarioBuilder.build_anomaly_scenario(anomaly_file, row_count=100)
    e2e_context.source_file = anomaly_file

    raw_df = pd.read_csv(anomaly_file)
    val_engine = ValidationEngine()
    clean_df, val_report = val_engine.validate_feed(raw_df, e2e_context)

    # Check quarantine directory creation
    quarantine_dir = tmp_path / "bad_records" / e2e_context.run_id
    assert quarantine_dir.exists()
    assert (quarantine_dir / "invalid_rows.csv").exists()

    trans_engine = TransformationEngine()
    fact_df, trans_report = trans_engine.transform_sales_feed(clean_df, e2e_context)

    loader_engine = WarehouseLoaderEngine()
    load_report = loader_engine.load_warehouse(fact_df, e2e_context)

    assert load_report.reconciliation_summary is not None
    assert load_report.reconciliation_summary.is_reconciled is True
