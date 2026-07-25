# Structured logging module optimized for Google Cloud Logging

import json
import logging
import sys
from typing import Any

class CloudJsonFormatter(logging.Formatter):
    """Formats Python log logs into GCP-compatible structured JSON format."""
    
    def format(self, record: logging.LogRecord) -> str:
        # GCP Cloud Logging expects severity key instead of levelname
        payload: dict[str, Any] = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, self.datefmt),
            "logging.googleapis.com/sourceLocation": {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName
            }
        }
        
        # Include extra payload dictionaries if attached to the record
        if hasattr(record, "extra_fields"):
            payload.update(record.extra_fields) # type: ignore
            
        return json.dumps(payload)

def get_cloud_logger(name: str = "retailflow-cloud-function") -> logging.Logger:
    """Configures and returns a structured JSON logger for standard out."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = CloudJsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger
