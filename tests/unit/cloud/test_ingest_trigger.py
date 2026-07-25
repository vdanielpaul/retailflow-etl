# Unit test validations verifying the Ingest Cloud Function trigger scaffolding

import base64
import json
import pytest
from cloudevents.http import CloudEvent
from retailflow.cloud.dependencies import IngestionDependencyContainer
from retailflow.cloud.handlers.event_handler import IngestEventHandler
from retailflow.cloud.main import entrypoint

@pytest.fixture
def test_container():
    """Initializes container configurations for unit tests."""
    return IngestionDependencyContainer()

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
    
    # Base64 encode the JSON payload to match Pub/Sub message data schema format
    json_bytes = json.dumps(raw_payload).encode("utf-8")
    base64_data = base64.b64encode(json_bytes).decode("utf-8")
    
    return {
        "message": {
            "data": base64_data,
            "messageId": "9999999999",
            "publishTime": "2026-07-25T12:00:01Z"
        }
    }

def test_handler_parses_valid_payload(test_container, mock_pubsub_message):
    """Verifies that the event handler decodes and validates standard formats."""
    handler = IngestEventHandler(test_container)
    result = handler.handle_ingestion_message(mock_pubsub_message["message"])
    
    assert result["status"] == "PARSED_SUCCESSFULLY"
    assert result["bucket"] == "retailflow-dev-project-retailflow-dev-raw"
    assert result["object"] == "sales/sales_20260725.csv"
    assert result["size"] == 1024

def test_handler_rejects_missing_data(test_container):
    """Verifies handler raises errors when data blocks are omitted."""
    handler = IngestEventHandler(test_container)
    invalid_message = {"attributes": {}}
    
    with pytest.raises(ValueError, match="missing 'data' field"):
        handler.handle_ingestion_message(invalid_message)

def test_handler_rejects_malformed_json(test_container):
    """Verifies handler raises error when base64 payload is invalid JSON."""
    handler = IngestEventHandler(test_container)
    bad_base64 = base64.b64encode(b"not-json-data").decode("utf-8")
    invalid_message = {"data": bad_base64}
    
    with pytest.raises(ValueError, match="Failed to decode base64"):
        handler.handle_ingestion_message(invalid_message)

def test_handler_rejects_missing_schema_properties(test_container):
    """Verifies Pydantic validations enforce presence of required parameters."""
    handler = IngestEventHandler(test_container)
    # Missing required 'bucket' and 'name' fields in storage notifications
    bad_payload = {"contentType": "text/csv", "size": 1024}
    json_bytes = json.dumps(bad_payload).encode("utf-8")
    bad_base64 = base64.b64encode(json_bytes).decode("utf-8")
    invalid_message = {"data": bad_base64}
    
    with pytest.raises(ValueError, match="Metadata schema validation failed"):
        handler.handle_ingestion_message(invalid_message)
