"""Custom domain exception hierarchy for RetailFlow ETL pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from retailflow.constants.constants import ErrorCode, ExecutionStage


class RetailFlowError(Exception):
    """Base exception class for all RetailFlow ETL pipeline errors."""

    def __init__(
        self,
        user_message: str,
        technical_message: str | None = None,
        error_code: ErrorCode | str = ErrorCode.ERR_CONFIG_INVALID,
        error_category: str = "SYSTEM",
        retryable: bool = False,
        stage: ExecutionStage | str = ExecutionStage.INITIALIZATION,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(user_message)
        self.user_message = user_message
        self.technical_message = technical_message or user_message
        self.error_code = error_code.value if isinstance(error_code, ErrorCode) else str(error_code)
        self.error_category = error_category
        self.retryable = retryable
        self.stage = stage.value if isinstance(stage, ExecutionStage) else str(stage)
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception metadata to a dictionary for logging and audit tracking."""
        return {
            "error_code": self.error_code,
            "error_category": self.error_category,
            "user_message": self.user_message,
            "technical_message": self.technical_message,
            "retryable": self.retryable,
            "stage": self.stage,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class ConfigurationError(RetailFlowError):
    """Raised when configuration parsing, loading, or semantic validation fails."""

    def __init__(
        self,
        user_message: str,
        technical_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            user_message=user_message,
            technical_message=technical_message,
            error_code=ErrorCode.ERR_CONFIG_INVALID,
            error_category="CONFIGURATION",
            retryable=False,
            stage=ExecutionStage.CONFIGURATION_LOADING,
            details=details,
        )


class DatabaseError(RetailFlowError):
    """Base exception class for database-related failures."""

    def __init__(
        self,
        user_message: str,
        technical_message: str | None = None,
        error_code: ErrorCode | str = ErrorCode.ERR_DB_EXECUTION,
        retryable: bool = False,
        stage: ExecutionStage | str = ExecutionStage.FACT_LOADING,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            user_message=user_message,
            technical_message=technical_message,
            error_code=error_code,
            error_category="DATABASE",
            retryable=retryable,
            stage=stage,
            details=details,
        )


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection or connection pool initialization fails."""

    def __init__(
        self,
        user_message: str,
        technical_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            user_message=user_message,
            technical_message=technical_message,
            error_code=ErrorCode.ERR_DB_CONNECTION,
            retryable=True,
            stage=ExecutionStage.INITIALIZATION,
            details=details,
        )


class DatabaseExecutionError(DatabaseError):
    """Raised when a SQL query or statement execution fails."""

    def __init__(
        self,
        user_message: str,
        technical_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            user_message=user_message,
            technical_message=technical_message,
            error_code=ErrorCode.ERR_DB_EXECUTION,
            retryable=False,
            stage=ExecutionStage.FACT_LOADING,
            details=details,
        )


class TransactionError(DatabaseError):
    """Raised when a database transaction commit or rollback fails."""

    def __init__(
        self,
        user_message: str,
        technical_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            user_message=user_message,
            technical_message=technical_message,
            error_code=ErrorCode.ERR_DB_EXECUTION,
            retryable=False,
            stage=ExecutionStage.FACT_LOADING,
            details=details,
        )


class ValidationError(RetailFlowError):
    """Base exception class for data validation failures."""

    def __init__(
        self,
        user_message: str,
        technical_message: str | None = None,
        error_code: ErrorCode | str = ErrorCode.VAL_INVALID_DATATYPE,
        stage: ExecutionStage | str = ExecutionStage.ROW_VALIDATION,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            user_message=user_message,
            technical_message=technical_message,
            error_code=error_code,
            error_category="VALIDATION",
            retryable=False,
            stage=stage,
            details=details,
        )


class SchemaValidationError(ValidationError):
    """Raised when CSV file structure or column headers fail validation."""

    def __init__(
        self,
        user_message: str,
        technical_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            user_message=user_message,
            technical_message=technical_message,
            error_code=ErrorCode.ERR_HEADER_MISMATCH,
            stage=ExecutionStage.SCHEMA_VALIDATION,
            details=details,
        )


class RowValidationError(ValidationError):
    """Raised when record-level validation threshold is breached."""

    def __init__(
        self,
        user_message: str,
        technical_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            user_message=user_message,
            technical_message=technical_message,
            error_code=ErrorCode.VAL_INVALID_DATATYPE,
            stage=ExecutionStage.ROW_VALIDATION,
            details=details,
        )


class TransformationError(RetailFlowError):
    """Raised when data transformation, cleaning, or surrogate key resolution fails."""

    def __init__(
        self,
        user_message: str,
        technical_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            user_message=user_message,
            technical_message=technical_message,
            error_code=ErrorCode.VAL_INVALID_DATATYPE,
            error_category="TRANSFORMATION",
            retryable=False,
            stage=ExecutionStage.TRANSFORMATION,
            details=details,
        )


class AuditError(RetailFlowError):
    """Raised when logging to audit table or watermark tracking fails."""

    def __init__(
        self,
        user_message: str,
        technical_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            user_message=user_message,
            technical_message=technical_message,
            error_code=ErrorCode.ERR_DB_EXECUTION,
            error_category="AUDIT",
            retryable=True,
            stage=ExecutionStage.AUDIT_LOGGING,
            details=details,
        )
