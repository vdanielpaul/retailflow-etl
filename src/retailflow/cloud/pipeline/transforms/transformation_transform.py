"""Beam DoFn for the three-stage transformation of verified canonical sale records.

This transform is the only component in the transformation stage that imports
Apache Beam. Its sole responsibility is:

  1. Receive a verified canonical sale dict from the upstream validation stage.
  2. Delegate entirely to TransformationAdapter (which invokes the three
     domain transformation functions: clean, normalize, enrich).
  3. Route the result to the correct output — main output for successfully
     transformed records, TAG_TRANSFORM_ERROR for records that fail any stage.

Business logic lives in the transformation domain functions.
Translation lives in TransformationAdapter.
Orchestration lives here.

Adapter Lifecycle
-----------------
The TransformationAdapter is constructed once per worker in setup(), not once
per element. The transformation functions are stateless — this is safe and
amortises object allocation cost across the full bundle. If mutable state is
introduced in the future, this lifecycle decision must be revisited.

Scope Boundary (Task 3.4)
--------------------------
This transform applies stages 1–3 only:
  Stage 1 — Cleaning
  Stage 2 — Normalization
  Stage 3 — Enrichment (derived financial metrics)

Surrogate key resolution, dimension lookups, and warehouse payload construction
(stages 4–5) belong to Task 3.5 and must not be added here.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Generator, Union

import apache_beam as beam

from retailflow.cloud.pipeline.adapters.transformation_adapter import (
    TRANSFORMER_VERSION,
    TransformationAdapter,
)

logger = logging.getLogger("retailflow.transforms.transformation")

# Side-output tag for records that fail transformation.
TAG_TRANSFORM_ERROR = "transform_errors"


class ApplyTransformationFn(beam.DoFn):
    """Routes verified canonical dicts through the three-stage transformation pipeline.

    Verified records pass to the main output as enriched dicts.
    Records that fail any transformation stage are serialised into an error dict
    and routed to TAG_TRANSFORM_ERROR for GCS quarantine.

    The transformation error dict schema is:
        correlation_id      -- pipeline trace identifier
        run_id              -- pipeline run identifier
        filename            -- source GCS path
        failed_stage        -- 'clean', 'normalize', 'enrich', or 'adapter'
        error               -- failure description
        original_record     -- the canonical dict that failed
        failed_at           -- UTC ISO timestamp
        transformer_version -- e.g. "TransformationAdapter v1.0"

    Enriched record additions (produced by enrich_sales_dataframe):
        gross_sales_amount
        net_sales_amount
        discount_percentage
        effective_unit_price
        transaction_line_total
    """

    def __init__(
        self,
        correlation_id: str,
        run_id: str,
        filename: str,
    ) -> None:
        """Initialise with pipeline-level trace metadata.

        Args:
            correlation_id: Unique trace ID for this pipeline invocation.
            run_id: Unique run identifier for audit purposes.
            filename: Source GCS path being processed.
        """
        self._correlation_id = correlation_id
        self._run_id = run_id
        self._filename = filename
        self._adapter: TransformationAdapter  # assigned in setup()

    def setup(self) -> None:
        """Initialise the adapter once per worker, not once per element.

        TransformationAdapter wraps stateless functions. Construction here
        amortises any future initialization overhead across the full bundle.
        """
        self._adapter = TransformationAdapter()
        logger.info(
            "ApplyTransformationFn worker ready. correlation_id=%s transformer=%s",
            self._correlation_id,
            TRANSFORMER_VERSION,
        )

    def process(
        self,
        element: Dict[str, Any],
    ) -> Generator[Union[Dict[str, Any], beam.pvalue.TaggedOutput], None, None]:
        """Apply the transformation pipeline to a single verified canonical dict.

        Args:
            element: Verified canonical sale dict from ValidateSaleRecordFn.

        Yields:
            Enriched record dicts to main output.
            Transformation error dicts (JSON strings) to TAG_TRANSFORM_ERROR.
        """
        result = self._adapter.transform(element)

        if result.success:
            yield result.transformed_record
        else:
            error_record = self._build_error_record(element, result)
            logger.warning(
                "Transformation failed. transaction_id=%s stage=%s error=%s",
                element.get("transaction_id", "UNKNOWN"),
                result.stage,
                result.error,
            )
            yield beam.pvalue.TaggedOutput(TAG_TRANSFORM_ERROR, error_record)

    def _build_error_record(self, element: Dict[str, Any], result) -> str:
        """Serialise a transformation failure into the error JSONL format.

        Returns a JSON string so the record is ready for beam.io.WriteToText
        without a further serialisation step in the pipeline graph.

        Args:
            element: The original canonical dict that failed.
            result: The TransformationResult containing failure context.

        Returns:
            JSON-serialised transformation error record string.
        """
        error_entry = {
            "correlation_id": self._correlation_id,
            "run_id": self._run_id,
            "filename": self._filename,
            "failed_stage": result.stage,
            "error": result.error,
            "original_record": element,
            "failed_at": result.transformation_timestamp,
            "transformer_version": TRANSFORMER_VERSION,
        }
        return json.dumps(error_entry, default=str)
