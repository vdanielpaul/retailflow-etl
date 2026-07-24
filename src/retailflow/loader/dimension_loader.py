"""Dimension loader executing SCD Type 1 upserts and delta inserts into warehouse dimension tables."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from retailflow.transformation.scd import SCD1Processor

logger = logging.getLogger(__name__)


class DimensionLoader:
    """Loader managing dimension inserts and SCD Type 1 attribute updates."""

    def load_store_dimension(self, cursor: Any, df: pd.DataFrame) -> tuple[int, int]:
        """Perform SCD Type 1 upsert for warehouse.dim_store.

        Returns:
            Tuple of (Inserted count, Updated count).
        """
        if df.empty or "store_id" not in df.columns:
            return 0, 0

        # Fetch existing store dimension snapshot
        cursor.execute("SELECT store_id, store_name, region, city, state FROM warehouse.dim_store;")
        rows = cursor.fetchall()
        existing_df = pd.DataFrame(rows, columns=["store_id", "store_name", "region", "city", "state"])

        processor = SCD1Processor(natural_key="store_id", tracked_attributes=["store_name", "region", "city", "state"])
        inserts_df, updates_df, metrics = processor.compute_scd1_delta(df, existing_df)

        # Execute Inserts
        if not inserts_df.empty:
            insert_sql = """
                INSERT INTO warehouse.dim_store (store_id, store_name, region, city, state)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (store_id) DO NOTHING;
            """
            data = [
                (r["store_id"], r["store_name"], r["region"], r["city"], r["state"])
                for _, r in inserts_df.iterrows()
            ]
            cursor.executemany(insert_sql, data)

        # Execute Updates (SCD Type 1)
        if not updates_df.empty:
            update_sql = """
                UPDATE warehouse.dim_store
                SET store_name = %s, region = %s, city = %s, state = %s, updated_at = CURRENT_TIMESTAMP
                WHERE store_id = %s;
            """
            data = [
                (r["store_name"], r["region"], r["city"], r["state"], r["store_id"])
                for _, r in updates_df.iterrows()
            ]
            cursor.executemany(update_sql, data)

        return metrics.rows_inserted, metrics.rows_changed

    def load_product_dimension(self, cursor: Any, df: pd.DataFrame) -> tuple[int, int]:
        """Perform SCD Type 1 upsert for warehouse.dim_product.

        Returns:
            Tuple of (Inserted count, Updated count).
        """
        if df.empty or "product_id" not in df.columns:
            return 0, 0

        cursor.execute("SELECT product_id, product_name, category, brand, unit_price FROM warehouse.dim_product;")
        rows = cursor.fetchall()
        existing_df = pd.DataFrame(rows, columns=["product_id", "product_name", "category", "brand", "unit_price"])

        processor = SCD1Processor(
            natural_key="product_id", tracked_attributes=["product_name", "category", "brand", "unit_price"]
        )
        inserts_df, updates_df, metrics = processor.compute_scd1_delta(df, existing_df)

        if not inserts_df.empty:
            insert_sql = """
                INSERT INTO warehouse.dim_product (product_id, product_name, category, brand, unit_price)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (product_id) DO NOTHING;
            """
            data = [
                (r["product_id"], r["product_name"], r["category"], r["brand"], r["unit_price"])
                for _, r in inserts_df.iterrows()
            ]
            cursor.executemany(insert_sql, data)

        if not updates_df.empty:
            update_sql = """
                UPDATE warehouse.dim_product
                SET product_name = %s, category = %s, brand = %s, unit_price = %s, updated_at = CURRENT_TIMESTAMP
                WHERE product_id = %s;
            """
            data = [
                (r["product_name"], r["category"], r["brand"], r["unit_price"], r["product_id"])
                for _, r in updates_df.iterrows()
            ]
            cursor.executemany(update_sql, data)

        return metrics.rows_inserted, metrics.rows_changed
