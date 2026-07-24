"""Transactional coordinator managing atomic warehouse boundaries and savepoints."""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from retailflow.database.connection import DatabaseManager
from retailflow.exceptions.exceptions import TransactionError

logger = logging.getLogger(__name__)


class TransactionCoordinator:
    """Manages transactional scope, savepoints, and failure recovery across warehouse loading stages."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager
        self.rollback_count = 0
        self.savepoint_rollbacks = 0

    @contextmanager
    def atomic_transaction(self) -> Generator[Any, None, None]:
        """Context manager executing atomic transaction scope (BEGIN ... COMMIT / ROLLBACK).

        Yields:
            psycopg2 cursor object.
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            try:
                logger.debug("Beginning atomic warehouse transaction...")
                yield cursor
                conn.commit()
                logger.debug("Atomic warehouse transaction committed successfully.")
            except Exception as e:
                self.rollback_count += 1
                try:
                    conn.rollback()
                    logger.warning("Transaction rolled back due to error.")
                except Exception as rollback_err:
                    logger.critical(f"Failed to rollback transaction: {rollback_err}")
                raise TransactionError(f"Atomic warehouse transaction failed and was rolled back: {e}") from e
            finally:
                cursor.close()

    @contextmanager
    def savepoint(self, cursor: Any, name: str) -> Generator[None, None, None]:
        """Context manager establishing a SQL SAVEPOINT within an active transaction.

        Args:
            cursor: Active psycopg2 cursor.
            name: Savepoint identifier name.
        """
        savepoint_name = f"sp_{name}"
        try:
            cursor.execute(f"SAVEPOINT {savepoint_name};")
            yield
            cursor.execute(f"RELEASE SAVEPOINT {savepoint_name};")
        except Exception as e:
            self.savepoint_rollbacks += 1
            cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name};")
            logger.warning(f"Rolled back to SAVEPOINT {savepoint_name} due to error: {e}")
            raise
