# Centralized Logging Architecture

## Overview
RetailFlow ETL implements Python's native `logging` library configured with custom formatters to deliver structured, predictable, and audit-ready logging across all pipeline modules.

---

## Log Output Formats

### 1. Console Output Format
Human-readable colored log format for interactive debugging:
```
2026-07-24 12:00:00 [INFO] retailflow.validation: File validation passed for store_001_sales.csv (Rows: 15420, Rejected: 12)
```

### 2. File Output Format (Rotating Handler)
Structured JSON line format for log aggregation systems:
```json
{
  "timestamp": "2026-07-24T12:00:00.123456Z",
  "level": "INFO",
  "module": "retailflow.validation",
  "func_name": "validate_sales_feed",
  "message": "File validation completed",
  "file_name": "store_001_sales.csv",
  "total_rows": 15420,
  "rejected_rows": 12
}
```

---

## Log Level Usage Standard

- `DEBUG`: Fine-grained information for diagnosing pipeline logic (e.g., individual SQL statement generation, DataFrame slice memory usage).
- `INFO`: Normal operational events (e.g., file ingestion start, batch database insert completed, audit record written).
- `WARNING`: Recoverable data issues or non-fatal anomalies (e.g., duplicate row ignored, non-critical field defaulted, threshold warning).
- `ERROR`: Recoverable pipeline failures (e.g., corrupted file header, row validation failure threshold breached).
- `CRITICAL`: Unrecoverable system failure preventing execution continuation (e.g., database connection dropped, missing mandatory directory).
