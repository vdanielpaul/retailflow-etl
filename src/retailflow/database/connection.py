"""PostgreSQL connection pool manager, retry strategy with jitter, and transaction context handling."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from psycopg2 import DataError, IntegrityError, InterfaceError, OperationalError
from psycopg2.pool import PoolError, ThreadedConnectionPool

from retailflow.config.settings import DatabaseSettings
from retailflow.exceptions.exceptions import (
    DatabaseConnectionError,
    DatabaseExecutionError,
    TransactionError,
)

logger = logging.getLogger(__name__)

# Exceptions classified as transient / retryable
RETRYABLE_EXCEPTIONS = (OperationalError, InterfaceError, PoolError)

# Exceptions classified as deterministic non-retryable failures
NON_RETRYABLE_EXCEPTIONS = (IntegrityError, DataError)


class DatabaseManager:
    """Thread-safe PostgreSQL database connection pool and transaction manager."""

    def __init__(self, db_settings: DatabaseSettings) -> None:
        self.settings = db_settings
        self._pool: ThreadedConnectionPool | None = None
        self._initialized = False

    def initialize_pool(self, max_retries: int = 3, base_delay_sec: float = 1.0) -> None:
        """Initialize ThreadedConnectionPool with exponential backoff and randomized jitter.

        Raises:
            DatabaseConnectionError: If pool creation fails after maximum retries.
        """
        if self._initialized and self._pool is not None:
            return

        attempt = 0
        while attempt < max_retries:
            attempt += 1
            try:
                logger.info(
                    f"Initializing database connection pool to {self.settings.host}:{self.settings.port}/{self.settings.name} (Attempt {attempt}/{max_retries})"
                )
                self._pool = ThreadedConnectionPool(
                    minconn=self.settings.min_connections,
                    maxconn=self.settings.max_connections,
                    host=self.settings.host,
                    port=self.settings.port,
                    dbname=self.settings.name,
                    user=self.settings.user,
                    password=self.settings.password,
                    connect_timeout=self.settings.connection_timeout,
                )
                self._pool.closed = False
                self._initialized = True
                logger.info("Database connection pool initialized successfully.")
                return
            except RETRYABLE_EXCEPTIONS as e:
                logger.warning(f"Transient database connection attempt {attempt} failed: {e}")
                if attempt >= max_retries:
                    raise DatabaseConnectionError(
                        f"Failed to connect to PostgreSQL database after {max_retries} attempts.",
                        details={"host": self.settings.host, "port": self.settings.port, "db": self.settings.name},
                    ) from e
                # Calculate backoff delay with randomized jitter to prevent thundering herd
                jitter = random.uniform(0.8, 1.2)
                delay = (base_delay_sec * (2 ** (attempt - 1))) * jitter
                time.sleep(delay)
            except Exception as e:
                raise DatabaseConnectionError(f"Fatal connection pool error: {e}") from e

    def close_pool(self) -> None:
        """Close all connections in the pool."""
        if self._pool is not None and not self._pool.closed:
            self._pool.closeall()
            self._initialized = False
            logger.info("Database connection pool closed.")

    @contextmanager
    def get_connection(self) -> Generator[Any, None, None]:
        """Context manager yielding a database connection from the pool.

        Yields:
            psycopg2 connection object.

        Raises:
            DatabaseConnectionError: If connection cannot be retrieved from pool.
        """
        if not self._initialized or self._pool is None:
            self.initialize_pool()

        try:
            assert self._pool is not None
            conn = self._pool.getconn()
        except RETRYABLE_EXCEPTIONS as e:
            raise DatabaseConnectionError(f"Connection pool acquisition failed: {e}") from e
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to acquire connection: {e}") from e

        try:
            yield conn
        finally:
            if self._pool is not None and not bool(self._pool.closed):
                self._pool.putconn(conn)

    @contextmanager
    def transaction(self) -> Generator[Any, None, None]:
        """Context manager for executing transactional database operations (BEGIN ... COMMIT/ROLLBACK).

        Yields:
            psycopg2 cursor object.

        Raises:
            TransactionError: If transaction commit or rollback fails.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except NON_RETRYABLE_EXCEPTIONS as e:
                conn.rollback()
                raise DatabaseExecutionError(f"Non-retryable data integrity error: {e}") from e
            except Exception as e:
                try:
                    conn.rollback()
                except Exception as rollback_err:
                    logger.critical(f"Failed to rollback transaction: {rollback_err}")
                raise TransactionError(f"Transaction aborted and rolled back due to error: {e}") from e
            finally:
                cursor.close()

    def health_check(self) -> bool:
        """Perform database connection health check (SELECT 1).

        Returns:
            True if database is responsive, False otherwise.
        """
        try:
            with self.get_connection() as conn, conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
                return result is not None and result[0] == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
