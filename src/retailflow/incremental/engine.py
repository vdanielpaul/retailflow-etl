"""Incremental processing engine orchestrating evaluation, replay, checkpoints, and manifests."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from retailflow.incremental.change_detection import ChangeDetector
from retailflow.incremental.file_registry import FileRegistry
from retailflow.incremental.state_manager import StateManager
from retailflow.incremental.watermark import WatermarkManager
from retailflow.models.incremental import (
    FileClassification,
    IncrementalReport,
    IncrementalStrategy,
    ProcessingManifest,
)
from retailflow.pipeline.context import PipelineContext


class IncrementalEngine:
    """Orchestrator for incremental processing evaluation, change detection, state checkpointing, and manifests."""

    def __init__(
        self,
        watermark_manager: WatermarkManager,
        change_detector: ChangeDetector | None = None,
        file_registry: FileRegistry | None = None,
        state_manager: StateManager | None = None,
        strategy: IncrementalStrategy = IncrementalStrategy.FILE_HASH,
    ) -> None:
        self.watermark_manager = watermark_manager
        self.change_detector = change_detector or ChangeDetector(watermark_manager)
        self.file_registry = file_registry or FileRegistry()
        self.state_manager = state_manager or StateManager()
        self.strategy = strategy

    def evaluate_feed_file(
        self, file_path: Path, is_manual_replay: bool = False
    ) -> tuple[FileClassification, str]:
        """Evaluate feed file and return change classification and SHA-256 content hash."""
        return self.change_detector.classify_file(file_path, is_manual_replay=is_manual_replay)

    def generate_manifest_and_report(
        self,
        context: PipelineContext,
        classification: FileClassification,
        file_hash: str,
        start_time: float,
    ) -> tuple[ProcessingManifest, IncrementalReport]:
        """Generate ProcessingManifest artifact and IncrementalReport DTO.

        Args:
            context: Shared pipeline context.
            classification: Target file classification.
            file_hash: Target file SHA-256 hash.
            start_time: Evaluation start time.

        Returns:
            Tuple of (ProcessingManifest, IncrementalReport).
        """
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        filename = context.source_file.name if context.source_file else "N/A"
        watermark_val = self.watermark_manager.get_latest_watermark()

        manifest = ProcessingManifest(
            run_id=context.run_id,
            batch_id=context.batch_id,
            filename=filename,
            file_hash=file_hash,
            rows_read=context.metrics.rows_read,
            rows_loaded=context.metrics.rows_loaded,
            rows_rejected=context.metrics.rows_invalid,
            processing_strategy=self.strategy,
            classification=classification,
            execution_time_ms=elapsed_ms,
            pipeline_version="0.1.0",
            processed_at=datetime.now(timezone.utc).isoformat(),
            status="SUCCESS" if classification in (FileClassification.NEW, FileClassification.REPROCESS) else "SKIPPED",
        )

        # Write manifest.json under data/processed/<run_id>/
        self.file_registry.write_manifest(context.run_id, manifest.to_dict())

        recommendations = []
        if classification == FileClassification.DUPLICATE:
            recommendations.append("File hash already processed. Safely skipped re-ingestion.")
        elif classification == FileClassification.REPROCESS:
            recommendations.append("Manual operator replay triggered. Existing watermark overridden.")

        report = IncrementalReport(
            strategy_used=self.strategy,
            watermark_before=watermark_val,
            watermark_after=datetime.now(timezone.utc).isoformat(),
            files_processed=1 if classification in (FileClassification.NEW, FileClassification.REPROCESS) else 0,
            files_skipped=1 if classification == FileClassification.DUPLICATE else 0,
            duplicate_count=1 if classification == FileClassification.DUPLICATE else 0,
            replay_count=1 if classification == FileClassification.REPROCESS else 0,
            stale_count=1 if classification == FileClassification.STALE else 0,
            checkpoint_restored=False,
            execution_time_ms=elapsed_ms,
            recommendations=recommendations,
        )

        return manifest, report
