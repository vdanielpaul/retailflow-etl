"""Unit tests for RetailFlow ETL database connection manager and transaction layer."""

from unittest.mock import MagicMock, patch

import pytest

from retailflow.config.settings import DatabaseSettings
from retailflow.database.connection import DatabaseManager
from retailflow.exceptions.exceptions import TransactionError


@pytest.fixture
def db_settings() -> DatabaseSettings:
    """Fixture providing DatabaseSettings instance."""
    return DatabaseSettings(
        host="localhost",
        port=5432,
        name="retailflow_dw",
        user="test_user",
        password="test_password",
    )


@patch("retailflow.database.connection.ThreadedConnectionPool")
def test_database_manager_pool_initialization(mock_pool_cls: MagicMock, db_settings: DatabaseSettings) -> None:
    """Test successful database connection pool initialization."""
    mock_pool_instance = MagicMock()
    mock_pool_instance.closed = False
    mock_pool_cls.return_value = mock_pool_instance

    db_mgr = DatabaseManager(db_settings)
    db_mgr.initialize_pool()

    assert db_mgr._initialized is True
    mock_pool_cls.assert_called_once_with(
        minconn=1,
        maxconn=10,
        host="localhost",
        port=5432,
        dbname="retailflow_dw",
        user="test_user",
        password="test_password",
        connect_timeout=30,
    )


@patch("retailflow.database.connection.ThreadedConnectionPool")
def test_get_connection_context_manager(mock_pool_cls: MagicMock, db_settings: DatabaseSettings) -> None:
    """Test acquiring and releasing connection from pool context manager."""
    mock_pool_instance = MagicMock()
    mock_pool_instance.closed = False
    mock_conn = MagicMock()
    mock_pool_instance.getconn.return_value = mock_conn
    mock_pool_cls.return_value = mock_pool_instance

    db_mgr = DatabaseManager(db_settings)
    db_mgr.initialize_pool()

    with db_mgr.get_connection() as conn:
        assert conn == mock_conn

    mock_pool_instance.getconn.assert_called_once()
    mock_pool_instance.putconn.assert_called_once_with(mock_conn)


@patch("retailflow.database.connection.ThreadedConnectionPool")
def test_transaction_commit_success(mock_pool_cls: MagicMock, db_settings: DatabaseSettings) -> None:
    """Test successful transaction execution triggers commit."""
    mock_pool_instance = MagicMock()
    mock_pool_instance.closed = False
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_pool_instance.getconn.return_value = mock_conn
    mock_pool_cls.return_value = mock_pool_instance

    db_mgr = DatabaseManager(db_settings)
    db_mgr.initialize_pool()

    with db_mgr.transaction() as cursor:
        cursor.execute("INSERT INTO test VALUES (1);")

    mock_cursor.execute.assert_called_once_with("INSERT INTO test VALUES (1);")
    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()


@patch("retailflow.database.connection.ThreadedConnectionPool")
def test_transaction_rollback_on_error(mock_pool_cls: MagicMock, db_settings: DatabaseSettings) -> None:
    """Test transaction rollback triggered on execution exception."""
    mock_pool_instance = MagicMock()
    mock_pool_instance.closed = False
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_pool_instance.getconn.return_value = mock_conn
    mock_pool_cls.return_value = mock_pool_instance

    db_mgr = DatabaseManager(db_settings)
    db_mgr.initialize_pool()

    with pytest.raises(TransactionError), db_mgr.transaction() as cursor:
        cursor.execute("SELECT * FROM invalid_table;")
        raise ValueError("Query Execution Error")

    mock_conn.rollback.assert_called_once()
    mock_cursor.close.assert_called_once()


@patch("retailflow.database.connection.ThreadedConnectionPool")
def test_health_check_success(mock_pool_cls: MagicMock, db_settings: DatabaseSettings) -> None:
    """Test health check returns True on successful SELECT 1."""
    mock_pool_instance = MagicMock()
    mock_pool_instance.closed = False
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1,)
    mock_conn.cursor.return_value = mock_cursor
    mock_pool_instance.getconn.return_value = mock_conn
    mock_pool_cls.return_value = mock_pool_instance

    db_mgr = DatabaseManager(db_settings)
    db_mgr.initialize_pool()

    assert db_mgr.health_check() is True
