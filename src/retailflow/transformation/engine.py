"""Transformation engine orchestrator assembling multi-stage cleaning, enrichment, and surrogate key resolution."""

from __future__ import annotations

import time

import pandas as pd

from retailflow.models.transformation import TransformationReport
from retailflow.pipeline.context import PipelineContext
from retailflow.transformation.cleaner import clean_dataframe
from retailflow.transformation.enricher import enrich_sales_dataframe
from retailflow.transformation.fact_builder import build_fact_sales_payload
from retailflow.transformation.normalizer import normalize_dataframe
from retailflow.transformation.surrogate_keys import SurrogateKeyResolver


class TransformationEngine:
    """Transformation engine orchestrating data cleaning, normalization, enrichment, and surrogate key mapping."""

    def __init__(self, key_resolver: SurrogateKeyResolver | None = None) -> None:
        self.key_resolver = key_resolver or SurrogateKeyResolver()

    def transform_sales_feed(
        self, df: pd.DataFrame, context: PipelineContext
    ) -> tuple[pd.DataFrame, TransformationReport]:
        """Execute full transformation lifecycle on validated sales DataFrame.

        Args:
            df: Clean validated input DataFrame.
            context: Shared pipeline execution context.

        Returns:
            Tuple of (Warehouse-ready fact_sales DataFrame, TransformationReport object).
        """
        start_time = time.perf_counter()
        warnings: list[str] = []
        rows_received = len(df)

        if df.empty:
            report = TransformationReport(
                run_id=context.run_id,
                rows_received=0,
                rows_transformed=0,
                rows_skipped=0,
                dimensions_updated=0,
                dimensions_inserted=0,
                facts_generated=0,
                lookup_failures=0,
                execution_time_ms=0.0,
            )
            return pd.DataFrame(), report

        # Stage 1: Data Cleaning (whitespace, unicode, NULL standardization)
        cleaned_df = clean_dataframe(df)

        # Stage 2: Data Normalization (lowercase emails, uppercase codes, decimal precision)
        normalized_df = normalize_dataframe(cleaned_df)

        # Stage 3: Business Metrics Enrichment (gross sales, net sales, discount %, effective unit price)
        enriched_df = enrich_sales_dataframe(normalized_df)

        # Stage 4: Surrogate Key Resolution (In-memory lookup caches)
        self.key_resolver.load_caches()
        resolved_df = self.key_resolver.resolve_sales_surrogate_keys(enriched_df)

        if self.key_resolver.lookup_failures > 0:
            warnings.append(
                f"Encountered {self.key_resolver.lookup_failures} dimension surrogate key lookup failures."
            )

        # Stage 5: Fact Sales Payload Construction
        fact_df = build_fact_sales_payload(resolved_df, context)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        rows_transformed = len(fact_df)

        report = TransformationReport(
            run_id=context.run_id,
            rows_received=rows_received,
            rows_transformed=rows_transformed,
            rows_skipped=rows_received - rows_transformed,
            dimensions_updated=0,
            dimensions_inserted=0,
            facts_generated=rows_transformed,
            lookup_failures=self.key_resolver.lookup_failures,
            execution_time_ms=duration_ms,
            warnings=warnings,
        )

        context.metrics.record_stage_time("TRANSFORMATION", duration_ms)

        return fact_df, report
