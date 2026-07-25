# Application service orchestrating the ingestion flow
# Decoupled from Pub/Sub parsing and database persistence implementations.

import uuid
from datetime import datetime, timezone
from typing import Any
from retailflow.cloud.dependencies import IngestionDependencyContainer
from retailflow.cloud.exceptions import DuplicateFileError
from retailflow.cloud.logging.logger import get_cloud_logger
from retailflow.cloud.models.events import GcsNotificationPayload, FileAcceptedEvent
from retailflow.cloud.repositories.models import WatermarkRecord, AuditRecord

logger = get_cloud_logger()

class IngestionApplicationService:
    """Coordinating service that implements file verification checks, deduplication, and workflow triggers."""

    def __init__(self, container: IngestionDependencyContainer) -> None:
        self.settings = container.settings
        self.metadata_repository = container.metadata_repository
        self.storage_service = container.storage_service
        self.event_publisher = container.event_publisher

    def process_file_upload(self, gcs_event: GcsNotificationPayload, correlation_id: str) -> dict[str, Any]:
        """Orchestrates the metadata checks, file hashing, duplicate validation, and triggers downstream.

        Args:
            gcs_event: Parsed GCS object finalized event.
            correlation_id: Tracing identifier.

        Returns:
            Dictionary containing operation status details.
        """
        # Generate operational run tracking keys
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        
        # Log entry point using structured formats
        logger.info(
            f"Starting file upload processing ingestion flow for: gs://{gcs_event.bucket}/{gcs_event.name}",
            extra={"extra_fields": {
                "correlation_id": correlation_id,
                "ingestion_id": run_id,
                "bucket": gcs_event.bucket,
                "object_name": gcs_event.name,
                "generation": gcs_event.generation,
                "event_type": "FILE_UPLOAD_START"
            }}
        )

        # Initialize raw audit logging
        audit_init = AuditRecord(
            run_id=run_id,
            status="INGESTING",
            rows_read=0,
            rows_loaded=0,
            rows_rejected=0,
            duration_ms=0,
            error_message=None
        )
        self.metadata_repository.record_audit(audit_init)

        # 1. Calculate File Hashing via streaming storage read API
        file_hash = self.storage_service.calculate_sha256(gcs_event.bucket, gcs_event.name)
        
        # 2. Duplicate Detection
        duplicate_check = self.metadata_repository.lookup_duplicate(file_hash)
        if duplicate_check.is_duplicate:
            logger.warning(
                f"Duplicate upload detected. Rejecting file processing: gs://{gcs_event.bucket}/{gcs_event.name}. "
                f"Historically processed in run {duplicate_check.run_id} at {duplicate_check.ingested_at}",
                extra={"extra_fields": {
                    "correlation_id": correlation_id,
                    "ingestion_id": run_id,
                    "file_hash": file_hash,
                    "event_type": "FILE_DUPLICATE_REJECTED",
                    "duplicate_of_run": duplicate_check.run_id
                }}
            )
            audit_fail = AuditRecord(
                run_id=run_id,
                status="REJECTED_DUPLICATE",
                error_message=f"Duplicate file hash detected: {file_hash}"
            )
            self.metadata_repository.record_audit(audit_fail)
            raise DuplicateFileError(f"Duplicate file hash detected: {file_hash}")

        # 3. Register Watermark Ingestion
        watermark_rec = WatermarkRecord(
            file_hash=file_hash,
            filename=gcs_event.name,
            run_id=run_id
        )
        self.metadata_repository.create_watermark(watermark_rec)

        # 4. Construct Structured Event Contract Payload
        accepted_event = FileAcceptedEvent(
            event_id=f"evt-{uuid.uuid4().hex[:8]}",
            ingestion_id=run_id,
            correlation_id=correlation_id,
            bucket=gcs_event.bucket,
            object_name=gcs_event.name,
            generation=gcs_event.generation,
            file_hash=file_hash,
            received_at=datetime.now(timezone.utc).isoformat(),
            event_version="1.0",
            event_type="FILE_ACCEPTED"
        )

        # 5. Publish Ingest trigger event downstream
        self.event_publisher.publish_accepted_event(accepted_event)

        # 6. Update audit log on success
        audit_success = AuditRecord(
            run_id=run_id,
            status="INGESTED",
            duration_ms=100
        )
        self.metadata_repository.record_audit(audit_success)

        logger.info(
            f"File accepted and trigger event successfully forwarded downstream for: gs://{gcs_event.bucket}/{gcs_event.name}",
            extra={"extra_fields": {
                "correlation_id": correlation_id,
                "ingestion_id": run_id,
                "file_hash": file_hash,
                "event_type": "FILE_ACCEPTED"
            }}
        )

        return {
            "status": "ACCEPTED",
            "run_id": run_id,
            "correlation_id": correlation_id,
            "file_hash": file_hash
        }
