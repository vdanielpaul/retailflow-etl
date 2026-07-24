# Database Naming Conventions & Standards

## Overview
This document specifies the database naming standards enforced across all PostgreSQL DDL scripts, schemas, tables, columns, indexes, and metadata objects in the **RetailFlow Data Warehouse**.

---

## 1. Schema Conventions
- Use lowercase singular noun names reflecting function or domain boundary.
- **Analytical Tables Schema**: `warehouse`
- **Audit & Metadata Schema**: `metadata`

---

## 2. Table Conventions
- Use lowercase `snake_case` with explicit architectural prefix.
- **Dimension Tables**: `dim_<entity>` (e.g. `warehouse.dim_customer`, `warehouse.dim_product`, `warehouse.dim_date`).
- **Fact Tables**: `fact_<domain>` (e.g. `warehouse.fact_sales`).
- **Partitions**: `<parent_table>_y<YYYY>m<MM>` (e.g. `warehouse.fact_sales_y2026m07`).
- **Metadata Tables**: `etl_<purpose>` (e.g. `metadata.etl_audit_log`, `metadata.etl_watermark`).

---

## 3. Column Conventions
- All column names must use lowercase `snake_case`.

### 3.1 Surrogate Keys (`_sk`)
- Every dimension table uses an auto-incrementing identity surrogate key: `<entity>_sk`.
- Example: `customer_sk`, `product_sk`, `store_sk`, `employee_sk`, `date_sk`.

### 3.2 Natural Keys (`_id`)
- Source system identifiers preserve source natural names ending in `_id`.
- Example: `customer_id`, `product_id`, `store_id`, `employee_id`, `transaction_id`.

### 3.3 Timestamps (`_at` / `_time`)
- System auditing timestamps end with `_at`: `created_at`, `updated_at`, `started_at`, `completed_at`.
- Transaction event timestamps end with `_time`: `transaction_time`.

---

## 4. Constraint Naming Conventions
- **Primary Keys**: `pk_<table_name>` (e.g. `pk_dim_customer`).
- **Foreign Keys**: `fk_<source_table>_<target_table>` (e.g. `fk_fact_sales_dim_product`).
- **Unique Constraints**: `uq_<table_name>_<column_name>` (e.g. `uq_dim_customer_customer_id`).
- **Check Constraints**: `chk_<table_name>_<column_name>` (e.g. `chk_dim_product_unit_price`).

---

## 5. Index Naming Conventions
- All custom indexes start with `idx_<table_name>_<column(s)>`.
- Single column index: `idx_fact_sales_customer`
- Composite index: `idx_fact_sales_store_time`
- Unique index: `idx_uq_etl_audit_file_hash`
