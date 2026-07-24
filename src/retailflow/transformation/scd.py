"""Slowly Changing Dimension (SCD Type 1) comparison and delta detection engine."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class SCD1Metrics:
    """Metrics tracking outcome of SCD Type 1 comparison."""

    rows_compared: int = 0
    rows_changed: int = 0
    rows_inserted: int = 0
    rows_unchanged: int = 0


class SCD1Processor:
    """SCD Type 1 processor comparing incoming dimension attributes against target warehouse records."""

    def __init__(self, natural_key: str, tracked_attributes: list[str]) -> None:
        self.natural_key = natural_key
        self.tracked_attributes = tracked_attributes

    def compute_scd1_delta(
        self, incoming_df: pd.DataFrame, existing_df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame, SCD1Metrics]:
        """Compare incoming dimension records against existing warehouse dimension table.

        Args:
            incoming_df: Fresh normalized dimension DataFrame.
            existing_df: Current warehouse dimension table snapshot.

        Returns:
            Tuple of (Insert DataFrame, Update DataFrame, SCD1Metrics).
        """
        metrics = SCD1Metrics(rows_compared=len(incoming_df))

        if existing_df.empty or self.natural_key not in existing_df.columns:
            metrics.rows_inserted = len(incoming_df)
            return incoming_df, pd.DataFrame(columns=incoming_df.columns), metrics

        # 1. Identify New Inserts (Natural Key not in existing)
        merged = incoming_df.merge(
            existing_df[[self.natural_key] + self.tracked_attributes],
            on=self.natural_key,
            how="left",
            suffixes=("", "_exist"),
        )

        insert_mask = merged[f"{self.tracked_attributes[0]}_exist"].isna()
        inserts_df = incoming_df[insert_mask].copy()
        metrics.rows_inserted = len(inserts_df)

        # 2. Identify Updates (Natural Key exists AND at least one tracked attribute differs)
        existing_matches = merged[~insert_mask].copy()
        if existing_matches.empty:
            metrics.rows_unchanged = 0
            metrics.rows_changed = 0
            return inserts_df, pd.DataFrame(columns=incoming_df.columns), metrics

        changed_mask = pd.Series(False, index=existing_matches.index)
        for attr in self.tracked_attributes:
            if attr in existing_matches.columns and f"{attr}_exist" in existing_matches.columns:
                attribute_diff = (
                    existing_matches[attr].astype(str) != existing_matches[f"{attr}_exist"].astype(str)
                )
                changed_mask = changed_mask | attribute_diff

        updates_df = incoming_df.loc[existing_matches.index[changed_mask]].copy()
        metrics.rows_changed = len(updates_df)
        metrics.rows_unchanged = len(existing_matches) - metrics.rows_changed

        return inserts_df, updates_df, metrics
