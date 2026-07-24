"""Audit event publisher interface and monitoring extension points."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from retailflow.audit.models import AuditEvent

logger = logging.getLogger(__name__)


class BaseAuditPublisher(ABC):
    """Abstract Base Class for publishing audit events to external telemetry systems."""

    @abstractmethod
    def publish(self, event: AuditEvent) -> None:
        """Publish audit event to target observability backend."""
        pass


class ConsolePublisher(BaseAuditPublisher):
    """Default audit publisher outputting event records to standard logger."""

    def publish(self, event: AuditEvent) -> None:
        logger.info(f"AUDIT EVENT [{event.severity.value}] [{event.event_name.value}]: {event.message}")


class PrometheusPublisherStub(BaseAuditPublisher):
    """Extension stub for publishing metrics to Prometheus Gateway."""

    def publish(self, event: AuditEvent) -> None:
        logger.debug(f"Prometheus metric push stub: {event.event_name.value}")


class AlertPublisherStub(BaseAuditPublisher):
    """Extension stub for firing operational alerts to Slack / Teams / PagerDuty."""

    def publish(self, event: AuditEvent) -> None:
        if event.severity.value in ("ERROR", "CRITICAL"):
            logger.warning(f"ALERT STUB [{event.severity.value}]: {event.message}")
