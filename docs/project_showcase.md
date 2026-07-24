# RetailFlow ETL - Project Showcase & Interview Guide

## Overview & Business Context
RetailFlow ETL simulates a production point-of-sale (POS) data warehouse pipeline built for a retail enterprise operating over 250 store locations. Every night, stores export batch CSV feeds containing sales line items. RetailFlow validates incoming feeds, cleans malformed data, computes financial metrics, updates dimension records via SCD Type 1, and bulk loads a PostgreSQL dimensional star schema.

---

## Technical Highlights & Key Innovations

### 1. Modern Medallion + Dimensional Star Schema Mapping
- **Bronze (Raw Ingestion)**: Ingestion of store feed CSV exports.
- **Silver (Cleaned & Validated)**: Modular validation engine separating malformed rows into `data/bad_records/<run_id>/`.
- **Gold (Enterprise Warehouse)**: Dimensional Star Schema containing `dim_date`, `dim_customer`, `dim_product`, `dim_store`, `dim_employee`, and range-partitioned `fact_sales`.

### 2. High-Performance Bulk Loading
- Implements PostgreSQL `COPY FROM STDIN` streaming and `psycopg2.extras.execute_values` chunked batch loading, achieving **>25,000 rows/second** throughput.

### 3. Operational Observability & Audit Logging
- Structured JSON logging with sensitive data redaction (passwords, connection tokens).
- 12 standardized `PipelineLifecycleEvent` audit records stored in `metadata.etl_audit_log`.

---

## Technical Talking Points for Data Engineering Interviews

1. **Why Pandas over Spark?**: For batch feeds under 10 GB per file, Pandas in-memory vectorized processing provides sub-second latency without cluster overhead. The codebase is decoupled via a Canonical Data Model so Spark can be swapped in seamlessly.
2. **How is Idempotency Guaranteed?**: Each feed file is hashed using SHA-256 and checked against `metadata.etl_watermark`. Re-running the pipeline on identical files cleanly skips re-ingestion.
3. **How are Data Quality Failures Handled?**: Bad records are quarantined to `data/bad_records/<run_id>/invalid_rows.csv` with a machine-readable `validation_report.json`, allowing clean rows to proceed while preserving raw bad data for audit investigation.
