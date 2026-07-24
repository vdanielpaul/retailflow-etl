"""Unit tests for HealthChecker."""

from pathlib import Path
from unittest.mock import MagicMock

from retailflow.config.settings import Settings
from retailflow.health.checker import HealthChecker


def test_health_checker_success(tmp_path: Path) -> None:
    """Test HealthChecker returns healthy status on valid settings."""
    settings = Settings()
    settings.paths.raw_dir = tmp_path / "raw"
    settings.paths.staging_dir = tmp_path / "staging"
    settings.paths.processed_dir = tmp_path / "processed"
    settings.paths.archive_dir = tmp_path / "archive"
    settings.paths.bad_records_dir = tmp_path / "bad"
    settings.paths.log_dir = tmp_path / "logs"

    mock_db = MagicMock()
    mock_db.health_check.return_value = True

    checker = HealthChecker(settings, db_manager=mock_db)
    result = checker.run_all_checks()

    assert result.is_healthy is True
    assert result.checks["config_validity"] is True
    assert result.checks["directory_structure"] is True
    assert result.checks["write_permissions"] is True
    assert result.checks["database_connectivity"] is True
    assert len(result.failures) == 0
