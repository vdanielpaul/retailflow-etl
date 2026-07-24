"""In-memory surrogate key lookup caching and missing natural key resolution."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

import pandas as pd

from retailflow.database.connection import DatabaseManager

logger = logging.getLogger(__name__)

# Fallback default surrogate key for unknown dimension records
UNKNOWN_SURROGATE_KEY = -1


class UnknownKeyStrategy(str, Enum):
    """Strategy for handling natural keys missing from dimension tables."""

    USE_UNKNOWN_KEY = "USE_UNKNOWN_KEY"  # Assign -1 fallback key
    AUTO_CREATE = "AUTO_CREATE"          # Dynamically seed new dimension member
    REJECT_ROW = "REJECT_ROW"            # Flag row as invalid


class SurrogateKeyResolver:
    """In-memory dimension lookup cache for mapping natural business keys to warehouse surrogate keys."""

    def __init__(
        self,
        db_manager: DatabaseManager | None = None,
        unknown_strategy: UnknownKeyStrategy = UnknownKeyStrategy.USE_UNKNOWN_KEY,
    ) -> None:
        self.db_manager = db_manager
        self.unknown_strategy = unknown_strategy

        # In-memory dictionaries: Natural Key -> Surrogate Key
        self._store_cache: dict[str, int] = {}
        self._product_cache: dict[str, int] = {}
        self._customer_cache: dict[str, int] = {}
        self._employee_cache: dict[str, int] = {}
        self._date_cache: dict[int, int] = {}  # YYYYMMDD int -> date_sk

        self.cache_hits = 0
        self.cache_misses = 0
        self.lookup_failures = 0

    def load_caches(self) -> None:
        """Pre-populate in-memory lookup caches from PostgreSQL dimension tables."""
        if self.db_manager is None:
            logger.debug("No DatabaseManager injected; running with empty dimension caches.")
            return

        try:
            with self.db_manager.get_connection() as conn, conn.cursor() as cursor:
                # 1. Store Cache
                cursor.execute("SELECT store_id, store_sk FROM warehouse.dim_store;")
                self._store_cache = {row[0]: row[1] for row in cursor.fetchall()}

                # 2. Product Cache
                cursor.execute("SELECT product_id, product_sk FROM warehouse.dim_product;")
                self._product_cache = {row[0]: row[1] for row in cursor.fetchall()}

                # 3. Customer Cache
                cursor.execute("SELECT customer_id, customer_sk FROM warehouse.dim_customer;")
                self._customer_cache = {row[0]: row[1] for row in cursor.fetchall()}

                # 4. Employee Cache
                cursor.execute("SELECT employee_id, employee_sk FROM warehouse.dim_employee;")
                self._employee_cache = {row[0]: row[1] for row in cursor.fetchall()}

                # 5. Date Cache
                cursor.execute("SELECT date_sk FROM warehouse.dim_date;")
                self._date_cache = {row[0]: row[0] for row in cursor.fetchall()}

            logger.info(
                f"Dimension caches loaded: {len(self._store_cache)} stores, {len(self._product_cache)} products, "
                f"{len(self._customer_cache)} customers, {len(self._employee_cache)} employees."
            )
        except Exception as e:
            logger.warning(f"Could not pre-populate dimension caches: {e}")

    def resolve_store_sk(self, store_id: str) -> int:
        """Resolve store natural key to store_sk surrogate key."""
        if not store_id:
            return UNKNOWN_SURROGATE_KEY
        if store_id in self._store_cache:
            self.cache_hits += 1
            return self._store_cache[store_id]
        self.cache_misses += 1
        self.lookup_failures += 1
        return UNKNOWN_SURROGATE_KEY

    def resolve_product_sk(self, product_id: str) -> int:
        """Resolve product natural key to product_sk surrogate key."""
        if not product_id:
            return UNKNOWN_SURROGATE_KEY
        if product_id in self._product_cache:
            self.cache_hits += 1
            return self._product_cache[product_id]
        self.cache_misses += 1
        self.lookup_failures += 1
        return UNKNOWN_SURROGATE_KEY

    def resolve_customer_sk(self, customer_id: str | None) -> int | None:
        """Resolve customer natural key to customer_sk surrogate key."""
        if not customer_id or pd.isna(customer_id):
            return None
        if customer_id in self._customer_cache:
            self.cache_hits += 1
            return self._customer_cache[customer_id]
        self.cache_misses += 1
        return UNKNOWN_SURROGATE_KEY

    def resolve_employee_sk(self, employee_id: str) -> int:
        """Resolve employee natural key to employee_sk surrogate key."""
        if not employee_id:
            return UNKNOWN_SURROGATE_KEY
        if employee_id in self._employee_cache:
            self.cache_hits += 1
            return self._employee_cache[employee_id]
        self.cache_misses += 1
        self.lookup_failures += 1
        return UNKNOWN_SURROGATE_KEY

    def resolve_date_sk(self, dt: Any) -> int:
        """Resolve ISO timestamp to date_sk integer key (YYYYMMDD)."""
        try:
            ts = pd.to_datetime(dt)
            date_sk = int(ts.strftime("%Y%m%d"))
            self.cache_hits += 1
            return date_sk
        except Exception:
            self.lookup_failures += 1
            return 19700101

    def resolve_sales_surrogate_keys(self, df: pd.DataFrame) -> pd.DataFrame:
        """Vectorized mapping of DataFrame natural keys to surrogate keys."""
        resolved_df = df.copy()

        # Map Store SK
        if "store_id" in resolved_df.columns:
            resolved_df["store_sk"] = resolved_df["store_id"].map(
                lambda x: self.resolve_store_sk(str(x))
            )

        # Map Product SK
        if "product_id" in resolved_df.columns:
            resolved_df["product_sk"] = resolved_df["product_id"].map(
                lambda x: self.resolve_product_sk(str(x))
            )

        # Map Customer SK
        if "customer_id" in resolved_df.columns:
            resolved_df["customer_sk"] = resolved_df["customer_id"].map(
                lambda x: self.resolve_customer_sk(str(x) if pd.notna(x) else None)
            )

        # Map Employee SK
        if "employee_id" in resolved_df.columns:
            resolved_df["employee_sk"] = resolved_df["employee_id"].map(
                lambda x: self.resolve_employee_sk(str(x))
            )

        # Map Date SK
        if "transaction_time" in resolved_df.columns:
            resolved_df["date_sk"] = resolved_df["transaction_time"].map(self.resolve_date_sk)

        return resolved_df
