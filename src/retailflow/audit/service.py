"""Audit service managing event instantiation and publisher dispatch."""

from __future__ import annotations

import contextlib
import uuid
from datetime import datetime, timezone
from typing import Any

from retailflow.audit.models import AuditEvent, AuditSeverity, FailureCategory, PipelineLifecycleEvent
from retailflow.audit.publisher import BaseAuditPublisher, ConsolePublisher


class AuditService:
    """Service generating structured AuditEvent objects and dispatching to publishers."""

    def __init__(self, publishers: list[BaseAuditPublisher] | None = None) -> None:
        self.publishers = publishers or [ConsolePublisher()]
        self.events: list[AuditEvent] = []

    def record_event(
        self,
        run_id: str,
        event_name: PipelineLifecycleEvent,
        severity: AuditSeverity,
        stage: str,
        message: str = "",
        duration_ms: float = 0.0,
        failure_category: FailureCategory | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Create and publish a lifecycle audit event.

        Returns:
            Instantiated AuditEvent object.
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            run_id=run_id,
            event_name=event_name,
            severity=severity,
            timestamp=datetime.now(timezone.utc).isoformat(),
            stage=stage,
            duration_ms=duration_ms,
            message=message,
            failure_category=failure_category,
            details=details or {},
        )
        self.events.append(event)

        for pub in self.publishers:
            with contextlib.suppress(Exception):
                pub.publish(event)

        return event
