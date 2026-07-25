# Unit tests for BigQueryWatermarkRepository using BQ Client mocking

from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock, patch
from google.api_core.exceptions import GoogleAPICallError
from retailflow.cloud.exceptions import WatermarkLookupError, MetadataPersistenceError
from retailflow.cloud.repositories.models import WatermarkRecord, AuditRecord
from retailflow.cloud.repositories.watermark_repository import BigQueryWatermarkRepository

@pytest.fixture
def mock_bq_client():
    return MagicMock()

@pytest.fixture
def bq_repository(mock_bq_client):
    return BigQueryWatermarkRepository(
        client=mock_bq_client,
        project_id="test-project",
        dataset_id="test_dataset"
    )

def test_exists_duplicate_found(bq_repository, mock_bq_client):
    """Verifies exists returns True when BigQuery query returns rows."""
    mock_query_job = MagicMock()
    # Mocking rows returned (length of results > 0)
    mock_query_job.result.return_value = [MagicMock()] 
    mock_bq_client.query.return_value = mock_query_job

    result = bq_repository.exists("some-file-hash")
    
    assert result is True
    mock_bq_client.query.assert_called_once()
    args, kwargs = mock_bq_client.query.call_args
    assert "test-project.test_dataset.etl_watermark" in args[0]
    assert kwargs["job_config"].query_parameters[0].value == "some-file-hash"

def test_exists_duplicate_not_found(bq_repository, mock_bq_client):
    """Verifies exists returns False when BigQuery query returns empty rows."""
    mock_query_job = MagicMock()
    mock_query_job.result.return_value = [] # Empty results
    mock_bq_client.query.return_value = mock_query_job

    result = bq_repository.exists("new-file-hash")
    
    assert result is False
    mock_bq_client.query.assert_called_once()

def test_exists_bq_api_failure(bq_repository, mock_bq_client):
    """Verifies exists raises WatermarkLookupError when BigQuery client raises API exception."""
    class MockBigQueryError(GoogleAPICallError):
        pass
        
    mock_bq_client.query.side_effect = MockBigQueryError("BQ query timeout")

    with pytest.raises(WatermarkLookupError, match="BigQuery API error"):
        bq_repository.exists("hash")

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
