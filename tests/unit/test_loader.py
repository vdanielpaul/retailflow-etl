"""Unit tests for RetailFlow database loader framework."""

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from retailflow.config.settings import Settings
from retailflow.exceptions.exceptions import TransactionError
from retailflow.loader.bulk import bulk_load_dataframe
from retailflow.loader.fact_loader import FactLoader
from retailflow.loader.transactional import TransactionCoordinator
from retailflow.models.loader import LoadStrategy
from retailflow.pipeline.context import PipelineContext


@pytest.fixture
def mock_context(tmp_path: Path) -> PipelineContext:
    """Fixture providing PipelineContext with mock database manager."""
    settings = Settings()
    mock_db = MagicMock()
    mock_conn = MagicMock()
    mock_conn.encoding = "UTF8"
    mock_db.get_connection.return_value.__enter__.return_value = mock_conn

    mock_logger = MagicMock()

    sample_file = tmp_path / "sales.csv"
    sample_file.write_text("transaction_id,quantity\nTX-1,5\n")

    return PipelineContext(
        configuration=settings,
        database=mock_db,
        logger=mock_logger,
        source_file=sample_file,
    )


def test_bulk_load_dataframe_execute_values() -> None:
    """Test bulk load executing execute_values strategy."""
    mock_cursor = MagicMock()
    mock_cursor.connection.encoding = "UTF8"
    df = pd.DataFrame({"col1": [1, 2], "col2": ["A", "B"]})

    rows, duration = bulk_load_dataframe(
        cursor=mock_cursor,
        df=df,
        table_name="test_table",
        columns=["col1", "col2"],
        strategy=LoadStrategy.EXECUTE_VALUES,
    )

    assert rows == 2
    assert duration >= 0.0


def test_transaction_coordinator_rollback() -> None:
    """Test transaction coordinator executes rollback on error."""
    mock_db = MagicMock()
    mock_conn = MagicMock()
    mock_conn.encoding = "UTF8"
    mock_cursor = MagicMock()
    mock_db.get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    coordinator = TransactionCoordinator(mock_db)

    with pytest.raises(TransactionError), coordinator.atomic_transaction():
        raise ValueError("Database write error")

    assert coordinator.rollback_count == 1
    mock_conn.rollback.assert_called_once()


def test_fact_loader_batch_chunking() -> None:
    """Test FactLoader splits rows into batch chunks."""
    mock_cursor = MagicMock()
    mock_cursor.connection.encoding = "UTF8"
    df = pd.DataFrame(
        {
            "transaction_id": [f"TX-{i}" for i in range(10)],
            "date_sk": [20260724] * 10,
            "customer_sk": [None] * 10,
            "product_sk": [1] * 10,
            "store_sk": [1] * 10,
            "employee_sk": [1] * 10,
            "transaction_time": ["2026-07-24 10:00:00"] * 10,
            "quantity": [1] * 10,
            "unit_price": [10.0] * 10,
            "discount_amount": [0.0] * 10,
            "net_sales_amount": [10.0] * 10,
            "audit_run_id": [1] * 10,
        }
    )

    loader = FactLoader()
    loaded, batches, db_time, durations = loader.load_fact_sales(
        cursor=mock_cursor, df=df, strategy=LoadStrategy.EXECUTE_VALUES, batch_size=4
    )

    assert loaded == 10
    assert batches == 3  # 4 + 4 + 2 = 3 batches
    assert len(durations) == 3
