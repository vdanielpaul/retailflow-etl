"""Modular Data Quality Validators utilizing vectorized Pandas operations."""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from retailflow.constants.constants import ErrorCode
from retailflow.models.validation import ValidationResult, ValidationSeverity, ValidationStatus
from retailflow.pipeline.context import PipelineContext
from retailflow.validation.base import BaseValidator


class FileValidator(BaseValidator):
    """Validator verifying file existence, non-emptiness, and file size bounds."""

    @property
    def validator_name(self) -> str:
        return "FileValidator"

    def validate(self, df: pd.DataFrame, context: PipelineContext) -> ValidationResult:
        start_time = time.perf_counter()
        source_file = context.source_file
        failed_count = 0
        summary: dict[str, int] = {}
        failed_indices: list[int] = []

        if source_file is not None:
            path = Path(source_file)
            if not path.exists():
                failed_count = 1
                summary[ErrorCode.ERR_FILE_NOT_FOUND.value] = 1
            elif path.stat().st_size == 0:
                failed_count = 1
                summary[ErrorCode.ERR_HEADER_MISMATCH.value] = 1

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        status = ValidationStatus.FAILED if failed_count > 0 else ValidationStatus.PASSED

        return ValidationResult(
            validator_name=self.validator_name,
            status=status,
            records_checked=len(df),
            records_failed=failed_count,
            severity=ValidationSeverity.CRITICAL,
            execution_time_ms=duration_ms,
            error_summary=summary,
            failed_row_indices=failed_indices,
        )


class SchemaValidator(BaseValidator):
    """Validator asserting presence of required schema columns."""

    def __init__(self, required_columns: list[str] | None = None) -> None:
        self.required_columns = required_columns or [
            "transaction_id",
            "store_id",
            "product_id",
            "employee_id",
            "quantity",
            "unit_price",
            "transaction_time",
        ]

    @property
    def validator_name(self) -> str:
        return "SchemaValidator"

    def validate(self, df: pd.DataFrame, context: PipelineContext) -> ValidationResult:
        start_time = time.perf_counter()
        missing_cols = [col for col in self.required_columns if col not in df.columns]

        failed_count = len(missing_cols)
        summary: dict[str, int] = {}
        if missing_cols:
            summary["VAL001_MISSING_COLUMN"] = failed_count

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        status = ValidationStatus.FAILED if missing_cols else ValidationStatus.PASSED

        return ValidationResult(
            validator_name=self.validator_name,
            status=status,
            records_checked=len(df),
            records_failed=failed_count,
            severity=ValidationSeverity.CRITICAL if missing_cols else ValidationSeverity.INFO,
            execution_time_ms=duration_ms,
            error_summary=summary,
        )


class DataTypeValidator(BaseValidator):
    """Vectorized validator coercing datatypes for quantity, price, and timestamp fields."""

    @property
    def validator_name(self) -> str:
        return "DataTypeValidator"

    def validate(self, df: pd.DataFrame, context: PipelineContext) -> ValidationResult:
        start_time = time.perf_counter()
        failed_indices: set[int] = set()
        summary: dict[str, int] = {}

        if df.empty:
            return ValidationResult(
                validator_name=self.validator_name,
                status=ValidationStatus.PASSED,
                records_checked=0,
                records_failed=0,
                execution_time_ms=0.0,
            )

        # 1. Numeric coercion for quantity
        if "quantity" in df.columns:
            qty_coerced = pd.to_numeric(df["quantity"], errors="coerce")
            invalid_qty_mask = qty_coerced.isna()
            bad_indices = set(df.index[invalid_qty_mask])
            failed_indices.update(bad_indices)
            if bad_indices:
                summary["VAL002_INVALID_DATATYPE_QTY"] = len(bad_indices)

        # 2. Numeric coercion for unit_price
        if "unit_price" in df.columns:
            price_coerced = pd.to_numeric(df["unit_price"], errors="coerce")
            invalid_price_mask = price_coerced.isna()
            bad_indices = set(df.index[invalid_price_mask])
            failed_indices.update(bad_indices)
            if bad_indices:
                summary["VAL002_INVALID_DATATYPE_PRICE"] = len(bad_indices)

        # 3. Timestamp coercion for transaction_time
        if "transaction_time" in df.columns:
            time_coerced = pd.to_datetime(df["transaction_time"], errors="coerce")
            invalid_time_mask = time_coerced.isna()
            bad_indices = set(df.index[invalid_time_mask])
            failed_indices.update(bad_indices)
            if bad_indices:
                summary["VAL002_INVALID_DATATYPE_TIME"] = len(bad_indices)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        status = ValidationStatus.FAILED if failed_indices else ValidationStatus.PASSED

        return ValidationResult(
            validator_name=self.validator_name,
            status=status,
            records_checked=len(df),
            records_failed=len(failed_indices),
            severity=ValidationSeverity.ERROR,
            execution_time_ms=duration_ms,
            error_summary=summary,
            failed_row_indices=sorted(failed_indices),
        )


