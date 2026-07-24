"""Structured database loader models, bulk strategy enums, and reconciliation DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LoadStrategy(str, Enum):
    """Database bulk ingestion strategy options."""

    COPY = "COPY"                      # High-volume streaming via PostgreSQL COPY FROM STDIN
    EXECUTE_VALUES = "EXECUTE_VALUES"  # Fast batch insert via psycopg2.extras.execute_values
    INSERT = "INSERT"                  # Standard parameterized multi-row INSERT


@dataclass
class ReconciliationReport:
    """End-to-end data pipeline row count reconciliation audit report."""

    source_rows: int
    validated_rows: int
    transformed_rows: int
    loaded_rows: int
    rejected_rows: int
    duplicate_rows: int
    is_reconciled: bool

    def to_dict(self) -> dict[str, Any]:
        """Serialize reconciliation metrics to dictionary."""
        return {
            "source_rows": self.source_rows,
            "validated_rows": self.validated_rows,
            "transformed_rows": self.transformed_rows,
            "loaded_rows": self.loaded_rows,
            "rejected_rows": self.rejected_rows,
            "duplicate_rows": self.duplicate_rows,
            "is_reconciled": self.is_reconciled,
        }


@dataclass
class LoadReport:
    """Comprehensive performance and statistics report for warehouse loading operation."""

    run_id: str
    dimensions_inserted: int
    dimensions_updated: int
    dimensions_unchanged: int
    facts_loaded: int
    facts_rejected: int
    batches_processed: int
    average_batch_time_ms: float
    rows_per_second: float
    database_time_ms: float
    rollback_count: int
    savepoint_rollbacks: int
    reconciliation_summary: ReconciliationReport | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize load summary report for audit logging and JSON reporting."""
        return {
            "run_id": self.run_id,
            "dimensions_inserted": self.dimensions_inserted,
            "dimensions_updated": self.dimensions_updated,
            "dimensions_unchanged": self.dimensions_unchanged,
            "facts_loaded": self.facts_loaded,
            "facts_rejected": self.facts_rejected,
            "batches_processed": self.batches_processed,
            "average_batch_time_ms": round(self.average_batch_time_ms, 2),
            "rows_per_second": round(self.rows_per_second, 2),
            "database_time_ms": round(self.database_time_ms, 2),
            "rollback_count": self.rollback_count,
            "savepoint_rollbacks": self.savepoint_rollbacks,
            "reconciliation_summary": (
                self.reconciliation_summary.to_dict() if self.reconciliation_summary else None
            ),
            "warnings_count": len(self.warnings),
            "warnings": self.warnings,
        }
