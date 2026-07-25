# Metadata database repository abstractions and BigQuery adapter

from abc import ABC, abstractmethod
from google.cloud import bigquery
from google.cloud.bigquery import ScalarQueryParameter
from google.api_core.exceptions import GoogleAPICallError
from retailflow.cloud.exceptions import WatermarkLookupError, MetadataPersistenceError
from retailflow.cloud.repositories.models import WatermarkRecord, AuditRecord, DuplicateLookupResult
from retailflow.cloud.repositories.sql import watermark_queries, audit_queries

class MetadataRepository(ABC):
    """Abstract interface defining the metadata persistence database boundaries (watermarks and audits)."""
    
    @abstractmethod
    def lookup_duplicate(self, file_hash: str) -> DuplicateLookupResult:
        """Query if the file hash has already been processed.

        Args:
            file_hash: Calculated SHA-256 hash of GCS object.

        Returns:
            DuplicateLookupResult model details.
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

class BigQueryMetadataRepository(MetadataRepository):
    """GCP BigQuery adapter implementing the MetadataRepository interface."""
    
    def __init__(self, client: bigquery.Client, project_id: str, dataset_id: str, environment: str = "dev") -> None:
        self.client = client
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.environment = environment
        
        # Standardized labels applied to all BigQuery operations for costing and audit tracking
        self.job_labels = {
            "project": "retailflow-etl",
            "environment": self.environment,
            "managed_by": "terraform",
            "component": "ingest-metadata-repo"
        }

    def lookup_duplicate(self, file_hash: str) -> DuplicateLookupResult:
        query_str = watermark_queries.CHECK_DUPLICATE_HASH.format(
            project_id=self.project_id,
            dataset_id=self.dataset_id
        )
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                ScalarQueryParameter("file_hash", "STRING", file_hash)
            ],
            labels=self.job_labels
        )
        try:
            query_job = self.client.query(query_str, job_config=job_config)
            results = list(query_job.result())
            
            if len(results) > 0:
                row = results[0]
                return DuplicateLookupResult(
                    is_duplicate=True,
                    run_id=row.get("run_id"),
                    ingested_at=row.get("ingested_at")
                )
            
            return DuplicateLookupResult(is_duplicate=False)
        except GoogleAPICallError as err:
            raise WatermarkLookupError(f"BigQuery API error checking duplicate watermark: {str(err)}") from err
        except Exception as err:
            raise WatermarkLookupError(f"Unexpected database error checking duplicate watermark: {str(err)}") from err

    def create_watermark(self, record: WatermarkRecord) -> None:
        query_str = watermark_queries.INSERT_WATERMARK.format(
            project_id=self.project_id,
            dataset_id=self.dataset_id
        )
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                ScalarQueryParameter("file_hash", "STRING", record.file_hash),
                ScalarQueryParameter("filename", "STRING", record.filename),
                ScalarQueryParameter("ingested_at", "TIMESTAMP", record.ingested_at),
                ScalarQueryParameter("run_id", "STRING", record.run_id),
            ],
            labels=self.job_labels
        )
        try:
            query_job = self.client.query(query_str, job_config=job_config)
            query_job.result()
        except GoogleAPICallError as err:
            raise MetadataPersistenceError(f"BigQuery API error writing watermark record: {str(err)}") from err
        except Exception as err:
            raise MetadataPersistenceError(f"Unexpected database error writing watermark record: {str(err)}") from err

    def record_audit(self, record: AuditRecord) -> None:
        query_str = audit_queries.INSERT_AUDIT_LOG.format(
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
            ],
            labels=self.job_labels
        )
        try:
            query_job = self.client.query(query_str, job_config=job_config)
            query_job.result()
        except GoogleAPICallError as err:
            raise MetadataPersistenceError(f"BigQuery API error writing audit log record: {str(err)}") from err
        except Exception as err:
            raise MetadataPersistenceError(f"Unexpected database error writing audit log record: {str(err)}") from err
