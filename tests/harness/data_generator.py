"""Synthetic dataset generator creating realistic retail POS sales feeds."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import pandas as pd


class SyntheticDataGenerator:
    """Generates synthetic retail POS sales feed DataFrames with configurable anomalies."""

    @staticmethod
    def generate_sales_feed(
        row_count: int = 100,
        duplicate_pct: float = 0.05,
        invalid_qty_pct: float = 0.02,
        invalid_price_pct: float = 0.01,
        future_date_pct: float = 0.01,
    ) -> pd.DataFrame:
        """Generate synthetic sales feed DataFrame.

        Args:
            row_count: Target row count.
            duplicate_pct: Percentage of duplicate transaction IDs.
            invalid_qty_pct: Percentage of negative quantity rows.
            invalid_price_pct: Percentage of negative price rows.
            future_date_pct: Percentage of future date timestamps.

        Returns:
            Pandas DataFrame simulating raw POS store export.
        """
        rows = []
        base_time = datetime.now(timezone.utc) - timedelta(days=1)

        for i in range(1, row_count + 1):
            tx_id = f"TX-SYNTH-{i:06d}"
            store_id = f"STR-{(i % 5) + 1:03d}"
            product_id = f"PROD-{(i % 20) + 1:03d}"
            employee_id = f"EMP-{(i % 10) + 1:03d}"
            customer_id = f"CUST-{(i % 50) + 1:04d}" if i % 4 != 0 else None

            qty = random.randint(1, 10)
            price = round(random.uniform(5.0, 250.0), 2)
            discount = round(random.uniform(0.0, 15.0), 2) if i % 3 == 0 else 0.00
            ts = (base_time + timedelta(seconds=i * 10)).strftime("%Y-%m-%d %H:%M:%S")

            # Inject anomalies based on configured percentages
            if random.random() < invalid_qty_pct:
                qty = -random.randint(1, 5)
            if random.random() < invalid_price_pct:
                price = -10.00
            if random.random() < future_date_pct:
                ts = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")

            rows.append(
                {
                    "transaction_id": tx_id,
                    "store_id": store_id,
                    "product_id": product_id,
                    "employee_id": employee_id,
                    "customer_id": customer_id,
                    "quantity": qty,
                    "unit_price": price,
                    "discount_amount": discount,
                    "transaction_time": ts,
                }
            )

        df = pd.DataFrame(rows)

        # Inject duplicate rows if requested
        if duplicate_pct > 0 and len(df) > 5:
            dup_count = int(row_count * duplicate_pct)
            dup_rows = df.iloc[:dup_count].copy()
            df = pd.concat([df, dup_rows], ignore_index=True)

        return df
