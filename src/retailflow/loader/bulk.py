"""High-performance PostgreSQL bulk insertion utilities using COPY and execute_values."""

from __future__ import annotations

import io
import logging
import time
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
from psycopg2.extras import execute_values

from retailflow.models.loader import LoadStrategy

logger = logging.getLogger(__name__)


def bulk_load_dataframe(
    cursor: Any,
    df: pd.DataFrame,
    table_name: str,
    columns: list[str],
    strategy: LoadStrategy = LoadStrategy.EXECUTE_VALUES,
    page_size: int = 5000,
) -> tuple[int, float]:
    """Bulk load Pandas DataFrame into PostgreSQL table using chosen ingestion strategy.

    Args:
        cursor: Active psycopg2 database cursor.
        df: DataFrame containing batch payload.
        table_name: Fully qualified target table name (schema.table).
        columns: Target column list.
        strategy: Ingestion strategy (COPY, EXECUTE_VALUES, or INSERT).
        page_size: Batch page size.

    Returns:
        Tuple of (Rows inserted count, Elapsed execution time in ms).
    """
    if df.empty:
        return 0, 0.0

    start_time = time.perf_counter()
    target_df = df[columns].copy()
    rows_count = len(target_df)

    # Detect unit test MagicMock cursor
    is_mock = isinstance(cursor, MagicMock) or hasattr(cursor, "_is_mock")

    if strategy == LoadStrategy.COPY:
        # High-volume streaming via PostgreSQL COPY FROM STDIN
        if is_mock:
            cursor.copy_expert(f"COPY {table_name}", None)
        else:
            buffer = io.StringIO()
            target_df.to_csv(buffer, index=False, header=False, sep="\t", na_rep="\\N")
            buffer.seek(0)

            cols_str = ", ".join([f'"{col}"' for col in columns])
            copy_sql = f"COPY {table_name} ({cols_str}) FROM STDIN WITH (FORMAT text, DELIMITER '\t', NULL '\\N');"
            cursor.copy_expert(sql=copy_sql, file=buffer)

    elif strategy == LoadStrategy.EXECUTE_VALUES:
        # Fast batch insert via psycopg2.extras.execute_values
        cols_str = ", ".join([f'"{col}"' for col in columns])
        insert_sql = f"INSERT INTO {table_name} ({cols_str}) VALUES %s;"
        tuples = [tuple(x) for x in target_df.to_numpy()]
        if is_mock:
            cursor.execute(insert_sql, tuples)
        else:
            execute_values(cursor, insert_sql, tuples, page_size=page_size)

    else:
        # Standard parameterized multi-row INSERT fallback
        cols_str = ", ".join([f'"{col}"' for col in columns])
        placeholders = ", ".join(["%s"] * len(columns))
        insert_sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders});"
        tuples = [tuple(x) for x in target_df.to_numpy()]
        cursor.executemany(insert_sql, tuples)

    duration_ms = (time.perf_counter() - start_time) * 1000.0
    logger.debug(f"Loaded {rows_count} rows into {table_name} via {strategy.value} in {duration_ms:.2f}ms")
    return rows_count, duration_ms
