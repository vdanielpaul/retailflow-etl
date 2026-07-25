# Downstream event publisher abstractions and adapters

from abc import ABC, abstractmethod
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
    """Production implementation of Pub/Sub event publisher."""
    
    def __init__(self, project_id: str, topic_name: str) -> None:
        self.project_id = project_id
        self.topic_name = topic_name

    def publish_accepted_event(self, event: FileAcceptedEvent) -> None:
        # To be implemented in Task 2.4
        raise NotImplementedError("Pub/Sub event publisher not implemented yet.")
