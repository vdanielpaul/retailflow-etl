# Downstream event publisher abstractions and adapters

import json
from abc import ABC, abstractmethod
from google.cloud import pubsub_v1
from google.api_core.exceptions import GoogleAPICallError
from retailflow.cloud.exceptions import PublishEventError
from retailflow.cloud.models.events import FileAcceptedEvent

class EventPublisher(ABC):
    """Abstract interface defining the publisher client contract."""
    
    @abstractmethod
    def publish_accepted_event(self, event: FileAcceptedEvent) -> None:
        """Publish the structured FILE_ACCEPTED contract payload downstream.

        Args:
            event: Structured FileAcceptedEvent object.
        """
        pass

class PubSubEventPublisher(EventPublisher):
    """Production implementation of Pub/Sub event publisher using google-cloud-pubsub."""
    
    def __init__(self, client: pubsub_v1.PublisherClient, project_id: str, topic_name: str) -> None:
        self.client = client
        self.project_id = project_id
        self.topic_name = topic_name
        self.topic_path = self.client.topic_path(self.project_id, self.topic_name)

    def publish_accepted_event(self, event: FileAcceptedEvent) -> None:
        # 1. Serialize the Pydantic event object payload into JSON bytes
        try:
            event_data = json.dumps(event.model_dump()).encode("utf-8")
        except Exception as err:
            raise PublishEventError(f"Failed to serialize FileAcceptedEvent payload: {str(err)}") from err

        # 2. Extract key attributes to propagate in message headers (aids tracing and subscription filters)
        attributes = {
            "event_type": event.event_type,
            "event_version": event.event_version,
            "correlation_id": event.correlation_id,
            "ingestion_id": event.ingestion_id
        }

        # 3. Publish the message to GCP Pub/Sub
        try:
            future = self.client.publish(
                self.topic_path,
                data=event_data,
                **attributes
            )
            future.result() # Synchronously block to guarantee the publish completes successfully
        except GoogleAPICallError as err:
            raise PublishEventError(f"Pub/Sub API call failure publishing event: {str(err)}") from err
        except Exception as err:
            raise PublishEventError(f"Unexpected error publishing trigger event: {str(err)}") from err
class MockEventPublisher(EventPublisher):
    """Test mock implementation for downstream event publishing."""
    def __init__(self) -> None:
        self.published_events = []

    def publish_accepted_event(self, event: FileAcceptedEvent) -> None:
        self.published_events.append(event)
