# Google Cloud Functions Gen2 Entry Point Handler

import functions_framework
from cloudevents.http import CloudEvent
from retailflow.cloud.dependencies import IngestionDependencyContainer
from retailflow.cloud.handlers.event_handler import IngestEventHandler
from retailflow.cloud.logging.logger import get_cloud_logger

logger = get_cloud_logger()

# 1. Instantiate the dependency container and handler
container = IngestionDependencyContainer()
handler = IngestEventHandler(container)

@functions_framework.cloud_event
def entrypoint(cloud_event: CloudEvent) -> None:
    """Invoked when a GCS event is published to the ingestion Pub/Sub topic.
    Behaves as a stateless trigger entry point.

    Args:
        cloud_event: CloudEvent container wrapper payload.
    """
    logger.info("Received raw CloudEvent notification payload.")
    
    # 2. Extract the Pub/Sub message data wrapper
    event_data = cloud_event.data
    if not event_data or "message" not in event_data:
        logger.error("CloudEvent data does not contain a valid Pub/Sub message wrapper.")
        return
        
    pubsub_message = event_data["message"]
    
    # 3. Delegate message to handler orchestrator
    try:
        result = handler.handle_ingestion_message(pubsub_message)
        logger.info(f"Ingestion event handling finished successfully: {result['status']}.")
    except Exception as err:
        logger.error(f"Ingestion trigger handling failed: {str(err)}")
        # Log and return to prevent Eventarc redelivery loops
        return
