"""Structured logging framework with sensitive data redaction for RetailFlow ETL."""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any

# Global context dictionary for correlation IDs and run metadata
_LOG_CONTEXT: dict[str, Any] = {
    "pipeline_run_id": "N/A",
    "batch_id": "N/A",
    "source_filename": "N/A",
    "execution_stage": "INITIALIZATION",
    "environment": "development",
    "application_version": "0.1.0",
}

# Regex patterns for masking sensitive secrets before writing to logs
_SENSITIVE_PATTERNS = [
    (re.compile(r"(password['\"]?\s*[:=]\s*['\"]?)([^'\"\s&]+)", re.IGNORECASE), r"\1********"),
    (re.compile(r"(postgres(?:ql)?://[^:]+:)([^@]+)(@)", re.IGNORECASE), r"\1********\3"),
    (re.compile(r"(token['\"]?\s*[:=]\s*['\"]?)([^'\"\s&]+)", re.IGNORECASE), r"\1********"),
    (re.compile(r"(api_key['\"]?\s*[:=]\s*['\"]?)([^'\"\s&]+)", re.IGNORECASE), r"\1********"),
    (re.compile(r"(secret['\"]?\s*[:=]\s*['\"]?)([^'\"\s&]+)", re.IGNORECASE), r"\1********"),
]


def set_log_context(
    run_id: str | None = None,
    batch_id: str | None = None,
    filename: str | None = None,
    stage: str | None = None,
    environment: str | None = None,
    version: str | None = None,
) -> None:
    """Set global log context values for contextual trace auditing."""
    if run_id is not None:
        _LOG_CONTEXT["pipeline_run_id"] = run_id
    if batch_id is not None:
        _LOG_CONTEXT["batch_id"] = batch_id
    if filename is not None:
        _LOG_CONTEXT["source_filename"] = filename
    if stage is not None:
        _LOG_CONTEXT["execution_stage"] = stage
    if environment is not None:
        _LOG_CONTEXT["environment"] = environment
    if version is not None:
        _LOG_CONTEXT["application_version"] = version


def redact_sensitive_data(message: str) -> str:
    """Mask passwords, secret tokens, and connection strings in log messages."""
    redacted = message
    for pattern, replacement in _SENSITIVE_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


class SensitiveDataFilter(logging.Filter):
    """Logging filter that redacts passwords and secrets from log record messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_data(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: redact_sensitive_data(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_sensitive_data(str(arg)) for arg in record.args)
        return True


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for automated log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "pipeline_run_id": getattr(record, "pipeline_run_id", _LOG_CONTEXT.get("pipeline_run_id", "N/A")),
            "batch_id": getattr(record, "batch_id", _LOG_CONTEXT.get("batch_id", "N/A")),
            "source_filename": getattr(record, "source_filename", _LOG_CONTEXT.get("source_filename", "N/A")),
            "execution_stage": getattr(record, "execution_stage", _LOG_CONTEXT.get("execution_stage", "INITIALIZATION")),
            "environment": getattr(record, "environment", _LOG_CONTEXT.get("environment", "development")),
            "application_version": getattr(record, "application_version", _LOG_CONTEXT.get("application_version", "0.1.0")),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


class ColoredConsoleFormatter(logging.Formatter):
    """Human-readable console log formatter with ANSI color codes."""

    GREY = "\x1b[38;20m"
    BLUE = "\x1b[34;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: GREY + "%(asctime)s [%(levelname)s] [%(name)s] [%(execution_stage)s]: %(message)s" + RESET,
        logging.INFO: BLUE + "%(asctime)s [%(levelname)s] [%(name)s] [%(execution_stage)s]: %(message)s" + RESET,
        logging.WARNING: YELLOW + "%(asctime)s [%(levelname)s] [%(name)s] [%(execution_stage)s]: %(message)s" + RESET,
        logging.ERROR: RED + "%(asctime)s [%(levelname)s] [%(name)s] [%(execution_stage)s]: %(message)s" + RESET,
        logging.CRITICAL: BOLD_RED + "%(asctime)s [%(levelname)s] [%(name)s] [%(execution_stage)s]: %(message)s" + RESET,
    }

    def format(self, record: logging.LogRecord) -> str:
        record.execution_stage = getattr(record, "execution_stage", _LOG_CONTEXT.get("execution_stage", "N/A"))
        log_fmt = self.FORMATS.get(record.levelno, "%(asctime)s [%(levelname)s]: %(message)s")
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logger(
    name: str = "retailflow",
    log_level: str = "INFO",
    log_dir: Path | str = Path("logs"),
    log_filename: str = "retailflow_etl.log",
    console_output: bool = True,
    file_output: bool = True,
    max_bytes: int = 10485760,
    backup_count: int = 5,
) -> logging.Logger:
    """Configure and return structured logger instance with sensitive data redaction."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()
    logger.propagate = False

    sensitive_filter = SensitiveDataFilter()

    # Console Handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredConsoleFormatter())
        console_handler.addFilter(sensitive_filter)
        logger.addHandler(console_handler)

    # File Handler (JSON Format)
    if file_output:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_target = log_path / log_filename

        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            file_target,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(JSONFormatter())
        file_handler.addFilter(sensitive_filter)
        logger.addHandler(file_handler)

    return logger


class ExecutionTimer:
    """Context manager for tracking elapsed execution latency."""

    def __init__(self, stage_name: str, logger: logging.Logger | None = None) -> None:
        self.stage_name = stage_name
        self.logger = logger or logging.getLogger("retailflow")
        self.start_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> ExecutionTimer:
        self.start_time = time.perf_counter()
        set_log_context(stage=self.stage_name)
        self.logger.info(f"Starting stage: {self.stage_name}")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000.0
        if exc_type is not None:
            self.logger.error(
                f"Stage {self.stage_name} failed after {self.elapsed_ms:.2f}ms with error: {exc_val}"
            )
        else:
            self.logger.info(f"Completed stage: {self.stage_name} in {self.elapsed_ms:.2f}ms")
