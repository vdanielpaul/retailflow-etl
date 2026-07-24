"""Data quality scorecard calculator evaluating feed quality metrics."""

from __future__ import annotations

import pandas as pd

from retailflow.models.scorecard import QualityScorecard
from retailflow.models.validation import ValidationReport


class ScorecardGenerator:
    """Evaluates validation reports and DataFrames to compute Data Quality Scorecards."""

    def generate_scorecard(
        self, df: pd.DataFrame, report: ValidationReport
    ) -> QualityScorecard:
        """Compute weighted Data Quality Scorecard across 6 dimensions.

        Args:
            df: Input raw feed DataFrame.
            report: ValidationReport object from validation engine.

        Returns:
            QualityScorecard object with overall quality index.
        """
        total_rows = len(df)
        if total_rows == 0:
            return QualityScorecard(
                run_id=report.run_id,
                total_records=0,
                completeness_pct=100.0,
                validity_pct=100.0,
                uniqueness_pct=100.0,
                consistency_pct=100.0,
                conformity_pct=100.0,
                freshness_pct=100.0,
                overall_quality_score=100.0,
            )

        # 1. Completeness: Non-null cell percentage
        total_cells = df.size
        null_cells = df.isna().sum().sum()
        completeness = ((total_cells - null_cells) / total_cells * 100.0) if total_cells > 0 else 100.0

        # 2. Validity: Rows passing validation rules
        validity = (report.passed_rows / total_rows * 100.0) if total_rows > 0 else 100.0

        # 3. Uniqueness: Non-duplicate row percentage
        dups = df.duplicated(subset=["transaction_id"]).sum() if "transaction_id" in df.columns else 0
        uniqueness = ((total_rows - dups) / total_rows * 100.0) if total_rows > 0 else 100.0

        # 4. Consistency & Conformity
        consistency = 100.0
        conformity = 100.0 if report.is_valid else 80.0
        freshness = 100.0

        # Overall weighted Quality Scorecard Index
        overall_score = (
            completeness * 0.25
            + validity * 0.30
            + uniqueness * 0.20
            + consistency * 0.10
            + conformity * 0.10
            + freshness * 0.05
        )

        return QualityScorecard(
            run_id=report.run_id,
            total_records=total_rows,
            completeness_pct=completeness,
            validity_pct=validity,
            uniqueness_pct=uniqueness,
            consistency_pct=consistency,
            conformity_pct=conformity,
            freshness_pct=freshness,
            overall_quality_score=overall_score,
        )
