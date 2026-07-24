"""Metrics collection engine for operational performance tracking and auditing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricsCollector:
    """Dataclass holding real-time performance metrics for a pipeline run."""

    files_processed: int = 0
    rows_read: int = 0
    rows_valid: int = 0
    rows_invalid: int = 0
    rows_loaded: int = 0
    duplicate_rows: int = 0
    execution_time_ms: float = 0.0
    database_time_ms: float = 0.0
    validation_time_ms: float = 0.0
    transformation_time_ms: float = 0.0
    loading_time_ms: float = 0.0
    stage_durations_ms: dict[str, float] = field(default_factory=dict)

    def record_rows(self, read: int = 0, valid: int = 0, invalid: int = 0, loaded: int = 0, duplicates: int = 0) -> None:
        """Increment row metrics."""
        self.rows_read += read
        self.rows_valid += valid
        self.rows_invalid += invalid
        self.rows_loaded += loaded
        self.duplicate_rows += duplicates

    def record_stage_time(self, stage_name: str, duration_ms: float) -> None:
        """Record latency for a specific pipeline stage."""
        self.stage_durations_ms[stage_name] = self.stage_durations_ms.get(stage_name, 0.0) + duration_ms
        if "database" in stage_name.lower():
            self.database_time_ms += duration_ms
        elif "validation" in stage_name.lower():
            self.validation_time_ms += duration_ms
        elif "transformation" in stage_name.lower():
            self.transformation_time_ms += duration_ms
        elif "load" in stage_name.lower():
            self.loading_time_ms += duration_ms

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics state to dictionary for audit table ingestion."""
        return {
            "files_processed": self.files_processed,
            "rows_read": self.rows_read,
            "rows_valid": self.rows_valid,
            "rows_invalid": self.rows_invalid,
            "rows_loaded": self.rows_loaded,
            "duplicate_rows": self.duplicate_rows,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "database_time_ms": round(self.database_time_ms, 2),
            "validation_time_ms": round(self.validation_time_ms, 2),
            "transformation_time_ms": round(self.transformation_time_ms, 2),
            "loading_time_ms": round(self.loading_time_ms, 2),
            "stage_durations_ms": {k: round(v, 2) for k, v in self.stage_durations_ms.items()},
        }
