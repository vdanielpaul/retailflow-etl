"""Structured transformation result and execution summary models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TransformationReport:
    """Aggregated metrics summary for a complete batch transformation run."""

    run_id: str
    rows_received: int
    rows_transformed: int
    rows_skipped: int
    dimensions_updated: int
    dimensions_inserted: int
    facts_generated: int
    lookup_failures: int
    execution_time_ms: float
    warnings: list[str] = field(default_factory=list)
    stage_metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize transformation summary to dictionary for audit logging."""
        return {
            "run_id": self.run_id,
            "rows_received": self.rows_received,
            "rows_transformed": self.rows_transformed,
            "rows_skipped": self.rows_skipped,
            "dimensions_updated": self.dimensions_updated,
            "dimensions_inserted": self.dimensions_inserted,
            "facts_generated": self.facts_generated,
            "lookup_failures": self.lookup_failures,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "warnings_count": len(self.warnings),
            "warnings": self.warnings,
            "stage_metrics": self.stage_metrics,
        }
