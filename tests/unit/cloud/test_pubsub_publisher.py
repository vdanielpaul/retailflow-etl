# Unit tests for PubSubEventPublisher using Pub/Sub client mocking

import json
import pytest
from unittest.mock import MagicMock
from google.api_core.exceptions import GoogleAPICallError
from retailflow.cloud.exceptions import PublishEventError
from retailflow.cloud.models.events import FileAcceptedEvent
from retailflow.cloud.services.event_publisher import PubSubEventPublisher

@pytest.fixture
def mock_pubsub_client():
    client = MagicMock()
    # Mock topic_path formatter method
    client.topic_path.return_value = "projects/test-project/topics/test-topic"
    return client

@pytest.fixture
def event_publisher(mock_pubsub_client):
    return PubSubEventPublisher(
        client=mock_pubsub_client,
        project_id="test-project",
        topic_name="test-topic"
    )

def test_publish_accepted_event_success(event_publisher, mock_pubsub_client):
    """Verifies that events are serialized and published with trace headers."""
    mock_future = MagicMock()
    mock_pubsub_client.publish.return_value = mock_future
    
    event = FileAcceptedEvent(
        event_id="evt-123",
        ingestion_id="run-456",
        correlation_id="corr-789",
        bucket="test-bucket",
        object_name="raw/sales.csv",
        generation="g1",
        file_hash="hash123",
        received_at="2026-07-25T12:00:00Z"
    )
    
    event_publisher.publish_accepted_event(event)
    
    # Verify client was called with correct data payload and attributes
    mock_pubsub_client.publish.assert_called_once()
    args, kwargs = mock_pubsub_client.publish.call_args
    assert args[0] == "projects/test-project/topics/test-topic"
    
    # Check payload serialization
    published_payload = json.loads(kwargs["data"].decode("utf-8"))
    assert published_payload["event_id"] == "evt-123"
    assert published_payload["event_version"] == "1.0"
    
    # Check correlation ID trace headers propagation
    assert kwargs["event_type"] == "FILE_ACCEPTED"
    assert kwargs["correlation_id"] == "corr-789"
    assert kwargs["ingestion_id"] == "run-456"
    
    mock_future.result.assert_called_once()

def test_publish_accepted_event_api_failure(event_publisher, mock_pubsub_client):
    """Verifies PublishEventError is raised when Pub/Sub API returns error."""
    class MockPubSubError(GoogleAPICallError):
        pass
        
    mock_pubsub_client.publish.side_effect = MockPubSubError("Quota Exceeded")
    
    event = FileAcceptedEvent(
        event_id="evt-123",
        ingestion_id="run-456",
        correlation_id="corr-789",
        bucket="test-bucket",
        object_name="raw/sales.csv",
        generation="g1",
        file_hash="hash123",
        received_at="2026-07-25T12:00:00Z"
    )
    
    with pytest.raises(PublishEventError, match="Pub/Sub API call failure"):
        event_publisher.publish_accepted_event(event)
