"""Data Quality Scorecard model measuring 6 dimensions of data quality."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class QualityScorecard:
    """Data Quality Scorecard measuring 6 key data quality dimensions."""

    run_id: str
    total_records: int
    completeness_pct: float
    validity_pct: float
    uniqueness_pct: float
    consistency_pct: float
    conformity_pct: float
    freshness_pct: float
    overall_quality_score: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize scorecard to dictionary."""
        return {
            "run_id": self.run_id,
            "total_records": self.total_records,
            "completeness_pct": round(self.completeness_pct, 2),
            "validity_pct": round(self.validity_pct, 2),
            "uniqueness_pct": round(self.uniqueness_pct, 2),
            "consistency_pct": round(self.consistency_pct, 2),
            "conformity_pct": round(self.conformity_pct, 2),
            "freshness_pct": round(self.freshness_pct, 2),
            "overall_quality_score": round(self.overall_quality_score, 2),
        }
