"""Data validation engine orchestrator and per-run bad record quarantine manager."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

from retailflow.models.validation import ValidationReport, ValidationResult
from retailflow.pipeline.context import PipelineContext
from retailflow.validation.base import BaseValidator
from retailflow.validation.validators import (
    BusinessRuleValidator,
    DataTypeValidator,
    DuplicateValidator,
    FileValidator,
    SchemaValidator,
)


class ValidationEngine:
    """Orchestrator for running modular data quality validators and quarantining bad records."""

    def __init__(self, validators: list[BaseValidator] | None = None) -> None:
        self.validators = validators or [
            FileValidator(),
            SchemaValidator(),
            DataTypeValidator(),
            BusinessRuleValidator(),
            DuplicateValidator(),
        ]

    def validate_feed(
        self, df: pd.DataFrame, context: PipelineContext
    ) -> tuple[pd.DataFrame, ValidationReport]:
        """Execute validation suite against raw feed DataFrame.

        Args:
            df: Raw input DataFrame.
            context: Shared pipeline context.

        Returns:
            Tuple of (Clean DataFrame with valid rows, ValidationReport object).
        """
        start_time = time.perf_counter()
        results: list[ValidationResult] = []
        all_failed_indices: set[int] = set()
        top_reasons: dict[str, int] = {}

        # 1. Run each validator sequentially
        for validator in self.validators:
            result = validator.validate(df, context)
            results.append(result)
            all_failed_indices.update(result.failed_row_indices)

            # Aggregate failure reasons
            for reason, count in result.error_summary.items():
                top_reasons[reason] = top_reasons.get(reason, 0) + count

        # 2. Separate clean vs. invalid rows
        failed_list = sorted(all_failed_indices)
        if failed_list:
            clean_df = df.drop(index=failed_list).reset_index(drop=True)
            bad_df = df.loc[failed_list].copy()
        else:
            clean_df = df.copy()
            bad_df = pd.DataFrame()

        total_rows = len(df)
        failed_rows_count = len(failed_list)
        passed_rows_count = total_rows - failed_rows_count
        failure_rate = (failed_rows_count / total_rows * 100.0) if total_rows > 0 else 0.0
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Check if validation passed overall
        is_valid = failed_rows_count == 0 or failure_rate <= context.configuration.pipeline.max_error_percentage

        report = ValidationReport(
            run_id=context.run_id,
            total_rows=total_rows,
            passed_rows=passed_rows_count,
            failed_rows=failed_rows_count,
            failure_rate_pct=failure_rate,
            execution_time_ms=duration_ms,
            is_valid=is_valid,
            validator_results=results,
            top_failure_reasons=top_reasons,
        )

        # 3. Quarantine bad records if invalid rows exist
        if not bad_df.empty:
            self._quarantine_records(bad_df, report, context)

        # Record metrics
        context.metrics.record_rows(
            read=total_rows,
            valid=passed_rows_count,
            invalid=failed_rows_count,
        )
        context.metrics.record_stage_time("VALIDATION", duration_ms)

        return clean_df, report

    def _quarantine_records(
        self, bad_df: pd.DataFrame, report: ValidationReport, context: PipelineContext
    ) -> Path:
        """Quarantine bad records and report artifacts into data/bad_records/<run_id>/."""
        base_quarantine_dir = Path(context.configuration.paths.bad_records_dir)
        run_quarantine_dir = base_quarantine_dir / context.run_id
        run_quarantine_dir.mkdir(parents=True, exist_ok=True)

        # 1. Save invalid rows as CSV
        invalid_csv_path = run_quarantine_dir / "invalid_rows.csv"
        bad_df.to_csv(invalid_csv_path, index=False)

        # 2. Save validation report JSON
        report_json_path = run_quarantine_dir / "validation_report.json"
        report_json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")

        # 3. Save summary JSON
        summary_json_path = run_quarantine_dir / "summary.json"
        summary_data = {
            "run_id": context.run_id,
            "batch_id": context.batch_id,
            "source_file": str(context.source_file) if context.source_file else "N/A",
            "quarantined_rows_count": len(bad_df),
            "top_failure_reasons": report.top_failure_reasons,
            "quarantined_at": pd.Timestamp.now(tz="UTC").isoformat(),
        }
        summary_json_path.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")

        context.logger.warning(
            f"Quarantined {len(bad_df)} invalid rows to {run_quarantine_dir}"
        )
        return run_quarantine_dir
