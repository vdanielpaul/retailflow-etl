# ADR-002: Selection of PostgreSQL as the Target Data Warehouse Engine

## Status
Accepted

## Context
RetailFlow ETL requires a robust target database management system to host dimension tables (`dim_customer`, `dim_product`, `dim_store`, `dim_employee`), transactional sales fact tables (`fact_sales`), and operational audit logs (`etl_audit_log`).

## Decision
We selected **PostgreSQL 14+** as the central relational data warehouse engine.

## Alternatives Considered
1. **SQLite**: Lightweight embedded SQL database.
   - *Pros*: Zero setup, serverless.
   - *Cons*: Weak concurrency control, lacks rich window functions and partitioning capabilities, unsuitable for multi-table enterprise DW modeling.
2. **Cloud Data Warehouses (Snowflake / AWS Redshift / GCP BigQuery)**:
   - *Pros*: Massive MPP analytical performance.
   - *Cons*: Requires active cloud subscriptions, external network egress, complex local deployment mocking for automated test pipelines.

## Consequences
- **Positive**: Strict ACID compliance, native support for JSONB, identity columns, composite indexing, cost-effective deployment on-premise or containerized, high SQL standard compliance.
- **Negative**: Requires connection pool management and vacuum/index maintenance for high-volume write operations.
