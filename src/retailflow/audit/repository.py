"""Audit repository interface executing queries against metadata.etl_audit_log."""

from __future__ import annotations

import logging
from typing import Any

from retailflow.database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class AuditRepository:
    """Repository persisting and retrieving audit execution logs from metadata schema."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Fetch audit log record by pipeline_run_id."""
        try:
            with self.db_manager.get_connection() as conn, conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM metadata.etl_audit_log WHERE pipeline_run_id = %s;", (run_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {"run_id": row[0], "pipeline_run_id": row[1], "status": row[8]}
        except Exception as e:
            logger.warning(f"Could not fetch audit run {run_id}: {e}")
        return None

    def list_recent_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        """Fetch list of recent pipeline runs."""
        results = []
        try:
            with self.db_manager.get_connection() as conn, conn.cursor() as cursor:
                cursor.execute(
                    "SELECT pipeline_run_id, status, rows_loaded, start_time FROM metadata.etl_audit_log ORDER BY start_time DESC LIMIT %s;",
                    (limit,),
                )
                for row in cursor.fetchall():
                    results.append(
                        {"pipeline_run_id": row[0], "status": row[1], "rows_loaded": row[2], "start_time": str(row[3])}
                    )
        except Exception as e:
            logger.warning(f"Could not list recent audit runs: {e}")
        return results

    def get_failed_runs(self) -> list[dict[str, Any]]:
        """Fetch list of failed pipeline executions."""
        results = []
        try:
            with self.db_manager.get_connection() as conn, conn.cursor() as cursor:
                cursor.execute(
                    "SELECT pipeline_run_id, status, error_count, start_time FROM metadata.etl_audit_log WHERE status = 'FAILED' ORDER BY start_time DESC;"
                )
                for row in cursor.fetchall():
                    results.append(
                        {"pipeline_run_id": row[0], "status": row[1], "error_count": row[2], "start_time": str(row[3])}
                    )
        except Exception as e:
            logger.warning(f"Could not fetch failed audit runs: {e}")
        return results
