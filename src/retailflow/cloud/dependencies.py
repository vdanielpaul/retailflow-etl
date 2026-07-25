# Dependency injection wiring container for Cloud Function repository adapters and services

from typing import Optional
from google.cloud import bigquery
from google.cloud import storage
from google.cloud import pubsub_v1
from retailflow.cloud.config.settings import CloudFunctionSettings
from retailflow.cloud.repositories.metadata_repository import MetadataRepository, BigQueryMetadataRepository
from retailflow.cloud.services.event_publisher import EventPublisher, PubSubEventPublisher
from retailflow.cloud.services.storage_service import StorageService, GcsStorageService

class IngestionDependencyContainer:
    """Manages instantiation and injection of configuration settings, API clients, and services."""

    def __init__(
        self, 
        bq_client: Optional[bigquery.Client] = None,
        storage_client: Optional[storage.Client] = None,
        pubsub_client: Optional[pubsub_v1.PublisherClient] = None
    ) -> None:
        self.settings = CloudFunctionSettings()
        
        # 1. Centrally manage the lifetime of the BigQuery client
        if bq_client is not None:
            self.bq_client = bq_client
        else:
            try:
                self.bq_client = bigquery.Client(project=self.settings.project_id)
            except Exception:
                self.bq_client = None

        if self.bq_client is not None:
            self.metadata_repository: MetadataRepository = BigQueryMetadataRepository(
                client=self.bq_client,
                project_id=self.settings.project_id,
                dataset_id=self.settings.metadata_dataset_id,
                environment=self.settings.environment
            )
        else:
            self.metadata_repository = None # type: ignore
        
        # 2. Centrally manage the GCS Storage client
        if storage_client is not None:
            self.storage_client = storage_client
        else:
            try:
                self.storage_client = storage.Client(project=self.settings.project_id)
            except Exception:
                self.storage_client = None

        if self.storage_client is not None:
            self.storage_service: StorageService = GcsStorageService(client=self.storage_client)
        else:
            self.storage_service = None # type: ignore

        # 3. Centrally manage the Pub/Sub Publisher client
        if pubsub_client is not None:
            self.pubsub_client = pubsub_client
        else:
            try:
                self.pubsub_client = pubsub_v1.PublisherClient()
            except Exception:
                self.pubsub_client = None

        if self.pubsub_client is not None:
            self.event_publisher: EventPublisher = PubSubEventPublisher(
                client=self.pubsub_client,
                project_id=self.settings.project_id,
                topic_name=self.settings.processing_topic_name
            )
        else:
            self.event_publisher = None # type: ignore
