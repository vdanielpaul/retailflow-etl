"""Watermark management engine interacting with metadata.etl_watermark table."""

from __future__ import annotations

import logging

from retailflow.database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class WatermarkManager:
    """Manages high-watermark timestamp and file hash tracking in metadata schema."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def get_latest_watermark(self) -> str:
        """Fetch latest processed watermark timestamp from metadata.etl_watermark table.

        Returns:
            ISO timestamp string or default epoch string if empty.
        """
        try:
            with self.db_manager.get_connection() as conn, conn.cursor() as cursor:
                cursor.execute(
                    "SELECT MAX(processed_at) FROM metadata.etl_watermark WHERE status = 'SUCCESS';"
                )
                row = cursor.fetchone()
                if row and row[0] is not None:
                    return row[0].isoformat()
        except Exception as e:
            logger.warning(f"Could not retrieve watermark timestamp: {e}")
        return "1970-01-01T00:00:00+00:00"

    def is_file_processed(self, file_hash: str) -> bool:
        """Check if file with given SHA-256 hash has already been successfully loaded.

        Args:
            file_hash: SHA-256 string.

        Returns:
            True if file hash exists in metadata.etl_watermark with status SUCCESS.
        """
        try:
            with self.db_manager.get_connection() as conn, conn.cursor() as cursor:
                cursor.execute(
                    "SELECT watermark_id FROM metadata.etl_watermark WHERE file_hash = %s AND status = 'SUCCESS';",
                    (file_hash,),
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.warning(f"Could not check file watermark: {e}")
            return False
