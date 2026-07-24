"""Unit tests for RetailFlow ETL logging framework and redaction engine."""

import json
import logging
from pathlib import Path

from retailflow.utils.logger import (
    JSONFormatter,
    redact_sensitive_data,
    set_log_context,
    setup_logger,
)


def test_redact_sensitive_data() -> None:
    """Test sensitive data redactor masks passwords, tokens, and connection strings."""
    raw = "Connecting with password='secret_password_123' and token='abc123token'"
    redacted = redact_sensitive_data(raw)

    assert "secret_password_123" not in redacted
    assert "abc123token" not in redacted
    assert "********" in redacted

    conn_str = "postgres://user:super_secret_pass@localhost:5432/retailflow_dw"
    redacted_conn = redact_sensitive_data(conn_str)
    assert "super_secret_pass" not in redacted_conn
    assert "********" in redacted_conn


def test_logger_setup_and_redaction(tmp_path: Path) -> None:
    """Test logger setup and verify file logs mask passwords automatically."""
    logger = setup_logger(
        name="test_logger",
        log_level="DEBUG",
        log_dir=tmp_path,
        log_filename="test_run.log",
        console_output=True,
        file_output=True,
    )

    logger.info("Connecting using password='my_db_password'")
    log_file = tmp_path / "test_run.log"

    content = log_file.read_text(encoding="utf-8")
    assert "my_db_password" not in content
    assert "********" in content


def test_json_formatter_extended_fields() -> None:
    """Test JSON log formatter includes pipeline_run_id, batch_id, and environment."""
    formatter = JSONFormatter()
    set_log_context(
        run_id="run-999",
        batch_id="BATCH-20260724",
        filename="sales_001.csv",
        stage="ROW_VALIDATION",
        environment="production",
    )

    record = logging.LogRecord(
        name="retailflow",
        level=logging.INFO,
        pathname="test.py",
        lineno=42,
        msg="Validated 100 rows",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["pipeline_run_id"] == "run-999"
    assert parsed["batch_id"] == "BATCH-20260724"
    assert parsed["source_filename"] == "sales_001.csv"
    assert parsed["execution_stage"] == "ROW_VALIDATION"
    assert parsed["environment"] == "production"
