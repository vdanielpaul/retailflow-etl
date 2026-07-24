"""Warehouse loader engine orchestrating dimension loading, fact ingestion, watermark update, and reconciliation."""

from __future__ import annotations

import hashlib
import time
from typing import Any

import pandas as pd

from retailflow.loader.dimension_loader import DimensionLoader
from retailflow.loader.fact_loader import FactLoader
from retailflow.loader.transactional import TransactionCoordinator
from retailflow.models.loader import LoadReport, LoadStrategy, ReconciliationReport
from retailflow.pipeline.context import PipelineContext


class WarehouseLoaderEngine:
    """Warehouse loading orchestrator performing atomic dimension updates, fact loading, and reconciliation."""

    def __init__(
        self,
        dimension_loader: DimensionLoader | None = None,
        fact_loader: FactLoader | None = None,
        strategy: LoadStrategy = LoadStrategy.EXECUTE_VALUES,
    ) -> None:
        self.dimension_loader = dimension_loader or DimensionLoader()
        self.fact_loader = fact_loader or FactLoader()
        self.strategy = strategy

    def load_warehouse(
        self,
        fact_df: pd.DataFrame,
        context: PipelineContext,
        dim_store_df: pd.DataFrame | None = None,
        dim_product_df: pd.DataFrame | None = None,
    ) -> LoadReport:
        """Orchestrate atomic warehouse loading sequence.

        Args:
            fact_df: Clean fact sales DataFrame.
            context: Shared pipeline context.
            dim_store_df: Optional fresh store dimension records.
            dim_product_df: Optional fresh product dimension records.

        Returns:
            LoadReport object containing load metrics and reconciliation report.
        """
        start_time = time.perf_counter()
        coordinator = TransactionCoordinator(context.database)
        warnings: list[str] = []

        dim_inserted = 0
        dim_updated = 0
        dim_unchanged = 0
        facts_loaded = 0
        batches_processed = 0
        database_time_ms = 0.0
        batch_durations: list[float] = []

        with coordinator.atomic_transaction() as cursor:
            # 1. Load Store Dimension (SCD Type 1)
            if dim_store_df is not None and not dim_store_df.empty:
                s_ins, s_upd = self.dimension_loader.load_store_dimension(cursor, dim_store_df)
                dim_inserted += s_ins
                dim_updated += s_upd

            # 2. Load Product Dimension (SCD Type 1)
            if dim_product_df is not None and not dim_product_df.empty:
                p_ins, p_upd = self.dimension_loader.load_product_dimension(cursor, dim_product_df)
                dim_inserted += p_ins
                dim_updated += p_upd

            # 3. Bulk Load Fact Sales
            batch_size = context.configuration.pipeline.batch_size
            facts_loaded, batches_processed, db_time, batch_durations = self.fact_loader.load_fact_sales(
                cursor=cursor,
                df=fact_df,
                strategy=self.strategy,
                batch_size=batch_size,
            )
            database_time_ms += db_time

            # 4. Update Watermark Table
            if context.source_file is not None:
                self._register_watermark(cursor, context)

            # 5. Record Audit Log Entry
            audit_id = self._register_audit_log(cursor, context, facts_loaded)
            context.metadata["audit_run_id"] = audit_id

        total_duration_ms = (time.perf_counter() - start_time) * 1000.0
        avg_batch_time = (sum(batch_durations) / len(batch_durations)) if batch_durations else 0.0
        rows_per_sec = (facts_loaded / (total_duration_ms / 1000.0)) if total_duration_ms > 0 else 0.0

        # Generate End-to-End Reconciliation Summary
        rows_read = context.metrics.rows_read
        rows_valid = context.metrics.rows_valid
        rows_invalid = context.metrics.rows_invalid
        is_reconciled = (rows_read == rows_valid + rows_invalid) and (rows_valid == facts_loaded)

        reconciliation = ReconciliationReport(
            source_rows=rows_read,
            validated_rows=rows_valid,
            transformed_rows=len(fact_df),
            loaded_rows=facts_loaded,
            rejected_rows=rows_invalid,
            duplicate_rows=context.metrics.duplicate_rows,
            is_reconciled=is_reconciled,
        )

        context.metrics.record_rows(loaded=facts_loaded)
        context.metrics.record_stage_time("LOADING", total_duration_ms)

        return LoadReport(
            run_id=context.run_id,
            dimensions_inserted=dim_inserted,
            dimensions_updated=dim_updated,
            dimensions_unchanged=dim_unchanged,
            facts_loaded=facts_loaded,
            facts_rejected=rows_invalid,
            batches_processed=batches_processed,
            average_batch_time_ms=avg_batch_time,
            rows_per_second=rows_per_sec,
            database_time_ms=database_time_ms,
            rollback_count=coordinator.rollback_count,
            savepoint_rollbacks=coordinator.savepoint_rollbacks,
            reconciliation_summary=reconciliation,
            warnings=warnings,
        )

    def _register_watermark(self, cursor: Any, context: PipelineContext) -> None:
        """Register file hash and high watermark in metadata.etl_watermark table."""
        file_path = context.source_file
        if file_path is None or not file_path.exists():
            return

        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        sql = """
            INSERT INTO metadata.etl_watermark (source_file, file_hash, rows_processed, status)
            VALUES (%s, %s, %s, 'SUCCESS')
            ON CONFLICT (file_hash) DO UPDATE
            SET processed_at = CURRENT_TIMESTAMP, status = 'REPROCESSED';
        """
        cursor.execute(sql, (file_path.name, file_hash, context.metrics.rows_loaded))

    def _register_audit_log(self, cursor: Any, context: PipelineContext, rows_loaded: int) -> int:
        """Write execution metrics to metadata.etl_audit_log table."""
        sql = """
            INSERT INTO metadata.etl_audit_log (
                pipeline_run_id, batch_id, source_file, target_table,
                rows_read, rows_loaded, rows_rejected, status, execution_stage
            )
            VALUES (%s, %s, %s, 'warehouse.fact_sales', %s, %s, %s, 'SUCCESS', %s)
            RETURNING run_id;
        """
        source_name = context.source_file.name if context.source_file else "N/A"
        cursor.execute(
            sql,
            (
                context.run_id,
                context.batch_id,
                source_name,
                context.metrics.rows_read,
                rows_loaded,
                context.metrics.rows_invalid,
                context.execution_state,
            ),
        )
        row = cursor.fetchone()
        return row[0] if row else 0
