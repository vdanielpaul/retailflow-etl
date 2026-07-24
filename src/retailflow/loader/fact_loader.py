"""Fact table loader executing chunked batch loading into warehouse.fact_sales."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from retailflow.loader.bulk import bulk_load_dataframe
from retailflow.models.loader import LoadStrategy

logger = logging.getLogger(__name__)

FACT_COLUMNS = [
    "transaction_id",
    "date_sk",
    "customer_sk",
    "product_sk",
    "store_sk",
    "employee_sk",
    "transaction_time",
    "quantity",
    "unit_price",
    "discount_amount",
    "net_sales_amount",
    "audit_run_id",
]


class FactLoader:
    """Loader executing bulk loading into warehouse.fact_sales in configurable batch sizes."""

    def load_fact_sales(
        self,
        cursor: Any,
        df: pd.DataFrame,
        strategy: LoadStrategy = LoadStrategy.EXECUTE_VALUES,
        batch_size: int = 5000,
    ) -> tuple[int, int, float, list[float]]:
        """Load fact_sales DataFrame in chunked batches.

        Args:
            cursor: Active psycopg2 cursor.
            df: Fact sales DataFrame payload.
            strategy: Ingestion strategy (COPY, EXECUTE_VALUES, INSERT).
            batch_size: Page size per batch.

        Returns:
            Tuple of (Total facts loaded, Batches processed count, Total DB time ms, Batch durations list).
        """
        if df.empty:
            return 0, 0, 0.0, []

        total_rows = len(df)
        total_loaded = 0
        batches_count = 0
        total_db_time_ms = 0.0
        batch_durations: list[float] = []

        # Split DataFrame into chunked batches
        for i in range(0, total_rows, batch_size):
            chunk = df.iloc[i : i + batch_size]
            batches_count += 1

            rows_loaded, elapsed_ms = bulk_load_dataframe(
                cursor=cursor,
                df=chunk,
                table_name="warehouse.fact_sales",
                columns=FACT_COLUMNS,
                strategy=strategy,
                page_size=batch_size,
            )
            total_loaded += rows_loaded
            total_db_time_ms += elapsed_ms
            batch_durations.append(elapsed_ms)

            logger.debug(
                f"Batch {batches_count}: Loaded {rows_loaded} facts into warehouse.fact_sales in {elapsed_ms:.2f}ms"
            )

        return total_loaded, batches_count, total_db_time_ms, batch_durations
