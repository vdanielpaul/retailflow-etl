"""Integration tests for incremental processing, watermark tracking, and replay engine."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from retailflow.config.settings import Settings
from retailflow.incremental.engine import IncrementalEngine
from retailflow.incremental.watermark import WatermarkManager
from retailflow.models.incremental import FileClassification
from retailflow.pipeline.context import PipelineContext


@pytest.fixture
def incremental_context(tmp_path: Path) -> PipelineContext:
    """Fixture providing PipelineContext for incremental integration testing."""
    settings = Settings()
    sample_file = tmp_path / "feed_incremental.csv"
    sample_file.write_text("transaction_id,quantity\nTX-1,5\n")

    mock_db = MagicMock()
    mock_conn = MagicMock()
    mock_conn.encoding = "UTF8"
    mock_cursor = MagicMock()
    mock_db.get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # No watermark found initially

    mock_logger = MagicMock()

    return PipelineContext(
        configuration=settings,
        database=mock_db,
        logger=mock_logger,
        source_file=sample_file,
    )


def test_incremental_duplicate_detection(incremental_context: PipelineContext) -> None:
    """Test IncrementalEngine detects duplicate file hash and classifies as DUPLICATE."""
    watermark_mgr = WatermarkManager(incremental_context.database)
    # Simulate DB returning file hash match
    watermark_mgr.is_file_processed = MagicMock(return_value=True)

    engine = IncrementalEngine(watermark_manager=watermark_mgr)
    classification, file_hash = engine.evaluate_feed_file(incremental_context.source_file)

    assert classification == FileClassification.DUPLICATE
    assert len(file_hash) == 64


def test_incremental_manual_replay_override(incremental_context: PipelineContext) -> None:
    """Test IncrementalEngine overrides duplicate status when manual replay is requested."""
    watermark_mgr = WatermarkManager(incremental_context.database)
    watermark_mgr.is_file_processed = MagicMock(return_value=True)

    engine = IncrementalEngine(watermark_manager=watermark_mgr)
    classification, file_hash = engine.evaluate_feed_file(
        incremental_context.source_file, is_manual_replay=True
    )

    assert classification == FileClassification.REPROCESS
