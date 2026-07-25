# Unit test validations verifying the Ingest Cloud Function trigger and Application Ingestion Service

import base64
import json
import pytest
from datetime import datetime, timezone
from retailflow.cloud.dependencies import IngestionDependencyContainer
from retailflow.cloud.exceptions import InvalidEventError, DuplicateFileError
from retailflow.cloud.handlers.event_handler import IngestEventHandler
from retailflow.cloud.models.events import FileAcceptedEvent
from retailflow.cloud.repositories.metadata_repository import MetadataRepository
from retailflow.cloud.services.event_publisher import EventPublisher
from retailflow.cloud.services.storage_service import StorageService
from retailflow.cloud.repositories.models import WatermarkRecord, AuditRecord, DuplicateLookupResult

#-------------------------------------------------------------------------------
# 1. Unit Test Mock Implementations (Isolated from production code)
#-------------------------------------------------------------------------------
class MockMetadataRepository(MetadataRepository):
    """Test mock implementation for metadata database checks."""
    def __init__(self, simulate_duplicate: bool = False) -> None:
        self.simulate_duplicate = simulate_duplicate
        self.registered_watermarks = []
        self.registered_audits = []

    def lookup_duplicate(self, file_hash: str) -> DuplicateLookupResult:
        if self.simulate_duplicate:
            return DuplicateLookupResult(
                is_duplicate=True,
                run_id="run-historic123",
                ingested_at=datetime.now(timezone.utc)
            )
        return DuplicateLookupResult(is_duplicate=False)

    def create_watermark(self, record: WatermarkRecord) -> None:
        self.registered_watermarks.append(record)

    def record_audit(self, record: AuditRecord) -> None:
        self.registered_audits.append(record)

class MockEventPublisher(EventPublisher):
    """Test mock implementation for downstream event publishing."""
    def __init__(self) -> None:
        self.published_events = []

    def publish_accepted_event(self, event: FileAcceptedEvent) -> None:
        self.published_events.append(event)

class MockStorageService(StorageService):
    """Test mock implementation for streaming GCS file hashing."""
    def __init__(self, test_hash: str = "hash-test-sha256-checksum") -> None:
        self.test_hash = test_hash
        self.called_with = []

    def calculate_sha256(self, bucket_name: str, object_name: str) -> str:
        self.called_with.append((bucket_name, object_name))
        return self.test_hash

#-------------------------------------------------------------------------------
# 2. Pytest Fixtures
#-------------------------------------------------------------------------------
@pytest.fixture
def mock_metadata_repository():
    return MockMetadataRepository(simulate_duplicate=False)

@pytest.fixture
def mock_event_publisher():
    return MockEventPublisher()

@pytest.fixture
def mock_storage_service():
    return MockStorageService(test_hash="hash-abc-123-xyz")

@pytest.fixture
def test_container(mock_metadata_repository, mock_event_publisher, mock_storage_service):
    """Initializes dependency container and overrides concrete adapters with mock services."""
    container = IngestionDependencyContainer()
    container.metadata_repository = mock_metadata_repository
    container.event_publisher = mock_event_publisher
    container.storage_service = mock_storage_service
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
    assert result["file_hash"] == "hash-abc-123-xyz"

    # Verify mock storage service hash was called
    assert len(test_container.storage_service.called_with) == 1
    assert test_container.storage_service.called_with[0] == (
        "retailflow-dev-project-retailflow-dev-raw",
        "sales/sales_20260725.csv"
    )

    # Verify mock repository audits & watermarks
    assert len(test_container.metadata_repository.registered_watermarks) == 1
    assert len(test_container.metadata_repository.registered_audits) == 2 # INGESTING, INGESTED success
    assert test_container.metadata_repository.registered_audits[0].status == "INGESTING"
    assert test_container.metadata_repository.registered_audits[1].status == "INGESTED"

    # Verify mock publisher was called
    assert len(test_container.event_publisher.published_events) == 1
    
    published_event = test_container.event_publisher.published_events[0]
    assert published_event.event_version == "1.0"
    assert published_event.event_type == "FILE_ACCEPTED"
    assert published_event.correlation_id == "corr-test-1234"
    assert published_event.file_hash == "hash-abc-123-xyz"

def test_handler_generates_correlation_id_if_missing(test_container, mock_pubsub_message):
    """Verifies that a correlation_id is auto-generated if missing from Pub/Sub attributes."""
    handler = IngestEventHandler(test_container)
    message = mock_pubsub_message["message"]
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
    test_container.metadata_repository.simulate_duplicate = True
    handler = IngestEventHandler(test_container)
    
    with pytest.raises(DuplicateFileError, match="Duplicate file hash detected"):
        handler.handle_ingestion_message(mock_pubsub_message["message"])

    # Verify no watermark created and no events published
    assert len(test_container.metadata_repository.registered_watermarks) == 0
    assert len(test_container.event_publisher.published_events) == 0
    assert test_container.metadata_repository.registered_audits[-1].status == "REJECTED_DUPLICATE"
