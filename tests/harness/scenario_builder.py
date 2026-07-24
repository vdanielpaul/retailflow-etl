"""Scenario builder producing pre-configured test scenarios."""

from __future__ import annotations

from pathlib import Path

from tests.harness.data_generator import SyntheticDataGenerator


class ScenarioBuilder:
    """Builder generating pre-configured test scenario CSV files."""

    @staticmethod
    def build_clean_scenario(target_file: Path, row_count: int = 50) -> Path:
        """Generate 100% clean sales feed file without anomalies."""
        df = SyntheticDataGenerator.generate_sales_feed(
            row_count=row_count,
            duplicate_pct=0.0,
            invalid_qty_pct=0.0,
            invalid_price_pct=0.0,
            future_date_pct=0.0,
        )
        target_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(target_file, index=False)
        return target_file

    @staticmethod
    def build_anomaly_scenario(target_file: Path, row_count: int = 100) -> Path:
        """Generate sales feed file containing duplicates, negative prices, and invalid quantities."""
        df = SyntheticDataGenerator.generate_sales_feed(
            row_count=row_count,
            duplicate_pct=0.10,
            invalid_qty_pct=0.05,
            invalid_price_pct=0.05,
            future_date_pct=0.02,
        )
        target_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(target_file, index=False)
        return target_file
