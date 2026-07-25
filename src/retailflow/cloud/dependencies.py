# Dependency injection wiring container for Cloud Function services

from retailflow.cloud.config.settings import CloudFunctionSettings
from retailflow.cloud.services.watermark_service import BaseWatermarkService, BigQueryWatermarkService
from retailflow.cloud.services.publisher_service import BasePublisherService, PubSubPublisherService

class IngestionDependencyContainer:
    """Manages instantiation and injection of configuration settings and production client services."""

    def __init__(self) -> None:
        self.settings = CloudFunctionSettings()
        # Wire production services by default; mock implementations reside in unit tests
        self.watermark_service: BaseWatermarkService = BigQueryWatermarkService(
            project_id=self.settings.project_id,
            dataset_id=self.settings.metadata_dataset_id
        )
        self.publisher_service: BasePublisherService = PubSubPublisherService(
            project_id=self.settings.project_id,
            topic_name=self.settings.processing_topic_name
        )
