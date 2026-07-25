# Unit tests for GcsStorageService using GCS Client mocking

import io
import pytest
from unittest.mock import MagicMock
from google.api_core.exceptions import GoogleAPICallError
from retailflow.cloud.exceptions import IngestionError
from retailflow.cloud.services.storage_service import GcsStorageService

@pytest.fixture
def mock_storage_client():
    return MagicMock()

@pytest.fixture
def storage_service(mock_storage_client):
    return GcsStorageService(client=mock_storage_client)

def test_calculate_sha256_success(storage_service, mock_storage_client):
    """Verifies that GCS storage service streams file content chunks and calculates SHA-256."""
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_storage_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    
    # Mock blob context manager streaming bytes
    # Hashing "hello world" yields 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
    dummy_file_stream = io.BytesIO(b"hello world")
    mock_blob.open.return_value.__enter__.return_value = dummy_file_stream

    result = storage_service.calculate_sha256("test-bucket", "raw/sales.csv")
    
    assert result == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    mock_storage_client.bucket.assert_called_once_with("test-bucket")
    mock_bucket.blob.assert_called_once_with("raw/sales.csv")
    mock_blob.open.assert_called_once_with("rb")

def test_calculate_sha256_gcs_api_failure(storage_service, mock_storage_client):
    """Verifies GcsStorageService raises IngestionError on API failures."""
    class MockGCSError(GoogleAPICallError):
        pass
        
    mock_storage_client.bucket.side_effect = MockGCSError("Access Denied")

    with pytest.raises(IngestionError, match="GCS API failure"):
        storage_service.calculate_sha256("bucket", "file")
