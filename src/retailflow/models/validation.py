"""Structured validation models, results, and summary reporting objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationStatus(str, Enum):
    """Validation outcome status."""

    PASSED = "PASSED"
    FAILED = "FAILED"


class ValidationSeverity(str, Enum):
    """Validation failure severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ValidationResult:
    """Detailed evaluation result from an individual validator."""

    validator_name: str
    status: ValidationStatus
    records_checked: int
    records_failed: int
    severity: ValidationSeverity = ValidationSeverity.ERROR
    execution_time_ms: float = 0.0
    error_summary: dict[str, int] = field(default_factory=dict)
    failed_row_indices: list[int] = field(default_factory=list)
    failure_details: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize result object to dictionary for JSON output."""
        return {
            "validator_name": self.validator_name,
            "status": self.status.value,
            "records_checked": self.records_checked,
            "records_failed": self.records_failed,
            "severity": self.severity.value,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "error_summary": self.error_summary,
            "failed_row_count": len(self.failed_row_indices),
        }


@dataclass
class ValidationReport:
    """Aggregated validation report across all run validators."""

    run_id: str
    total_rows: int
    passed_rows: int
    failed_rows: int
    failure_rate_pct: float
    execution_time_ms: float
    is_valid: bool
    validator_results: list[ValidationResult] = field(default_factory=list)
    top_failure_reasons: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize validation report for audit logging and JSON report export."""
        return {
            "run_id": self.run_id,
            "total_rows": self.total_rows,
            "passed_rows": self.passed_rows,
            "failed_rows": self.failed_rows,
            "failure_rate_pct": round(self.failure_rate_pct, 2),
            "execution_time_ms": round(self.execution_time_ms, 2),
            "is_valid": self.is_valid,
            "validator_results": [r.to_dict() for r in self.validator_results],
            "top_failure_reasons": self.top_failure_reasons,
        }
