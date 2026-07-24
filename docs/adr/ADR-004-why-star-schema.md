# ADR-004: Star Schema Data Warehouse Modeling

## Status
Accepted

## Context
Retail sales data requires analytical processing across multiple business axes: sales by store location, sales by product category, customer purchasing behavior, and employee POS performance. We needed a database modeling structure optimized for OLAP analytics.

## Decision
We implemented a **Kimball Star Schema** consisting of a centralized line-item fact table (`fact_sales`) joined directly to denormalized dimension tables (`dim_customer`, `dim_product`, `dim_store`, `dim_employee`).

## Alternatives Considered
1. **Third Normal Form (3NF) Relational Model**:
   - *Pros*: Eliminates data redundancy, optimized for high-frequency transactional writes (OLTP).
   - *Cons*: Requires 6 to 10 JOIN operations for simple analytical business reports, resulting in slow query performance.
2. **Single Flat Wide Table (One Big Table / OBT)**:
   - *Pros*: Zero JOINs required.
   - *Cons*: Severe data duplication, inefficient storage, high update anomaly risk when store or product attributes change.

## Consequences
- **Positive**: High query performance for business reporting, intuitive structure for SQL analytics, decoupled dimension updates via surrogate keys.
- **Negative**: Requires ETL pipeline logic to perform surrogate key resolution during ingestion.
