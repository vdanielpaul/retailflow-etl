# Pipeline dependency wiring container for infrastructure components

import uuid
from typing import Optional

from google.cloud import bigquery
from retailflow.cloud.repositories.metadata_repository import MetadataRepository, BigQueryMetadataRepository


class PipelineDependencyContainer:
    """Manages the lifecycle of database connections and metadata repositories for the pipeline runner."""

    def __init__(self, project_id: str, metadata_dataset: str, environment: str = "dev") -> None:
        self.project_id = project_id
        self.metadata_dataset = metadata_dataset
        self.environment = environment
        self.run_id = f"run-{uuid.uuid4().hex[:12]}"

        # Try to initialize the client, but handle missing credentials gracefully in offline test contexts
        try:
            self.bq_client = bigquery.Client(project=self.project_id)
            self.metadata_repository: Optional[MetadataRepository] = BigQueryMetadataRepository(
                client=self.bq_client,
                project_id=self.project_id,
                dataset_id=self.metadata_dataset,
                environment=self.environment
            )
        except Exception:
            self.bq_client = None
            self.metadata_repository = None
