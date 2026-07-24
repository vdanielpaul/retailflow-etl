"""Unit tests for RetailFlow ETL configuration system."""

from pathlib import Path

import pytest

from retailflow.config.loader import load_config
from retailflow.config.settings import Settings
from retailflow.exceptions.exceptions import ConfigurationError


def test_default_config_loading(tmp_path: Path) -> None:
    """Test loading base configuration file."""
    config_file = tmp_path / "base.yaml"
    config_file.write_text(
        """
pipeline:
  environment: "testing"
  batch_size: 5000
database:
  host: "test-host"
  port: 5432
paths:
  raw_dir: "data/raw"
  archive_dir: "data/archive"
  log_dir: "logs"
""",
        encoding="utf-8",
    )

    settings = load_config(config_file)
    assert isinstance(settings, Settings)
    assert settings.pipeline.environment == "testing"
    assert settings.pipeline.batch_size == 5000


def test_layered_config_inheritance(tmp_path: Path) -> None:
    """Test inherited configuration overrides base values."""
    base_file = tmp_path / "base.yaml"
    base_file.write_text(
        """
pipeline:
  environment: "base"
  batch_size: 10000
database:
  host: "localhost"
paths:
  raw_dir: "data/raw"
  archive_dir: "data/archive"
""",
        encoding="utf-8",
    )

    dev_file = tmp_path / "development.yaml"
    dev_file.write_text(
        """
extends: "base.yaml"
pipeline:
  environment: "development"
""",
        encoding="utf-8",
    )

    settings = load_config(dev_file)
    assert settings.pipeline.environment == "development"
    assert settings.pipeline.batch_size == 10000


def test_env_var_interpolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test dynamic environment variable resolution (env_var:NAME)."""
    monkeypatch.setenv("TEST_POSTGRES_PASS", "secret_pass_123")

    config_file = tmp_path / "base.yaml"
    config_file.write_text(
        """
database:
  password: "env_var:TEST_POSTGRES_PASS"
paths:
  raw_dir: "data/raw"
  archive_dir: "data/archive"
""",
        encoding="utf-8",
    )

    settings = load_config(config_file)
    assert settings.database.password == "secret_pass_123"


def test_semantic_validation_same_raw_and_archive_dir(tmp_path: Path) -> None:
    """Test semantic check fails when archive_dir is identical to raw_dir."""
    config_file = tmp_path / "base.yaml"
    config_file.write_text(
        """
paths:
  raw_dir: "data/raw"
  archive_dir: "data/raw"
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError) as exc_info:
        load_config(config_file)
    assert "archive_dir cannot be identical to paths.raw_dir" in str(exc_info.value)


def test_invalid_config_fail_fast(tmp_path: Path) -> None:
    """Test fail-fast startup behavior for invalid configuration values."""
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text(
        """
pipeline:
  batch_size: -100
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_config(config_file)
