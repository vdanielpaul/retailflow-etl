# Chapter 18: Comprehensive Data Engineering Glossary

## Glossary of Key Concepts & Terminology

- **ACID**: Atomicity, Consistency, Isolation, Durability. Properties guaranteeing reliable database transactions.
- **Audit Table**: A metadata logging table (`metadata.etl_audit_log`) tracking pipeline execution metrics, row counts, and status.
- **Batch Processing**: Execution pattern where data is collected over an interval and processed together in bulk feeds.
- **Bulk Loading**: High-speed database ingestion methods (`COPY FROM STDIN`) bypassing row-by-row SQL insertion.
- **Canonical Data Model (CDM)**: An enterprise integration pattern normalizing raw inputs into source-agnostic entities.
- **CDC (Change Data Capture)**: Software capturing row-level database changes (inserts, updates, deletes) in real time.
- **Checkpoint**: Saved execution state file (`checkpoint.json`) enabling partial failure recovery.
- **Dimension Table**: Warehouse table storing descriptive context attributes (`dim_store`, `dim_product`, `dim_customer`).
- **ETL**: Extract, Transform, Load. Standard data pipeline processing paradigm.
- **Fact Table**: Central warehouse table storing quantitative numeric measurements (`fact_sales`).
- **Idempotency**: Property where re-executing a pipeline on identical input data produces the exact same outcome without duplicating records.
- **In-Memory Caching**: Pre-loading reference data into Python dictionary hash maps for $O(1)$ fast lookups.
- **Natural Key / Business Key**: Identifier assigned to an entity by an operational source system (`STR-001`).
- **OLAP**: Online Analytical Processing. Database engines optimized for complex aggregate reporting queries.
- **OLTP**: Online Transaction Processing. Database engines optimized for high-concurrency cash register writes.
- **Partitioning**: Dividing a large physical table into smaller, faster file chunks on disk based on a key (e.g., transaction month).
- **Quarantine**: Isolating invalid records to a separate directory (`data/bad_records/<run_id>/`) without stopping clean record processing.
- **Reconciliation**: Automated verification checking that Source Rows = Clean Rows + Quarantined Rows = Loaded Warehouse Rows.
- **Replay**: Manually forcing the re-execution of a historical feed file, overriding watermark duplicate checks.
- **SAVEPOINT**: A SQL boundary marker allowing partial transaction rollback without aborting the entire transaction.
- **SCD (Slowly Changing Dimension)**: Technique for managing attribute changes in dimension tables over time (SCD Type 1 overwrites in-place).
- **Star Schema**: Dimensional warehouse design organizing context dimensions around a central fact table.
- **Surrogate Key**: An auto-incrementing integer created by the warehouse to uniquely identify dimension records (`store_sk BIGINT`).
- **Vectorization**: Execution technique applying operations across entire array memory columns simultaneously in C.
- **Watermark**: High-watermark tracking mechanism (`metadata.etl_watermark`) recording processed file hashes and timestamps.
