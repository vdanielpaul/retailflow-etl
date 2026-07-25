# Dependency injection wiring container for Cloud Function repository adapters and services

from typing import Optional
from google.cloud import bigquery
from retailflow.cloud.config.settings import CloudFunctionSettings
from retailflow.cloud.repositories.watermark_repository import WatermarkRepository, BigQueryWatermarkRepository
from retailflow.cloud.services.event_publisher import EventPublisher, PubSubEventPublisher

class IngestionDependencyContainer:
    """Manages instantiation and injection of configuration settings, API clients, and repositories."""

    def __init__(self, bq_client: Optional[bigquery.Client] = None) -> None:
        self.settings = CloudFunctionSettings()
        
        # Centrally manage the lifetime of the BigQuery client
        if bq_client is not None:
            self.bq_client = bq_client
        else:
            try:
                self.bq_client = bigquery.Client(project=self.settings.project_id)
            except Exception:
                # Fallback to None in local testing environments without GCP authentication credentials
                self.bq_client = None

        # Instantiate repository adapter passing client dependency
        if self.bq_client is not None:
            self.watermark_repository: WatermarkRepository = BigQueryWatermarkRepository(
                client=self.bq_client,
                project_id=self.settings.project_id,
                dataset_id=self.settings.metadata_dataset_id
            )
        else:
            # Placeholder to prevent initialization crashes in test suites (overridden during test setups)
            self.watermark_repository = None # type: ignore
        
        # Instantiate publisher adapter
        self.event_publisher: EventPublisher = PubSubEventPublisher(
            project_id=self.settings.project_id,
            topic_name=self.settings.processing_topic_name
        )
