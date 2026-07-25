# Repository models representing database records

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class DuplicateLookupResult(BaseModel):
    """Encapsulates duplicate query checks with historical tracing metadata."""
    is_duplicate: bool = Field(..., description="True if a matching hash already exists.")
    run_id: Optional[str] = Field(default=None, description="The historical execution run ID that ingested the file.")
    ingested_at: Optional[datetime] = Field(default=None, description="The timestamp tracking when the matching file was processed.")

class WatermarkRecord(BaseModel):
    """Domain model representing a file watermark database record."""
    file_hash: str = Field(..., description="The calculated SHA-256 hash of the ingested file.")
    filename: str = Field(..., description="The GCS file name path of the raw file.")
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The UTC timestamp tracking when the file was ingested."
    )
    run_id: str = Field(..., description="Unique run identifier tracking the execution instance.")

class AuditRecord(BaseModel):
    """Domain model representing an ETL execution audit metadata log record."""
    run_id: str = Field(..., description="Unique run identifier tracking the execution instance.")
    status: str = Field(..., description="The current status of the pipeline (e.g. INGESTED, COMPLETED, FAILED).")
    rows_read: int = Field(default=0, description="The total number of rows read from the source file.")
    rows_loaded: int = Field(default=0, description="The total number of rows loaded to the warehouse.")
    rows_rejected: int = Field(default=0, description="The total number of quarantined rows.")
    duration_ms: int = Field(default=0, description="The execution duration of the run in milliseconds.")
    error_message: Optional[str] = Field(default=None, description="The error message details if execution failed.")
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The UTC timestamp tracking when the audit log was updated."
    )
