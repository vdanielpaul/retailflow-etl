# Pydantic data schemas representing GCS inputs and the downstream trigger event contract

from typing import Optional
from pydantic import BaseModel, Field

class GcsNotificationPayload(BaseModel):
    """Represents the raw payload structure emitted by GCS storage notifications (JSON API v1)."""
    bucket: str = Field(..., description="The name of the GCS bucket.")
    name: str = Field(..., description="The file path name of the uploaded object.")
    generation: str = Field(..., description="The content generation identifier of the object.")
    size: int = Field(..., description="The size of the object in bytes.")
    contentType: str = Field(..., description="The MIME content type of the object.")
    updated: str = Field(..., description="The modification timestamp of the object.")

class FileAcceptedEvent(BaseModel):
    """The structured event contract payload published to processing-events topic after duplicate verification succeeds."""
    event_id: str = Field(..., description="A unique UUID identifying this processing event.")
    ingestion_id: str = Field(..., description="A tracking run ID for this ingestion pipeline instance.")
    correlation_id: str = Field(..., description="A correlation tracing identifier linking logs and state metrics.")
    bucket: str = Field(..., description="The name of the GCS raw bucket.")
    object_name: str = Field(..., description="The file path name of the accepted object.")
    generation: str = Field(..., description="The content generation identifier of the object.")
    file_hash: str = Field(..., description="The calculated SHA-256 hash of the object content.")
    received_at: str = Field(..., description="The UTC timestamp tracking when the file was accepted.")
    event_version: str = Field(default="1.0", description="The schema version of the event contract payload.")
    event_type: str = Field(default="FILE_ACCEPTED", description="The type classification of the event.")
