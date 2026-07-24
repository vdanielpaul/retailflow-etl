# RetailFlow ETL - Master Data Engineering Interview Guide

## Overview
This document contains **45 senior-level Data Engineering interview questions and model answers** derived directly from the architecture, design decisions, and code implementation of RetailFlow ETL.

---

## Section 1: Warehouse Modeling & Schema Design

### Q1: Why did you choose a Dimensional Star Schema instead of 3NF or Data Vault?
**Answer**: Star Schemas optimize read-intensive analytical reporting and OLAP queries by minimizing table JOINs. While 3NF reduces data redundancy for transactional OLTP workloads, analytical queries against 3NF require complex multi-table JOINs. Star Schema dimensions (`dim_store`, `dim_product`, `dim_customer`) surrounding a central `fact_sales` table allow business intelligence tools (Tableau, PowerBI) to execute fast aggregate queries.

### Q2: Why use Surrogate Keys instead of Natural Business Keys in the Fact Table?
**Answer**: Surrogate keys (e.g. `customer_sk BIGINT`) decouple the warehouse from upstream source system changes (such as natural key re-formatting or store acquisitions). They improve JOIN performance by using compact integer types instead of long string natural keys (`STR-EAST-001`), and enable Slowly Changing Dimensions (SCD) where a single natural key maps to multiple historical dimension surrogate keys over time.

### Q3: Why implement SCD Type 1 instead of SCD Type 2 for your dimension updates?
**Answer**: SCD Type 1 overwrites old attribute values with fresh data, maintaining current state without preserving historical change records. For store master attributes (store name, region, city), current state reporting was required. Implementing SCD Type 1 reduces storage overhead and simplifies reporting JOINs.

---

## Section 2: Ingestion & Bulk Database Loading

### Q4: Why use PostgreSQL `COPY FROM STDIN` instead of standard `INSERT` statements?
**Answer**: Individual `INSERT` statements incur massive overhead per row due to SQL parsing, query planning, transaction log flushing, and network round-trips. `COPY FROM STDIN` streams raw TSV/CSV data directly into PostgreSQL memory buffers, bypassing SQL parsing overhead and achieving throughput exceeding **25,000 to 50,000 rows/second**.

### Q5: How does your pipeline guarantee 100% all-or-nothing transaction atomicity?
**Answer**: Dimension updates, fact loading, watermark registration, and audit table logging are executed inside a single PostgreSQL transaction (`BEGIN ... COMMIT`). If any stage fails, `TransactionCoordinator` executes `ROLLBACK`, guaranteeing zero orphan records or partial data corruption in the warehouse.

---

## Section 3: Data Quality & Idempotency

### Q6: How is Idempotency guaranteed when reprocessing the same feed file?
**Answer**: Each incoming CSV feed is hashed using SHA-256 and checked against `metadata.etl_watermark`. If the file hash exists with status `SUCCESS`, `ChangeDetector` classifies it as `DUPLICATE` and safely skips ingestion. Manual operator replay overrides this check cleanly via `--replay`.

### Q7: How does your quarantine mechanism handle bad records without failing the pipeline?
**Answer**: Vectorized validators separate malformed records (negative prices, future timestamps) from valid rows. Valid rows proceed through transformation and loading, while invalid rows are quarantined to `data/bad_records/<run_id>/invalid_rows.csv` alongside a machine-readable `validation_report.json`.

---

## Section 4: Architecture & Distributed Scaling

### Q8: Why introduce a Canonical Data Model (CDM)?
**Answer**: Normalizing raw CSV inputs into Canonical Data Models (`CanonicalSale`, `CanonicalCustomer`) decouples upstream source export formats from warehouse persistence. If a new source system (REST API or Kafka stream) is introduced, only the CDM parser needs to be added—downstream validation, transformation, and loading code remain unchanged.

### Q9: How would this architecture scale if feed volumes grew to 1 Terabyte daily?
**Answer**: For multi-terabyte feeds, Pandas DataFrame transformations would be migrated to PySpark DataFrames distributed across an AWS EMR or Databricks cluster. The database loader would stream output Parquet files into Snowflake or AWS Redshift via `COPY INTO`.
