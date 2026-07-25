"""Framework-agnostic adapter between canonical record dicts and the v1.0 BusinessRuleValidator.

Design Principles
-----------------
* No Beam, Dataflow, or cloud-specific imports. This module is pure Python.
* The BusinessRuleValidator is the single source of truth for business rules.
  Rules are never duplicated or re-expressed in this adapter.
* The adapter translates between the Beam element representation (a dict) and
  the validator interface (pd.DataFrame). It is the only place this translation
  occurs.
* The validator is stateless. A single shared instance is safe to reuse across
  many records. If mutable state is introduced into BusinessRuleValidator in the
  future, the lifecycle decision in ValidateSaleRecordFn.setup() must be revisited.

Future Validation Strategy
--------------------------
If new business rules are required, they must be added to BusinessRuleValidator
(or a new companion validator). Rules must never be implemented directly inside
Beam DoFns or pipeline transforms. This preserves a single source of truth for
business validation and keeps the adapter layer stable.

Reusability
-----------
BusinessRuleAdapter can be called from:
  - Apache Beam DoFns (primary use case in v2.0)
  - Local CLI pipeline (v1.0 compatibility)
  - Integration test harnesses
  - Future Flink or Spark adapters
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd

from retailflow.models.validation import ValidationStatus
from retailflow.validation.validators import BusinessRuleValidator

logger = logging.getLogger("retailflow.adapters.business_rule")

# Validator version tag embedded in quarantine records.
# Update this string when BusinessRuleValidator behavior changes significantly.
VALIDATOR_VERSION = "BusinessRuleValidator v1.0"


@dataclass
class ValidationCheckResult:
    """Result produced by the BusinessRuleAdapter for a single canonical record.

    Attributes:
        valid: True if the record passed all business rule checks.
        errors: Collected error descriptions — all failures are captured, not
            just the first. A blank list indicates a passing record.
        canonical_record: The original canonical dict, preserved for routing
            and quarantine output without requiring re-serialization.
        validation_timestamp: UTC ISO timestamp captured at validation time.
            Useful for diagnostics, audit logging, and quarantine record tracing.
    """

    valid: bool
    errors: List[str]
    canonical_record: Dict[str, Any]
    validation_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class BusinessRuleAdapter:
    """Translates canonical record dicts into the BusinessRuleValidator interface.

    The adapter converts a single canonical dict into a minimal single-row
    pd.DataFrame, invokes the existing BusinessRuleValidator, and translates
    the ValidationResult back into a ValidationCheckResult.

    This keeps the validator interface unchanged while allowing it to operate
    on individual Beam elements rather than full-batch DataFrames.

    Usage
    -----
    Instantiate once (e.g., in a DoFn.setup() call) and reuse across many
    records. The validator instance is stateless; construction is inexpensive
    and the same instance is safe to share within a single worker.

        adapter = BusinessRuleAdapter()
        result = adapter.validate(canonical_dict)
        if result.valid:
            yield result.canonical_record
        else:
            yield quarantine_record(result)
    """

    def __init__(self) -> None:
        # Instantiated once per adapter instance.
        # The validator is stateless — if that assumption changes, this must
        # be revisited and the DoFn lifecycle updated accordingly.
        self._validator = BusinessRuleValidator()
        logger.debug("BusinessRuleAdapter initialised with %s", VALIDATOR_VERSION)

    def validate(self, record: Dict[str, Any]) -> ValidationCheckResult:
        """Validate a single canonical record dict against business rules.

        All failures are collected before returning. The record is never
        short-circuited on the first failure — this allows data quality
        investigations to see the complete failure profile per record.

        Args:
            record: Canonical sale dict produced by ParseAndCanonicalizeCsvFn.

        Returns:
            ValidationCheckResult with valid flag, collected errors, and the
            original record.
        """
        validation_timestamp = datetime.now(timezone.utc).isoformat()

        try:
            # Wrap the single record in a minimal DataFrame to satisfy the
            # validator interface. orient="index" creates one row from the dict.
            df = pd.DataFrame([record])

            # Invoke the existing validator — context is not required because
            # BusinessRuleValidator does not access any PipelineContext fields.
            result = self._validator.validate(df)

        except Exception as exc:  # noqa: BLE001
            # Defensive fallback: if DataFrame construction or validator
            # invocation raises unexpectedly, treat the record as invalid and
            # surface the technical error for investigation.
            logger.error(
                "Unexpected error during BusinessRuleAdapter.validate(): %s", exc
            )
            return ValidationCheckResult(
                valid=False,
                errors=[f"AdapterError: {exc}"],
                canonical_record=record,
                validation_timestamp=validation_timestamp,
            )

        # Collect all error codes from the validation result summary.
        # error_summary maps error-code strings to occurrence counts.
        # We expand them into human-readable messages for quarantine records.
        errors: List[str] = []
        if result.status == ValidationStatus.FAILED:
            for error_code, count in result.error_summary.items():
                errors.append(f"{error_code} (affected rows in batch: {count})")

        is_valid = result.status == ValidationStatus.PASSED

        if not is_valid:
            logger.debug(
                "Record failed validation. transaction_id=%s errors=%s",
                record.get("transaction_id", "UNKNOWN"),
                errors,
            )

        return ValidationCheckResult(
            valid=is_valid,
            errors=errors,
            canonical_record=record,
            validation_timestamp=validation_timestamp,
        )
