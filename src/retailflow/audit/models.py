"""Audit models, lifecycle event enums, severity levels, and execution dashboard DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PipelineLifecycleEvent(str, Enum):
    """Standardized pipeline lifecycle audit events."""

    PIPELINE_STARTED = "PIPELINE_STARTED"
    HEALTH_CHECK_COMPLETED = "HEALTH_CHECK_COMPLETED"
    VALIDATION_STARTED = "VALIDATION_STARTED"
    VALIDATION_COMPLETED = "VALIDATION_COMPLETED"
    TRANSFORMATION_STARTED = "TRANSFORMATION_STARTED"
    TRANSFORMATION_COMPLETED = "TRANSFORMATION_COMPLETED"
    LOADING_STARTED = "LOADING_STARTED"
    LOADING_COMPLETED = "LOADING_COMPLETED"
    WATERMARK_UPDATED = "WATERMARK_UPDATED"
    RECONCILIATION_COMPLETED = "RECONCILIATION_COMPLETED"
    PIPELINE_COMPLETED = "PIPELINE_COMPLETED"
    PIPELINE_FAILED = "PIPELINE_FAILED"


class AuditSeverity(str, Enum):
    """Operational audit event severity levels."""

    INFO = "INFO"          # Operational progress updates
    WARNING = "WARNING"      # Non-critical row quarantine or duplicate skip
    ERROR = "ERROR"        # Recoverable batch failure or validation threshold breach
    CRITICAL = "CRITICAL"   # Transaction abort or database connectivity loss


class FailureCategory(str, Enum):
    """Failure classification taxonomy."""

    CONFIGURATION = "CONFIGURATION"
    VALIDATION = "VALIDATION"
    TRANSFORMATION = "TRANSFORMATION"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    INCREMENTAL = "INCREMENTAL"
    AUDIT = "AUDIT"
    UNKNOWN = "UNKNOWN"


@dataclass
class AuditEvent:
    """Strongly typed audit event record."""

    event_id: str
    run_id: str
    event_name: PipelineLifecycleEvent
    severity: AuditSeverity
    timestamp: str
    stage: str
    duration_ms: float = 0.0
    message: str = ""
    failure_category: FailureCategory | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize audit event to dictionary."""
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "event_name": self.event_name.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "stage": self.stage,
            "duration_ms": round(self.duration_ms, 2),
            "message": self.message,
            "failure_category": self.failure_category.value if self.failure_category else None,
            "details": self.details,
        }


@dataclass
class PipelineExecutionSummary:
    """Operational Dashboard DTO summarizing end-to-end pipeline run metrics."""

    pipeline_name: str
    environment: str
    run_id: str
    batch_id: str
    start_time: str
    end_time: str
    duration_ms: float
    files_processed: int
    rows_processed: int
    rows_loaded: int
    rows_rejected: int
    throughput_rows_per_sec: float
    warnings_count: int
    errors_count: int
    final_status: str
    reconciliation_status: str
    timeline: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize execution summary for dashboard monitoring and API responses."""
        return {
            "pipeline_name": self.pipeline_name,
            "environment": self.environment,
            "run_id": self.run_id,
            "batch_id": self.batch_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": round(self.duration_ms, 2),
            "files_processed": self.files_processed,
            "rows_processed": self.rows_processed,
            "rows_loaded": self.rows_loaded,
            "rows_rejected": self.rows_rejected,
            "throughput_rows_per_sec": round(self.throughput_rows_per_sec, 2),
            "warnings_count": self.warnings_count,
            "errors_count": self.errors_count,
            "final_status": self.final_status,
            "reconciliation_status": self.reconciliation_status,
            "timeline": self.timeline,
        }
