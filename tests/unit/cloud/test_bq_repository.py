# Unit tests for BigQueryMetadataRepository using BQ Client mocking

from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock
from google.api_core.exceptions import GoogleAPICallError
from retailflow.cloud.exceptions import WatermarkLookupError, MetadataPersistenceError
from retailflow.cloud.repositories.models import WatermarkRecord, AuditRecord
from retailflow.cloud.repositories.metadata_repository import BigQueryMetadataRepository

@pytest.fixture
def mock_bq_client():
    return MagicMock()

@pytest.fixture
def bq_repository(mock_bq_client):
    return BigQueryMetadataRepository(
        client=mock_bq_client,
        project_id="test-project",
        dataset_id="test_dataset",
        environment="dev"
    )

def test_lookup_duplicate_found(bq_repository, mock_bq_client):
    """Verifies lookup_duplicate returns DuplicateLookupResult(is_duplicate=True) and mapping details."""
    mock_query_job = MagicMock()
    
    # Mocking rows returned with mock row objects (dicts or row objects with keys)
    mock_row = MagicMock()
    mock_row.get.side_effect = lambda key: {
        "run_id": "run-historic123",
        "ingested_at": datetime(2026, 7, 25, 12, 0, 0, tzinfo=timezone.utc)
    }.get(key)
    
    mock_query_job.result.return_value = [mock_row]
    mock_bq_client.query.return_value = mock_query_job

    result = bq_repository.lookup_duplicate("some-file-hash")
    
    assert result.is_duplicate is True
    assert result.run_id == "run-historic123"
    assert result.ingested_at == datetime(2026, 7, 25, 12, 0, 0, tzinfo=timezone.utc)
    mock_bq_client.query.assert_called_once()
    args, kwargs = mock_bq_client.query.call_args
    assert "test-project.test_dataset.etl_watermark" in args[0]
    assert kwargs["job_config"].query_parameters[0].value == "some-file-hash"
    assert kwargs["job_config"].labels["environment"] == "dev"

def test_lookup_duplicate_not_found(bq_repository, mock_bq_client):
    """Verifies lookup_duplicate returns DuplicateLookupResult(is_duplicate=False)."""
    mock_query_job = MagicMock()
    mock_query_job.result.return_value = []
    mock_bq_client.query.return_value = mock_query_job

    result = bq_repository.lookup_duplicate("new-file-hash")
    
    assert result.is_duplicate is False
    assert result.run_id is None
    assert result.ingested_at is None
    mock_bq_client.query.assert_called_once()

def test_lookup_duplicate_bq_api_failure(bq_repository, mock_bq_client):
    """Verifies lookup_duplicate raises WatermarkLookupError when BigQuery client raises API exception."""
    class MockBigQueryError(GoogleAPICallError):
        pass
        
    mock_bq_client.query.side_effect = MockBigQueryError("BQ query timeout")

    with pytest.raises(WatermarkLookupError, match="BigQuery API error"):
        bq_repository.lookup_duplicate("hash")

def test_create_watermark_success(bq_repository, mock_bq_client):
    """Verifies watermark insert completes successfully."""
    mock_query_job = MagicMock()
    mock_bq_client.query.return_value = mock_query_job
    
    record = WatermarkRecord(
        file_hash="abc-123",
        filename="sales/sales_data.csv",
        run_id="run-999"
    )
    
    bq_repository.create_watermark(record)
    
    mock_bq_client.query.assert_called_once()
    mock_query_job.result.assert_called_once()
    args, kwargs = mock_bq_client.query.call_args
    assert "INSERT INTO `test-project.test_dataset.etl_watermark`" in args[0]
    params = kwargs["job_config"].query_parameters
    assert params[0].name == "file_hash"
    assert params[0].value == "abc-123"

def test_create_watermark_failure(bq_repository, mock_bq_client):
    """Verifies create_watermark raises MetadataPersistenceError on API failure."""
    class MockBigQueryError(GoogleAPICallError):
        pass
        
    mock_bq_client.query.side_effect = MockBigQueryError("Table not found")
    record = WatermarkRecord(
        file_hash="abc-123",
        filename="sales/sales_data.csv",
        run_id="run-999"
    )

    with pytest.raises(MetadataPersistenceError, match="BigQuery API error"):
        bq_repository.create_watermark(record)

def test_record_audit_success(bq_repository, mock_bq_client):
    """Verifies audit record logs successfully."""
    mock_query_job = MagicMock()
    mock_bq_client.query.return_value = mock_query_job
    
    record = AuditRecord(
        run_id="run-999",
        status="COMPLETED",
        rows_read=100,
        rows_loaded=90,
        rows_rejected=10,
        duration_ms=5000,
        error_message=None
    )
    
    bq_repository.record_audit(record)
    
    mock_bq_client.query.assert_called_once()
    mock_query_job.result.assert_called_once()
    args, kwargs = mock_bq_client.query.call_args
    assert "INSERT INTO `test-project.test_dataset.etl_audit_log`" in args[0]
    params = kwargs["job_config"].query_parameters
    assert params[0].name == "run_id"
    assert params[0].value == "run-999"
    assert params[1].name == "status"
    assert params[1].value == "COMPLETED"
