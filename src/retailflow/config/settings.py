"""Typed Pydantic settings models for RetailFlow ETL configuration validation."""

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class PipelineSettings(BaseModel):
    """Pipeline execution parameters."""

    name: str = "retailflow-etl"
    version: str = "0.1.0"
    environment: str = "development"
    batch_size: int = Field(default=10000, ge=1, le=100000)
    stop_on_error: bool = False
    max_error_percentage: float = Field(default=5.0, ge=0.0, le=100.0)


class DatabaseSettings(BaseModel):
    """PostgreSQL database connection parameters."""

    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)
    name: str = "retailflow_dw"
    user: str = "retailflow_user"
    password: str = ""
    schema_name: str = Field(default="public", alias="schema")
    connection_timeout: int = Field(default=30, ge=1)
    min_connections: int = Field(default=1, ge=1)
    max_connections: int = Field(default=10, ge=1)


class PathsSettings(BaseModel):
    """Directory targets for data lifecycle, logs, and SQL scripts."""

    sample_dir: Path = Path("data/sample")
    raw_dir: Path = Path("data/raw")
    staging_dir: Path = Path("data/staging")
    processed_dir: Path = Path("data/processed")
    archive_dir: Path = Path("data/archive")
    bad_records_dir: Path = Path("data/bad_records")
    log_dir: Path = Path("logs")
    sql_dir: Path = Path("sql")


class LoggingSettings(BaseModel):
    """Logging formatting and rotation options."""

    level: str = "INFO"
    console_output: bool = True
    file_output: bool = True
    log_filename: str = "retailflow_etl.log"
    max_bytes: int = Field(default=10485760, ge=1024)
    backup_count: int = Field(default=5, ge=1)

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level string."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in allowed:
            raise ValueError(f"Invalid log level: {v}. Must be one of {allowed}")
        return upper_v


class ValidationSettings(BaseModel):
    """Data quality enforcement rules."""

    allow_missing_optional_columns: bool = False
    quarantine_bad_records: bool = True
    reject_future_dates: bool = True
    reject_negative_sales: bool = True
    email_validation_regex: str = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class AuditSettings(BaseModel):
    """Audit table and operational metrics options."""

    table_name: str = "etl_audit_log"
    watermark_table_name: str = "etl_watermark"
    enable_row_level_metrics: bool = True


class Settings(BaseModel):
    """Master Application Settings container."""

    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    paths: PathsSettings = Field(default_factory=PathsSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    validation: ValidationSettings = Field(default_factory=ValidationSettings)
    audit: AuditSettings = Field(default_factory=AuditSettings)
