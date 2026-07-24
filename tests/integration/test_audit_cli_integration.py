"""Integration tests for production CLI runner, audit logging, and exit code mappings."""

from pathlib import Path
from unittest.mock import patch

from retailflow.cli import (
    EXIT_CONFIG_FAILURE,
    EXIT_SUCCESS,
    run_pipeline,
)


def test_cli_dry_run_mode(tmp_path: Path) -> None:
    """Test CLI execution in --dry-run mode returns success without database writes."""
    config_file = tmp_path / "base.yaml"
    config_file.write_text(
        f"""
pipeline:
  environment: "testing"
  batch_size: 1000
paths:
  raw_dir: "{tmp_path}"
  archive_dir: "{tmp_path / 'archive'}"
  log_dir: "{tmp_path / 'logs'}"
""",
        encoding="utf-8",
    )

    feed_file = tmp_path / "sales.csv"
    feed_file.write_text("transaction_id,store_id,product_id,employee_id,quantity,unit_price,transaction_time\nTX-1,STR-1,P-1,EMP-1,2,10.0,2026-01-01 10:00:00\n")

    with patch("retailflow.database.connection.DatabaseManager.health_check", return_value=True), patch("retailflow.incremental.watermark.WatermarkManager.is_file_processed", return_value=False):
        exit_code = run_pipeline(["--config", str(config_file), "--file", str(feed_file), "--dry-run"])

    assert exit_code == EXIT_SUCCESS


def test_cli_validation_only_mode(tmp_path: Path) -> None:
    """Test CLI execution in --validation-only mode exits cleanly after validation."""
    config_file = tmp_path / "base.yaml"
    config_file.write_text(
        f"""
pipeline:
  environment: "testing"
  batch_size: 1000
paths:
  raw_dir: "{tmp_path}"
  archive_dir: "{tmp_path / 'archive'}"
  log_dir: "{tmp_path / 'logs'}"
""",
        encoding="utf-8",
    )

    feed_file = tmp_path / "sales.csv"
    feed_file.write_text("transaction_id,store_id,product_id,employee_id,quantity,unit_price,transaction_time\nTX-1,STR-1,P-1,EMP-1,2,10.0,2026-01-01 10:00:00\n")

    with patch("retailflow.database.connection.DatabaseManager.health_check", return_value=True), patch("retailflow.incremental.watermark.WatermarkManager.is_file_processed", return_value=False):
        exit_code = run_pipeline(["--config", str(config_file), "--file", str(feed_file), "--validation-only"])

    assert exit_code == EXIT_SUCCESS


def test_cli_missing_config_exit_code() -> None:
    """Test CLI returns EXIT_CONFIG_FAILURE on non-existent config file."""
    exit_code = run_pipeline(["--config", "non_existent_config.yaml"])
    assert exit_code == EXIT_CONFIG_FAILURE
