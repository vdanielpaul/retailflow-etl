# Coordinates raw Pub/Sub message decoding, metadata validation, and routing

import base64
import json
import uuid
from typing import Any
from retailflow.cloud.application.ingestion_service import IngestionApplicationService
from retailflow.cloud.dependencies import IngestionDependencyContainer
from retailflow.cloud.exceptions import InvalidEventError
from retailflow.cloud.logging.logger import get_cloud_logger
from retailflow.cloud.models.events import GcsNotificationPayload

logger = get_cloud_logger()

class IngestEventHandler:
    """Orchestrates parsing of incoming storage notifications, validating parameters, and delegating execution."""

    def __init__(self, container: IngestionDependencyContainer) -> None:
        self.container = container
        self.service = IngestionApplicationService(container)

    def handle_ingestion_message(self, pubsub_message: dict[str, Any]) -> dict[str, Any]:
        """Decodes the Pub/Sub base64 payload, validates metadata schemas, and delegates to the application service.

        Args:
            pubsub_message: Standard dictionary representing a Pub/Sub message wrapper.

        Returns:
            Dictionary containing operation status details.
        """
        # 1. Parse the Pub/Sub message envelope
        data_b64 = pubsub_message.get("data")
        if not data_b64:
            raise InvalidEventError("Invalid Pub/Sub payload structure: missing 'data' field.")

        # 2. Extract or initialize correlation ID for distributed trace tracking
        attributes = pubsub_message.get("attributes", {}) or {}
        correlation_id = attributes.get("correlation_id")
        if not correlation_id:
            correlation_id = f"corr-{uuid.uuid4().hex[:12]}"

        # 3. Decode the base64 payload
        try:
            decoded_bytes = base64.b64decode(data_b64)
            raw_payload = json.loads(decoded_bytes.decode("utf-8"))
        except Exception as err:
            raise InvalidEventError(f"Failed to decode base64 Pub/Sub payload JSON: {str(err)}") from err

        # 4. Enforce validation against GCS notification schemas
        try:
            gcs_event = GcsNotificationPayload.model_validate(raw_payload)
        except Exception as err:
            raise InvalidEventError(f"Metadata schema validation failed: {str(err)}") from err

        # 5. Hand execution over to the stateless Application Ingestion Service
        return self.service.process_file_upload(gcs_event, correlation_id)
