"""Beam DoFn for business rule validation of canonical sale records.

This transform is the only component in the validation stage that imports
Apache Beam. Its sole responsibility is:

  1. Receive a canonical sale dict from the upstream parse stage.
  2. Delegate entirely to BusinessRuleAdapter (which delegates to
     BusinessRuleValidator).
  3. Route the result to the correct output — main output for valid records,
     TAG_INVALID for records that fail any business rule.

Business logic lives in BusinessRuleValidator.
Translation lives in BusinessRuleAdapter.
Orchestration lives here.

Validator Lifecycle
-------------------
The BusinessRuleAdapter (and therefore BusinessRuleValidator) is constructed
once per worker in setup(), not once per element. This amortises object
allocation cost across the full bundle. The validator is stateless — if
mutable state is introduced into BusinessRuleValidator in the future, this
lifecycle decision must be revisited and the DoFn refactored accordingly.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Generator, Union

import apache_beam as beam

from retailflow.cloud.pipeline.adapters.business_rule_adapter import (
    VALIDATOR_VERSION,
    BusinessRuleAdapter,
)

logger = logging.getLogger("retailflow.transforms.validation")

# Side-output tag for records that fail business rule validation.
TAG_INVALID = "invalid_records"


class ValidateSaleRecordFn(beam.DoFn):
    """Routes canonical sale dicts through BusinessRuleValidator via adapter.

    Valid records pass to the main output.
    Invalid records are serialised into a quarantine dict and routed to
    TAG_INVALID, where pipeline.py writes them to GCS as JSONL.

    The quarantine dict schema is:
        correlation_id    -- pipeline trace identifier
        run_id            -- pipeline run identifier
        filename          -- source GCS path
        row_number        -- element position (0 if not tracked)
        validation_errors -- all failure descriptions collected (not fail-fast)
        original_record   -- the canonical dict that failed
        quarantined_at    -- UTC ISO timestamp
        validator_version -- e.g. "BusinessRuleValidator v1.0"

    This schema allows operational teams to:
        - Trace failures back to a specific pipeline run
        - Identify the source file and approximate row position
        - Understand all validation failures on a single record
        - Know which validator version produced the quarantine entry
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
        self._adapter: BusinessRuleAdapter  # assigned in setup()

    def setup(self) -> None:
        """Initialise the adapter once per worker, not once per element.

        Constructing BusinessRuleAdapter (and therefore BusinessRuleValidator)
        here avoids per-element object allocation overhead. This is safe because
        the validator is stateless. If that assumption changes, this method must
        be revisited.
        """
        self._adapter = BusinessRuleAdapter()
        logger.info(
            "ValidateSaleRecordFn worker ready. correlation_id=%s validator=%s",
            self._correlation_id,
            VALIDATOR_VERSION,
        )

    def process(
        self,
        element: Dict[str, Any],
    ) -> Generator[Union[Dict[str, Any], beam.pvalue.TaggedOutput], None, None]:
        """Validate a single canonical sale dict.

        Args:
            element: Canonical sale dict from ParseAndCanonicalizeCsvFn.

        Yields:
            Valid records to main output.
            Quarantine dicts to TAG_INVALID side output.
        """
        result = self._adapter.validate(element)

        if result.valid:
            yield element
        else:
            quarantine_record = self._build_quarantine_record(
                element, result.errors, result.validation_timestamp
            )
            logger.debug(
                "Record quarantined. transaction_id=%s errors=%s",
                element.get("transaction_id", "UNKNOWN"),
                result.errors,
            )
            yield beam.pvalue.TaggedOutput(TAG_INVALID, quarantine_record)

    def _build_quarantine_record(
        self,
        element: Dict[str, Any],
        errors: list,
        validation_timestamp: str,
    ) -> str:
        """Serialise a failed record into the quarantine JSONL format.

        Returns a JSON string so the record is ready for beam.io.WriteToText
        without a further serialisation step in the pipeline graph.

        Args:
            element: The original canonical dict.
            errors: All collected validation error descriptions.
            validation_timestamp: UTC ISO timestamp from the adapter result.

        Returns:
            JSON-serialised quarantine record string.
        """
        quarantine = {
            "correlation_id": self._correlation_id,
            "run_id": self._run_id,
            "filename": self._filename,
            "row_number": 0,  # Row-level position tracking is not available in streaming mode
            "validation_errors": errors,
            "original_record": element,
            "quarantined_at": validation_timestamp,
            "validator_version": VALIDATOR_VERSION,
        }
        return json.dumps(quarantine, default=str)
