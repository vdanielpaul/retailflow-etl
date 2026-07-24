"""Layered YAML configuration loader with environment variable interpolation and semantic validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from retailflow.config.settings import Settings
from retailflow.exceptions.exceptions import ConfigurationError


def _resolve_env_variables(data: Any) -> Any:
    """Recursively resolve 'env_var:VAR_NAME' strings to environment variable values."""
    if isinstance(data, dict):
        return {k: _resolve_env_variables(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_resolve_env_variables(item) for item in data]
    elif isinstance(data, str) and data.startswith("env_var:"):
        var_name = data.split("env_var:", 1)[1]
        env_val = os.getenv(var_name)
        if env_val is None:
            return ""
        return env_val
    return data


def _deep_merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries, giving priority to override keys."""
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def validate_semantic_config(settings: Settings) -> None:
    """Perform semantic validation rules beyond Pydantic schema validation.

    Raises:
        ConfigurationError: If semantic rules are violated.
    """
    # 1. Batch size check
    if settings.pipeline.batch_size <= 0:
        raise ConfigurationError("pipeline.batch_size must be greater than 0.")

    # 2. Database connection pool bounds check
    if settings.database.min_connections > settings.database.max_connections:
        raise ConfigurationError(
            f"database.min_connections ({settings.database.min_connections}) cannot exceed "
            f"database.max_connections ({settings.database.max_connections})."
        )

    # 3. Archive directory must be different from raw input directory
    raw_path = Path(settings.paths.raw_dir).resolve()
    archive_path = Path(settings.paths.archive_dir).resolve()
    if raw_path == archive_path:
        raise ConfigurationError("paths.archive_dir cannot be identical to paths.raw_dir.")

    # 4. Check log directory can be created
    log_path = Path(settings.paths.log_dir)
    try:
        log_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ConfigurationError(f"Failed to verify/create log directory at {log_path}: {e}") from e


def load_raw_yaml(config_path: Path) -> dict[str, Any]:
    """Load raw YAML file into a dictionary."""
    if not config_path.exists():
        raise ConfigurationError(f"Configuration file not found at: {config_path}")
    try:
        with open(config_path, encoding="utf-8") as f:
            content = yaml.safe_load(f)
            return content if isinstance(content, dict) else {}
    except Exception as e:
        raise ConfigurationError(f"Failed to parse YAML configuration at {config_path}: {e}") from e


def load_config(config_path: str | Path = "config/development.yaml") -> Settings:
    """Load layered configuration with base inheritance, environment variable resolution, and semantic validation.

    Args:
        config_path: Path to target configuration YAML file.

    Returns:
        Validated Pydantic Settings instance.

    Raises:
        ConfigurationError: If configuration file is missing or invalid.
    """
    path = Path(config_path)

    raw_config = load_raw_yaml(path)

    parent_config: dict[str, Any] = {}
    if "extends" in raw_config:
        base_filename = raw_config.pop("extends")
        base_path = path.parent / base_filename
        if base_path.exists():
            parent_config = load_raw_yaml(base_path)
    else:
        default_base = path.parent / "base.yaml"
        if default_base.exists() and path != default_base:
            parent_config = load_raw_yaml(default_base)

    merged_dict = _deep_merge_dicts(parent_config, raw_config)
    resolved_dict = _resolve_env_variables(merged_dict)

    try:
        settings = Settings(**resolved_dict)
        validate_semantic_config(settings)
        return settings
    except ConfigurationError:
        raise
    except Exception as e:
        raise ConfigurationError(f"Configuration validation failed: {e}") from e
