# Operational Engineering Runbook & Troubleshooting Guide

## Overview
This runbook provides DevOps and Data Engineers with operational guidance to run, monitor, troubleshoot, and recover the RetailFlow ETL pipeline in production.

---

## 1. CLI Command Usage Quick Reference

### Running Pipeline in Production Mode
```bash
./venv/bin/python -m retailflow.cli --config config/production.yaml --env production
```

### Dry-Run Mode (Validation & Transformation without DB Commits)
```bash
./venv/bin/python -m retailflow.cli --dry-run --file data/raw/sales_20260724.csv
```

### Validation-Only Execution
```bash
./venv/bin/python -m retailflow.cli --validation-only --file data/raw/sales_20260724.csv
```

### Manual Replay of Historical Feed File
```bash
./venv/bin/python -m retailflow.cli --replay --file data/raw/sales_20260724.csv
```

---

## 2. Standard Exit Codes Matrix

| Exit Code | Classification | Cause & Recovery Action |
|---|---|---|
| **`0`** | `EXIT_SUCCESS` | Pipeline completed successfully or safely skipped duplicate file. |
| **`1`** | `EXIT_VALIDATION_FAILURE` | Feed CSV headers missing or row error percentage threshold exceeded. Inspect `data/bad_records/<run_id>/invalid_rows.csv`. |
| **`2`** | `EXIT_CONFIG_FAILURE` | Missing YAML config file or directory permission check failed. Verify `config/production.yaml`. |
| **`3`** | `EXIT_DATABASE_FAILURE` | PostgreSQL connection pool timeout or constraint error. Verify host connectivity & database credentials. |
| **`4`** | `EXIT_INCREMENTAL_FAILURE` | Watermark or file hash verification failure. |
| **`5`** | `EXIT_AUDIT_FAILURE` | Audit log table write failure. Check `metadata.etl_audit_log` storage permissions. |
| **`6`** | `EXIT_UNKNOWN_FAILURE` | Unexpected fatal exception. Inspect full stack trace in `logs/retailflow_etl.log`. |

---

## 3. Interpreting Diagnostic Artifacts

- **Processing Manifest**: Check `data/processed/<run_id>/manifest.json` for file hash, classification (`NEW`, `DUPLICATE`, `REPROCESS`), and row counts.
- **Quarantine Folder**: Check `data/bad_records/<run_id>/invalid_rows.csv` and `validation_report.json` to identify rejected rows.
- **Audit Table Logs**: Query PostgreSQL table `metadata.etl_audit_log` to view historical performance metrics.
