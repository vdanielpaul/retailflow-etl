"""Framework-agnostic adapter between canonical record dicts and the v1.0 transformation pipeline.

Design Principles
-----------------
* No Beam, Dataflow, or cloud-specific imports. This module is pure Python.
* The adapter invokes the three domain transformation functions directly:
    clean_dataframe → normalize_dataframe → enrich_sales_dataframe
  These are stateless, pure functions with no external dependencies.
* The TransformationEngine.transform_sales_feed() is intentionally NOT used here.
  It bundles stages 1–3 with stages 4–5 (surrogate key resolution and fact payload
  construction), which belong to Task 3.5. Calling the three functions directly
  provides the correct scope boundary without modification.
* Surrogate key resolution, dimension lookups, and MERGE operations belong to Task 3.5.

Transformation Scope (Task 3.4)
--------------------------------
  Stage 1 — Cleaning  : whitespace trimming, unicode normalization, NULL standardization
  Stage 2 — Normalization: email casing, code formatting, currency decimal precision
  Stage 3 — Enrichment: derived financial metrics
      gross_sales_amount  = quantity × unit_price
      net_sales_amount    = gross_sales_amount − discount_amount
      discount_percentage = (discount_amount / gross_sales_amount) × 100
      effective_unit_price = net_sales_amount / quantity
      transaction_line_total = net_sales_amount

Out of Scope (Task 3.5)
-----------------------
  Stage 4 — Surrogate key resolution (dimension lookups)
  Stage 5 — Fact payload construction (warehouse-ready schema)
  BigQuery writes
  MERGE statements

Preservation Statement
----------------------
The three transformation functions (clean_dataframe, normalize_dataframe,
enrich_sales_dataframe) are invoked without modification. Their logic is unchanged.
The adapter provides only the translation layer between Beam's single-element dict
representation and the DataFrame-based function interfaces.

Reusability
-----------
TransformationAdapter can be called from:
  - Apache Beam DoFns (primary use case in v2.0)
  - Local CLI pipeline (v1.0 compatibility)
  - Integration test harnesses
  - Future transformation CLI tools or data quality checks
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

from retailflow.transformation.cleaner import clean_dataframe
from retailflow.transformation.enricher import enrich_sales_dataframe
from retailflow.transformation.normalizer import normalize_dataframe

logger = logging.getLogger("retailflow.adapters.transformation")

# Transformer version tag embedded in transformed records and metrics.
# Update when transformation behaviour changes significantly.
TRANSFORMER_VERSION = "TransformationAdapter v1.0"

# Derived fields produced by enrich_sales_dataframe — used in output validation.
ENRICHED_FIELDS = frozenset({
    "gross_sales_amount",
    "net_sales_amount",
    "discount_percentage",
    "effective_unit_price",
    "transaction_line_total",
})


@dataclass
class TransformationResult:
    """Result produced by TransformationAdapter for a single canonical record.

    Attributes:
        success: True if all three transformation stages completed without error.
        transformed_record: The fully cleaned, normalized, and enriched record dict.
            None if success is False.
        error: Description of the failure if success is False. None otherwise.
        stage: The transformation stage that produced this result
            ('clean', 'normalize', 'enrich', or 'adapter').
        execution_time_ms: Wall-clock time for the three transformation stages in ms.
        transformation_timestamp: UTC ISO timestamp captured at adapter invocation.
        transformer_version: Identifies the adapter version for audit tracing.
    """

    success: bool
    transformed_record: Optional[Dict[str, Any]]
    error: Optional[str]
    stage: str
    execution_time_ms: float
    transformation_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    transformer_version: str = TRANSFORMER_VERSION


class TransformationAdapter:
    """Translates canonical record dicts through the v1.0 transformation pipeline.

    The adapter converts a single canonical dict into a minimal single-row
    pd.DataFrame, invokes the three domain transformation functions in sequence,
    and converts the result back to a dict for downstream Beam processing.

    This keeps the transformation functions unchanged while allowing them to
    operate on individual Beam elements rather than full-batch DataFrames.

    Usage
    -----
    Instantiate once (e.g., in a DoFn.setup() call) and reuse across many
    records. The transformation functions are stateless; construction is
    inexpensive and the same instance is safe to share within a single worker.

        adapter = TransformationAdapter()
        result = adapter.transform(canonical_dict)
        if result.success:
            yield result.transformed_record
        else:
            yield transformation_error_record(result)
    """

    def __init__(self) -> None:
        # The transformation functions are stateless module-level functions.
        # No initialization required. Adapter construction is cheap.
        logger.debug("TransformationAdapter initialised. version=%s", TRANSFORMER_VERSION)

    def transform(self, record: Dict[str, Any]) -> TransformationResult:
        """Apply the three-stage transformation pipeline to a single canonical record.

        Stages executed in order:
          1. clean_dataframe  — whitespace, unicode, NULL standardization
          2. normalize_dataframe — email/code formatting, currency precision
          3. enrich_sales_dataframe — derived financial metrics

        Any unexpected exception in any stage causes a TransformationResult with
        success=False and a descriptive error. The record is never partially applied.

        Args:
            record: Validated canonical sale dict from the validation stage.

        Returns:
            TransformationResult with the enriched record or failure context.
        """
        transformation_timestamp = datetime.now(timezone.utc).isoformat()
        t_start = time.perf_counter()

        try:
            # Wrap the single record in a minimal DataFrame to satisfy the
            # transformation function interfaces. Same pattern as BusinessRuleAdapter.
            df = pd.DataFrame([record])
        except Exception as exc:  # noqa: BLE001
            return TransformationResult(
                success=False,
                transformed_record=None,
                error=f"AdapterError (DataFrame construction): {exc}",
                stage="adapter",
                execution_time_ms=0.0,
                transformation_timestamp=transformation_timestamp,
            )

        # -------------------------------------------------------------------------
        # Stage 1: Data Cleaning
        # -------------------------------------------------------------------------
        try:
            df = clean_dataframe(df)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Cleaning stage failed for transaction_id=%s: %s",
                record.get("transaction_id", "UNKNOWN"),
                exc,
            )
            return TransformationResult(
                success=False,
                transformed_record=None,
                error=f"CleaningError: {exc}",
                stage="clean",
                execution_time_ms=(time.perf_counter() - t_start) * 1000.0,
                transformation_timestamp=transformation_timestamp,
            )

        # -------------------------------------------------------------------------
        # Stage 2: Data Normalization
        # -------------------------------------------------------------------------
        try:
            df = normalize_dataframe(df)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Normalization stage failed for transaction_id=%s: %s",
                record.get("transaction_id", "UNKNOWN"),
                exc,
            )
            return TransformationResult(
                success=False,
                transformed_record=None,
                error=f"NormalizationError: {exc}",
                stage="normalize",
                execution_time_ms=(time.perf_counter() - t_start) * 1000.0,
                transformation_timestamp=transformation_timestamp,
            )

        # -------------------------------------------------------------------------
        # Stage 3: Business Metrics Enrichment
        # -------------------------------------------------------------------------
        try:
            df = enrich_sales_dataframe(df)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Enrichment stage failed for transaction_id=%s: %s",
                record.get("transaction_id", "UNKNOWN"),
                exc,
            )
            return TransformationResult(
                success=False,
                transformed_record=None,
                error=f"EnrichmentError: {exc}",
                stage="enrich",
                execution_time_ms=(time.perf_counter() - t_start) * 1000.0,
                transformation_timestamp=transformation_timestamp,
            )

        execution_time_ms = (time.perf_counter() - t_start) * 1000.0

        # Convert the single-row DataFrame back to a dict.
        # iloc[0] selects row 0; to_dict() produces the field map.
        transformed_record = df.iloc[0].to_dict()

        logger.debug(
            "Transformation complete. transaction_id=%s duration_ms=%.3f",
            transformed_record.get("transaction_id", "UNKNOWN"),
            execution_time_ms,
        )

        return TransformationResult(
            success=True,
            transformed_record=transformed_record,
            error=None,
            stage="enrich",
            execution_time_ms=execution_time_ms,
            transformation_timestamp=transformation_timestamp,
        )
