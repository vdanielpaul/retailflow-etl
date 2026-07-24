"""Unit tests for RetailFlow incremental processing framework."""

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from retailflow.config.settings import Settings
from retailflow.incremental.change_detection import ChangeDetector
from retailflow.incremental.engine import IncrementalEngine
from retailflow.incremental.file_registry import FileRegistry
from retailflow.incremental.state_manager import StateManager
from retailflow.incremental.watermark import WatermarkManager
from retailflow.models.incremental import FileClassification, IncrementalStrategy
from retailflow.pipeline.context import PipelineContext


@pytest.fixture
def mock_watermark_mgr() -> MagicMock:
    """Fixture providing mock WatermarkManager."""
    mock_wm = MagicMock(spec=WatermarkManager)
    mock_wm.get_latest_watermark.return_value = "2026-07-24T10:00:00+00:00"
    mock_wm.is_file_processed.return_value = False
    return mock_wm


def test_change_detector_new_file(tmp_path: Path, mock_watermark_mgr: MagicMock) -> None:
    """Test ChangeDetector classifies new file as NEW."""
    sample_file = tmp_path / "feed_001.csv"
    sample_file.write_text("transaction_id,quantity\nTX-1,5\n")

    detector = ChangeDetector(mock_watermark_mgr)
    classification, file_hash = detector.classify_file(sample_file)

    assert classification == FileClassification.NEW
    assert len(file_hash) == 64


def test_change_detector_duplicate_file(tmp_path: Path, mock_watermark_mgr: MagicMock) -> None:
    """Test ChangeDetector classifies previously processed file as DUPLICATE."""
    sample_file = tmp_path / "feed_001.csv"
    sample_file.write_text("transaction_id,quantity\nTX-1,5\n")

    mock_watermark_mgr.is_file_processed.return_value = True
    detector = ChangeDetector(mock_watermark_mgr)
    classification, file_hash = detector.classify_file(sample_file)

    assert classification == FileClassification.DUPLICATE


def test_state_manager_checkpoint(tmp_path: Path) -> None:
    """Test StateManager saves and loads stage checkpoint JSON."""
    manager = StateManager(processed_dir=tmp_path)
    path = manager.save_checkpoint(
        run_id="run-123",
        stage_name="TRANSFORMATION_PASSED",
        state_data={"transformed_rows": 100},
    )

    assert path.exists()
    checkpoint = manager.load_checkpoint("run-123")
    assert checkpoint is not None
    assert checkpoint["last_successful_stage"] == "TRANSFORMATION_PASSED"
    assert checkpoint["state"]["transformed_rows"] == 100


def test_incremental_engine_manifest_generation(tmp_path: Path, mock_watermark_mgr: MagicMock) -> None:
    """Test IncrementalEngine generates ProcessingManifest and IncrementalReport."""
    sample_file = tmp_path / "feed.csv"
    sample_file.write_text("tx_id\n1\n")

    settings = Settings()
    context = PipelineContext(
        configuration=settings,
        database=MagicMock(),
        logger=MagicMock(),
        source_file=sample_file,
    )

    file_registry = FileRegistry(processed_dir=tmp_path / "processed")
    engine = IncrementalEngine(
        watermark_manager=mock_watermark_mgr,
        file_registry=file_registry,
        strategy=IncrementalStrategy.FILE_HASH,
    )

    start_time = time.perf_counter()
    manifest, report = engine.generate_manifest_and_report(
        context=context,
        classification=FileClassification.NEW,
        file_hash="dummyhash123",
        start_time=start_time,
    )

    assert manifest.filename == "feed.csv"
    assert manifest.classification == FileClassification.NEW.value
    assert (tmp_path / "processed" / context.run_id / "manifest.json").exists()
    assert report.files_processed == 1
