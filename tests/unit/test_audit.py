"""Unit tests for RetailFlow audit subsystem."""

from unittest.mock import MagicMock

from retailflow.audit.models import AuditSeverity, PipelineLifecycleEvent
from retailflow.audit.publisher import ConsolePublisher
from retailflow.audit.repository import AuditRepository
from retailflow.audit.service import AuditService


def test_audit_service_recording() -> None:
    """Test AuditService records lifecycle events."""
    publisher = MagicMock(spec=ConsolePublisher)
    service = AuditService(publishers=[publisher])

    evt = service.record_event(
        run_id="run-100",
        event_name=PipelineLifecycleEvent.PIPELINE_STARTED,
        severity=AuditSeverity.INFO,
        stage="INITIALIZATION",
        message="Started run",
    )

    assert evt.run_id == "run-100"
    assert evt.event_name == PipelineLifecycleEvent.PIPELINE_STARTED
    assert len(service.events) == 1
    publisher.publish.assert_called_once_with(evt)


def test_audit_repository_search_api() -> None:
    """Test AuditRepository query methods."""
    mock_db = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db.get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [("run-001", "SUCCESS", 100, "2026-07-24 10:00:00")]

    repo = AuditRepository(mock_db)
    recent = repo.list_recent_runs(limit=5)

    assert len(recent) == 1
    assert recent[0]["pipeline_run_id"] == "run-001"
