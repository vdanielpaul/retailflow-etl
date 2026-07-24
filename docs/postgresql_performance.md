# PostgreSQL Bulk Ingestion & Warehouse Performance Guide

## Overview
High-throughput data warehousing requires optimizing PostgreSQL write paths, indexing strategies, transaction overhead, and storage engine maintenance.

---

## 1. Ingestion Strategy Benchmarks & Trade-Offs

| Ingestion Strategy | Mechanism | Throughput (rows/sec) | Best Use Case |
|---|---|---|---|
| **`COPY FROM STDIN`** | Direct binary/tsv stream into PostgreSQL buffer | **50,000 – 100,000+** | Initial warehouse backfills & large daily batch files |
| **`execute_values()`** | Prepared SQL batch insert (`VALUES (%s), (%s)...`) | **10,000 – 25,000** | Chunked fact batch loading & SCD Type 1 upserts |
| **`executemany()`** | Individual SQL statements sent sequentially | **500 – 2,000** | Fallback small dimension seed loading only |

---

## 2. PostgreSQL Tuning Best Practices

### B-Tree Indexing Strategy
- **Bulk Loading Overhead**: Indexes must be updated for every inserted row.
- **Optimization**: For large historical backfills, drop non-primary indexes before loading, perform bulk `COPY`, then recreate indexes concurrently (`CREATE INDEX CONCURRENTLY`).

### Range Partitioning & Pruning
- `warehouse.fact_sales` is range-partitioned monthly by `transaction_time`.
- Enables partition pruning during analytical queries (`WHERE transaction_time >= '2026-07-01'`) and allows dropping old partition tables instantly (`DROP TABLE`) instead of slow `DELETE` queries.

### Maintenance & Vacuuming
- Run `ANALYZE warehouse.fact_sales;` post-loading to update query planner statistics.
- Configure `autovacuum` parameters for high-write staging tables.
