"""Structured incremental models, file classifications, processing manifests, and reporting DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IncrementalStrategy(str, Enum):
    """Incremental execution strategy options."""

    TIMESTAMP = "TIMESTAMP"    # High-watermark timestamp comparison
    FILE_HASH = "FILE_HASH"    # SHA-256 content hash matching
    BATCH_ID = "BATCH_ID"      # Unique batch identifier lookup
    COMPOSITE = "COMPOSITE"    # Timestamp + SHA-256 hash composite
    FULL_RELOAD = "FULL_RELOAD"# Unconditional complete re-ingestion


class FileClassification(str, Enum):
    """Change detection classification status for incoming feed files."""

    NEW = "NEW"                # Unprocessed fresh feed file
    MODIFIED = "MODIFIED"      # File hash changed since last run
    DUPLICATE = "DUPLICATE"    # Identical file hash already processed
    STALE = "STALE"            # Timestamp older than current watermark
    REPROCESS = "REPROCESS"    # Operator-triggered manual replay


@dataclass
class ProcessingManifest:
    """Detailed processing manifest metadata exported per run to data/processed/<run_id>/manifest.json."""

    run_id: str
    batch_id: str
    filename: str
    file_hash: str
    rows_read: int
    rows_loaded: int
    rows_rejected: int
    processing_strategy: IncrementalStrategy
    classification: FileClassification
    execution_time_ms: float
    pipeline_version: str
    processed_at: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize manifest to dictionary for JSON output."""
        return {
            "run_id": self.run_id,
            "batch_id": self.batch_id,
            "filename": self.filename,
            "file_hash": self.file_hash,
            "rows_read": self.rows_read,
            "rows_loaded": self.rows_loaded,
            "rows_rejected": self.rows_rejected,
            "processing_strategy": self.processing_strategy.value,
            "classification": self.classification.value,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "pipeline_version": self.pipeline_version,
            "processed_at": self.processed_at,
            "status": self.status,
        }


@dataclass
class IncrementalReport:
    """Operational summary report for incremental feed evaluation and execution."""

    strategy_used: IncrementalStrategy
    watermark_before: str
    watermark_after: str
    files_processed: int
    files_skipped: int
    duplicate_count: int
    replay_count: int
    stale_count: int
    checkpoint_restored: bool
    execution_time_ms: float
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize report to dictionary for audit logging."""
        return {
            "strategy_used": self.strategy_used.value,
            "watermark_before": self.watermark_before,
            "watermark_after": self.watermark_after,
            "files_processed": self.files_processed,
            "files_skipped": self.files_skipped,
            "duplicate_count": self.duplicate_count,
            "replay_count": self.replay_count,
            "stale_count": self.stale_count,
            "checkpoint_restored": self.checkpoint_restored,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "recommendations": self.recommendations,
        }
