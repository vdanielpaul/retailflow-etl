# Cloud Function environment settings configurations

import os
from pydantic import BaseModel, Field

class CloudFunctionSettings(BaseModel):
    """Encapsulates system configuration parameters loaded from environment variables."""
    project_id: str = Field(
        default_factory=lambda: os.getenv("GCP_PROJECT", "retailflow-dev-project"),
        description="The active Google Cloud Platform Project ID."
    )
    environment: str = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "dev"),
        description="The environment stage lifecycle (dev, staging, or prod)."
    )
    processing_topic_name: str = Field(
        default_factory=lambda: os.getenv("PROCESSING_TOPIC_NAME", "retailflow-dev-processing-events"),
        description="The name of the Pub/Sub topic to publish validated ingest events to."
    )
    metadata_dataset_id: str = Field(
        default_factory=lambda: os.getenv("METADATA_DATASET_ID", "retailflow_dev_metadata"),
        description="The BigQuery dataset ID hosting audit watermark logs."
    )
