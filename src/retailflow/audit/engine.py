"""Audit engine orchestrating lifecycle timeline aggregation and execution summaries."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from retailflow.audit.models import PipelineExecutionSummary
from retailflow.audit.service import AuditService
from retailflow.pipeline.context import PipelineContext


class AuditEngine:
    """Orchestrator for managing pipeline execution audit timelines and summaries."""

    def __init__(self, audit_service: AuditService | None = None) -> None:
        self.audit_service = audit_service or AuditService()

    def build_execution_summary(
        self, context: PipelineContext, start_time: float, status: str = "SUCCESS"
    ) -> PipelineExecutionSummary:
        """Construct PipelineExecutionSummary object for dashboard reporting and API queries."""
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        timeline = [evt.to_dict() for evt in self.audit_service.events if evt.run_id == context.run_id]

        rows_read = context.metrics.rows_read
        rows_loaded = context.metrics.rows_loaded
        rows_rejected = context.metrics.rows_invalid

        throughput = (rows_loaded / (elapsed_ms / 1000.0)) if elapsed_ms > 0 else 0.0
        warnings_count = sum(1 for e in self.audit_service.events if e.severity.value == "WARNING")
        errors_count = sum(1 for e in self.audit_service.events if e.severity.value in ("ERROR", "CRITICAL"))

        is_reconciled = (rows_read == rows_loaded + rows_rejected) if rows_read > 0 else True

        return PipelineExecutionSummary(
            pipeline_name=context.pipeline_name,
            environment=context.environment,
            run_id=context.run_id,
            batch_id=context.batch_id,
            start_time=context.started_at.isoformat(),
            end_time=datetime.now(timezone.utc).isoformat(),
            duration_ms=elapsed_ms,
            files_processed=1 if context.source_file else 0,
            rows_processed=rows_read,
            rows_loaded=rows_loaded,
            rows_rejected=rows_rejected,
            throughput_rows_per_sec=throughput,
            warnings_count=warnings_count,
            errors_count=errors_count,
            final_status=status,
            reconciliation_status="RECONCILED" if is_reconciled else "UNRECONCILED",
            timeline=timeline,
        )
