# Unit test validations verifying the Ingest Cloud Function trigger scaffolding

import base64
import json
import pytest
from retailflow.cloud.dependencies import IngestionDependencyContainer
from retailflow.cloud.exceptions import InvalidEventError, DuplicateFileError
from retailflow.cloud.handlers.event_handler import IngestEventHandler
from retailflow.cloud.models.events import FileAcceptedEvent
from retailflow.cloud.services.watermark_service import BaseWatermarkService
from retailflow.cloud.services.publisher_service import BasePublisherService

#-------------------------------------------------------------------------------
# 1. Unit Test Mock Implementations (Isolated from production code)
#-------------------------------------------------------------------------------
class MockWatermarkService(BaseWatermarkService):
    """Test mock implementation for watermark database checks."""
    def __init__(self, simulate_duplicate: bool = False) -> None:
        self.simulate_duplicate = simulate_duplicate
        self.registered_hashes = []

    def is_duplicate_hash(self, file_hash: str) -> bool:
        return self.simulate_duplicate

    def register_ingestion(self, file_hash: str, filename: str, run_id: str) -> None:
        self.registered_hashes.append(file_hash)

class MockPublisherService(BasePublisherService):
    """Test mock implementation for downstream event publishing."""
    def __init__(self) -> None:
        self.published_events = []

    def publish_accepted_event(self, event: FileAcceptedEvent) -> None:
        self.published_events.append(event)

#-------------------------------------------------------------------------------
# 2. Pytest Fixtures
#-------------------------------------------------------------------------------
@pytest.fixture
def mock_watermark_service():
    return MockWatermarkService(simulate_duplicate=False)

@pytest.fixture
def mock_publisher_service():
    return MockPublisherService()

@pytest.fixture
def test_container(mock_watermark_service, mock_publisher_service):
    """Initializes dependency container and injects mock services for test context."""
    container = IngestionDependencyContainer()
    container.watermark_service = mock_watermark_service
    container.publisher_service = mock_publisher_service
    return container

@pytest.fixture
def mock_pubsub_message():
    """Builds a mock GCS object finalize notification payload wrapper."""
    raw_payload = {
        "bucket": "retailflow-dev-project-retailflow-dev-raw",
        "name": "sales/sales_20260725.csv",
        "generation": "1234567890",
        "size": 1024,
        "contentType": "text/csv",
        "updated": "2026-07-25T12:00:00Z"
    }
    
    json_bytes = json.dumps(raw_payload).encode("utf-8")
    base64_data = base64.b64encode(json_bytes).decode("utf-8")
    
    return {
        "message": {
            "data": base64_data,
            "messageId": "9999999999",
            "publishTime": "2026-07-25T12:00:01Z",
            "attributes": {
                "correlation_id": "corr-test-1234"
            }
        }
    }

#-------------------------------------------------------------------------------
# 3. Test Cases
#-------------------------------------------------------------------------------
def test_handler_parses_valid_payload(test_container, mock_pubsub_message):
    """Verifies that the event handler decodes raw messages and invokes the service."""
    handler = IngestEventHandler(test_container)
    result = handler.handle_ingestion_message(mock_pubsub_message["message"])
    
    assert result["status"] == "ACCEPTED"
    assert result["correlation_id"] == "corr-test-1234"
    assert result["run_id"].startswith("run-")
    assert result["file_hash"].startswith("hash-")

    # Verify mock services were called
    assert len(test_container.watermark_service.registered_hashes) == 1
    assert len(test_container.publisher_service.published_events) == 1
    
    published_event = test_container.publisher_service.published_events[0]
    assert published_event.event_version == "1.0"
    assert published_event.event_type == "FILE_ACCEPTED"
    assert published_event.correlation_id == "corr-test-1234"

def test_handler_generates_correlation_id_if_missing(test_container, mock_pubsub_message):
    """Verifies that a correlation_id is auto-generated if missing from Pub/Sub attributes."""
    handler = IngestEventHandler(test_container)
    message = mock_pubsub_message["message"]
    # Strip correlation_id
    if "attributes" in message:
        del message["attributes"]

    result = handler.handle_ingestion_message(message)
    assert result["status"] == "ACCEPTED"
    assert result["correlation_id"].startswith("corr-")

def test_handler_rejects_missing_data(test_container):
    """Verifies handler raises InvalidEventError when data is missing."""
    handler = IngestEventHandler(test_container)
    invalid_message = {"attributes": {}}
    
    with pytest.raises(InvalidEventError, match="missing 'data' field"):
        handler.handle_ingestion_message(invalid_message)

def test_handler_rejects_malformed_json(test_container):
    """Verifies handler raises InvalidEventError when JSON parsing fails."""
    handler = IngestEventHandler(test_container)
    bad_base64 = base64.b64encode(b"not-json-data").decode("utf-8")
    invalid_message = {"data": bad_base64}
    
    with pytest.raises(InvalidEventError, match="Failed to decode base64"):
        handler.handle_ingestion_message(invalid_message)

def test_handler_rejects_missing_schema_properties(test_container):
    """Verifies Pydantic validations enforce required metadata fields."""
    handler = IngestEventHandler(test_container)
    bad_payload = {"contentType": "text/csv", "size": 1024}
    json_bytes = json.dumps(bad_payload).encode("utf-8")
    bad_base64 = base64.b64encode(json_bytes).decode("utf-8")
    invalid_message = {"data": bad_base64}
    
    with pytest.raises(InvalidEventError, match="Metadata schema validation failed"):
        handler.handle_ingestion_message(invalid_message)

def test_duplicate_file_throws_exception(test_container, mock_pubsub_message):
    """Verifies that watermark duplicates trigger DuplicateFileError and stop flow."""
    # Force watermark service to simulate a duplicate hash match
    test_container.watermark_service.simulate_duplicate = True
    handler = IngestEventHandler(test_container)
    
    with pytest.raises(DuplicateFileError, match="Duplicate file hash detected"):
        handler.handle_ingestion_message(mock_pubsub_message["message"])

    # Verify no publish took place
    assert len(test_container.publisher_service.published_events) == 0
