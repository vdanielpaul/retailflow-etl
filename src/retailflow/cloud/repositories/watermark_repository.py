# Watermark database repository abstractions and BigQuery adapter

from abc import ABC, abstractmethod
from google.cloud import bigquery
from google.cloud.bigquery import ScalarQueryParameter
from google.api_core.exceptions import GoogleAPICallError
from retailflow.cloud.exceptions import WatermarkLookupError, MetadataPersistenceError
from retailflow.cloud.repositories.models import WatermarkRecord, AuditRecord
from retailflow.cloud.repositories.sql import queries

class WatermarkRepository(ABC):
    """Abstract interface defining the metadata persistence database boundaries."""
    
    @abstractmethod
    def exists(self, file_hash: str) -> bool:
        """Query if the file hash has already been processed.

        Args:
            file_hash: Calculated SHA-256 hash of GCS object.

        Returns:
            True if hash already exists in metadata logs, False otherwise.
        """
        pass

    @abstractmethod
    def create_watermark(self, record: WatermarkRecord) -> None:
        """Register the file ingestion details into the watermark database.

        Args:
            record: WatermarkRecord domain model.
        """
        pass

    @abstractmethod
    def record_audit(self, record: AuditRecord) -> None:
        """Log an ETL execution audit metric record into the database.

        Args:
            record: AuditRecord domain model.
        """
        pass

class BigQueryWatermarkRepository(WatermarkRepository):
    """GCP BigQuery adapter implementing the WatermarkRepository interface."""
    
    def __init__(self, client: bigquery.Client, project_id: str, dataset_id: str) -> None:
        self.client = client
        self.project_id = project_id
        self.dataset_id = dataset_id

    def exists(self, file_hash: str) -> bool:
        query_str = queries.CHECK_DUPLICATE_HASH.format(
            project_id=self.project_id,
            dataset_id=self.dataset_id
        )
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                ScalarQueryParameter("file_hash", "STRING", file_hash)
            ]
        )
        try:
            query_job = self.client.query(query_str, job_config=job_config)
            results = query_job.result()
            # If any rows are returned, the file hash has been processed
            return len(list(results)) > 0
        except GoogleAPICallError as err:
            raise WatermarkLookupError(f"BigQuery API error checking duplicate watermark: {str(err)}") from err
        except Exception as err:
            raise WatermarkLookupError(f"Unexpected database error checking duplicate watermark: {str(err)}") from err

    def create_watermark(self, record: WatermarkRecord) -> None:
        query_str = queries.INSERT_WATERMARK.format(
            project_id=self.project_id,
            dataset_id=self.dataset_id
        )
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                ScalarQueryParameter("file_hash", "STRING", record.file_hash),
                ScalarQueryParameter("filename", "STRING", record.filename),
                ScalarQueryParameter("ingested_at", "TIMESTAMP", record.ingested_at),
                ScalarQueryParameter("run_id", "STRING", record.run_id),
            ]
        )
        try:
            query_job = self.client.query(query_str, job_config=job_config)
            query_job.result() # Wait for query to complete execution
        except GoogleAPICallError as err:
            raise MetadataPersistenceError(f"BigQuery API error writing watermark record: {str(err)}") from err
        except Exception as err:
            raise MetadataPersistenceError(f"Unexpected database error writing watermark record: {str(err)}") from err

    def record_audit(self, record: AuditRecord) -> None:
        query_str = queries.INSERT_AUDIT_LOG.format(
            project_id=self.project_id,
            dataset_id=self.dataset_id
        )
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                ScalarQueryParameter("run_id", "STRING", record.run_id),
                ScalarQueryParameter("status", "STRING", record.status),
                ScalarQueryParameter("rows_read", "INT64", record.rows_read),
                ScalarQueryParameter("rows_loaded", "INT64", record.rows_loaded),
                ScalarQueryParameter("rows_rejected", "INT64", record.rows_rejected),
                ScalarQueryParameter("duration_ms", "INT64", record.duration_ms),
                ScalarQueryParameter("error_message", "STRING", record.error_message),
                ScalarQueryParameter("updated_at", "TIMESTAMP", record.updated_at),
            ]
        )
        try:
            query_job = self.client.query(query_str, job_config=job_config)
            query_job.result()
        except GoogleAPICallError as err:
            raise MetadataPersistenceError(f"BigQuery API error writing audit log record: {str(err)}") from err
        except Exception as err:
            raise MetadataPersistenceError(f"Unexpected database error writing audit log record: {str(err)}") from err
