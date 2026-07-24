# Data Warehouse Architectural Design & Star Schema Specification

## 1. Executive Summary
This document defines the architectural specifications for the **RetailFlow Data Warehouse**. It details the business grain, fact table design, surrogate vs. natural key strategies, SCD type choices, partitioning, indexing, constraint rules, schema separation, and data retention policies governing the PostgreSQL database implementation.

---

## 2. Dimensional Model Overview

```mermaid
erDiagram
    fact_sales }|..|| dim_date : "date_sk"
    fact_sales }|..|| dim_customer : "customer_sk"
    fact_sales }|..|| dim_product : "product_sk"
    fact_sales }|..|| dim_store : "store_sk"
    fact_sales }|..|| dim_employee : "employee_sk"
    fact_sales }|..|| etl_audit_log : "audit_run_id"

    dim_date {
        INT date_sk PK
        DATE calendar_date
        INT year
        INT quarter
        INT month
        VARCHAR month_name
        INT week
        INT day
        VARCHAR day_name
        BOOLEAN is_weekend
        INT fiscal_year
    }

    dim_customer {
        BIGINT customer_sk PK
        VARCHAR customer_id NK
        VARCHAR first_name
        VARCHAR last_name
        VARCHAR email
        VARCHAR phone
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    dim_product {
        BIGINT product_sk PK
        VARCHAR product_id NK
        VARCHAR product_name
        VARCHAR category
        VARCHAR brand
        NUMERIC unit_price
        TIMESTAMP updated_at
    }

    dim_store {
        BIGINT store_sk PK
        VARCHAR store_id NK
        VARCHAR store_name
        VARCHAR region
        VARCHAR city
        VARCHAR state
        TIMESTAMP updated_at
    }

    dim_employee {
        BIGINT employee_sk PK
        VARCHAR employee_id NK
        VARCHAR first_name
        VARCHAR last_name
        VARCHAR role
        VARCHAR store_id
        TIMESTAMP updated_at
    }

    fact_sales {
        BIGINT sales_sk PK
        VARCHAR transaction_id
        INT date_sk FK
        BIGINT customer_sk FK
        BIGINT product_sk FK
        BIGINT store_sk FK
        BIGINT employee_sk FK
        TIMESTAMP transaction_time
        INT quantity
        NUMERIC unit_price
        NUMERIC discount_amount
        NUMERIC net_sales_amount
        BIGINT audit_run_id FK
    }

    etl_audit_log {
        BIGINT run_id PK
        UUID pipeline_run_id
        VARCHAR batch_id
        VARCHAR source_filename
        VARCHAR source_file_hash
        VARCHAR execution_stage
        BIGINT records_read
        BIGINT records_valid
        BIGINT records_rejected
        BIGINT records_loaded
        VARCHAR execution_status
        TIMESTAMP started_at
        TIMESTAMP completed_at
        BIGINT duration_ms
        VARCHAR executed_by
        VARCHAR application_version
    }
```

---

## 3. Schema Architecture Isolation
To maintain clean operational boundaries, the database is partitioned into two isolated schemas:
- **`warehouse` Schema**: Contains analytical dimensional tables (`dim_*`) and fact tables (`fact_sales`). Accessed by business intelligence tools and analysts.
- **`metadata` Schema**: Contains operational control tables (`etl_audit_log`, `etl_watermark`). Accessed strictly by the ETL orchestration engine.

---

## 4. Key Design Decisions & Architectural Deep Dives

### 4.1 Business & Fact Grain Definition
- **Business Process**: Point-of-Sale (POS) customer checkout transactions across 250+ store locations.
- **Fact Table Grain**: One row in `warehouse.fact_sales` represents **a single line item on a POS checkout transaction**.

### 4.2 Time Dimension (`dim_time`) Decision
- **Omission Rationale**: A separate `dim_time` (86,400 rows representing every second/minute of a day) was omitted. Transaction timestamps (`transaction_time`) are stored directly on `fact_sales` alongside `date_sk` linking to `dim_date`.
- **When `dim_time` is Useful**: High-frequency intra-day hourly/minute pattern reporting across millions of daily events.
- **Evolution Path**: If business requirements demand detailed intra-day hourly peak shift reporting, a `dim_time` table with 1,440 minute rows can be added without altering existing `fact_sales` grain.

### 4.3 Business Key Resolution & SCD Type 1 Upserts
- **Natural Keys**: `customer_id` (Customer), `product_id` (Product), `store_id` (Store), `employee_id` (Employee).
- **Duplicate Key Handling**: Incoming batch feeds perform atomic upserts using PostgreSQL `INSERT ... ON CONFLICT (natural_key) DO UPDATE SET attribute = EXCLUDED.attribute, updated_at = CURRENT_TIMESTAMP`. Duplicate business keys within the same feed are deduplicated during the transformation phase prior to database loading.

### 4.4 Slowly Changing Dimensions (SCD) Trade-off Analysis

| SCD Strategy | Storage Impact | Query Complexity | Historical Accuracy | Best Used For |
|---|---|---|---|---|
| **SCD Type 1 (Implemented)** | Minimal (Overwrites existing record) | Extremely Simple (Single JOIN) | Current state only | Frequently changing attributes where past state is irrelevant (e.g. phone number, customer email) |
| **SCD Type 2** | High (Adds new row version per update) | Moderate (Requires `is_current = True` or date filter) | 100% Point-in-Time historical accuracy | Critical business changes where historical reporting must reflect past attribute state (e.g., product price changes, store region reassignments) |
| **SCD Type 3** | Medium (Adds `previous_attribute` column) | Simple | Previous & current state only | Tracking single historical change (e.g., previous manager name) |

### 4.5 Dual Watermark & SHA-256 Idempotency Strategy
The watermark system in `metadata.etl_watermark` records both **Max Event Timestamp** and **SHA-256 File Hash**:
- **Timestamp Watermarking**: Ensures incremental batches only pull events newer than the last processed timestamp per store.
- **SHA-256 Hash Tracking**: Prevents accidental re-ingestion of identical store CSV files delivered under different filenames, guaranteeing 100% idempotent pipeline runs.

---

## 5. Expanded Indexing Strategy & Performance Trade-offs

| Index Name | Target Table & Columns | Supported Query Pattern | Selectivity | Maintenance Cost | Rationale / Trade-offs |
|---|---|---|---|---|---|
| `idx_fact_sales_store_time` | `fact_sales (store_sk, transaction_time)` | Regional & store-level daily sales reports | High | Medium | Optimizes primary OLAP report path. Small write overhead on batch inserts. |
| `idx_fact_sales_date` | `fact_sales (date_sk)` | Monthly/Quarterly date filtering | High | Low | Accelerates `dim_date` JOIN aggregations. |
| `idx_fact_sales_product_time` | `fact_sales (product_sk, transaction_time)` | Product merchandise category velocity | High | Medium | Speeds up product velocity queries. |
| `idx_fact_sales_customer` | `fact_sales (customer_sk)` | Customer repeat order lookups | Medium | Low | Speeds up CRM customer queries. |
| `idx_etl_audit_file_hash` | `etl_audit_log (source_file_hash)` | Duplicate file check pre-ingestion | Very High | Negligible | Instantly resolves idempotency check. |

### Why Indexes Are Intentionally Omitted on Other Columns
Creating indexes on every column degrades bulk INSERT performance and bloats database storage. Columns with low selectivity (e.g., `is_weekend`, `quantity`, `discount_amount`) are intentionally left unindexed because full table/partition scans or sequential scans are cheaper for PostgreSQL query planners when aggregating over low-cardinality attributes.