class BusinessRuleValidator(BaseValidator):
    """Vectorized validator enforcing domain constraints (quantity > 0, price >= 0, timestamps not in future)."""

    @property
    def validator_name(self) -> str:
        return "BusinessRuleValidator"

    def validate(self, df: pd.DataFrame, context: PipelineContext) -> ValidationResult:
        start_time = time.perf_counter()
        failed_indices: set[int] = set()
        summary: dict[str, int] = {}

        if df.empty:
            return ValidationResult(
                validator_name=self.validator_name,
                status=ValidationStatus.PASSED,
                records_checked=0,
                records_failed=0,
                execution_time_ms=0.0,
            )

        # 1. Non-negative quantity check (VAL005)
        if "quantity" in df.columns:
            qty_series = pd.to_numeric(df["quantity"], errors="coerce")
            invalid_qty = qty_series <= 0
            bad_idx = set(df.index[invalid_qty.fillna(False)])
            failed_indices.update(bad_idx)
            if bad_idx:
                summary["VAL005_NEGATIVE_QUANTITY"] = len(bad_idx)

        # 2. Non-negative price check
        if "unit_price" in df.columns:
            price_series = pd.to_numeric(df["unit_price"], errors="coerce")
            invalid_price = price_series < 0.0
            bad_idx = set(df.index[invalid_price.fillna(False)])
            failed_indices.update(bad_idx)
            if bad_idx:
                summary["VAL002_NEGATIVE_PRICE"] = len(bad_idx)

        # 3. Future transaction timestamp check (VAL006)
        if "transaction_time" in df.columns:
            now_utc = pd.Timestamp.now(tz="UTC")
            ts_series = pd.to_datetime(df["transaction_time"], errors="coerce", utc=True)
            invalid_ts = ts_series > now_utc
            bad_idx = set(df.index[invalid_ts.fillna(False)])
            failed_indices.update(bad_idx)
            if bad_idx:
                summary["VAL006_FUTURE_TRANSACTION_DATE"] = len(bad_idx)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        status = ValidationStatus.FAILED if failed_indices else ValidationStatus.PASSED

        return ValidationResult(
            validator_name=self.validator_name,
            status=status,
            records_checked=len(df),
            records_failed=len(failed_indices),
            severity=ValidationSeverity.ERROR,
            execution_time_ms=duration_ms,
            error_summary=summary,
            failed_row_indices=sorted(failed_indices),
        )


class DuplicateValidator(BaseValidator):
    """Validator identifying duplicate transaction IDs (VAL003)."""

    def __init__(self, key_columns: list[str] | None = None) -> None:
        self.key_columns = key_columns or ["transaction_id", "product_id"]

    @property
    def validator_name(self) -> str:
        return "DuplicateValidator"

    def validate(self, df: pd.DataFrame, context: PipelineContext) -> ValidationResult:
        start_time = time.perf_counter()
        summary: dict[str, int] = {}
        failed_indices: list[int] = []

        valid_keys = [col for col in self.key_columns if col in df.columns]
        if valid_keys and not df.empty:
            dup_mask = df.duplicated(subset=valid_keys, keep="first")
            failed_indices = list(df.index[dup_mask])
            if failed_indices:
                summary["VAL003_DUPLICATE_PRIMARY_KEY"] = len(failed_indices)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        status = ValidationStatus.FAILED if failed_indices else ValidationStatus.PASSED

        return ValidationResult(
            validator_name=self.validator_name,
            status=status,
            records_checked=len(df),
            records_failed=len(failed_indices),
            severity=ValidationSeverity.WARNING,
            execution_time_ms=duration_ms,
            error_summary=summary,
            failed_row_indices=failed_indices,
        )
