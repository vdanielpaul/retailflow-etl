# SQL Scripts & DDL Guide

## Script Catalog

All SQL scripts reside in the `sql/` directory and must be executed in numeric sequence.

```
sql/
├── ddl/
│   ├── 01_create_schema.sql      # Schema initialization & UUID extension
│   ├── 02_create_dimensions.sql  # dim_customer, dim_product, dim_store, dim_employee
│   ├── 03_create_fact_sales.sql  # Partitioned fact_sales table
│   ├── 04_create_audit_tables.sql# etl_audit_log & etl_watermark
│   └── 05_create_indexes.sql     # Composite B-tree indexes
└── dml/
    ├── 01_seed_dimensions.sql    # Core store, product, employee, & customer master seed data
    └── 02_sample_queries.sql     # Business analytical validation queries
```

---

## Execution Sequence

```bash
# 1. Execute DDL Scripts
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f sql/ddl/01_create_schema.sql
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f sql/ddl/02_create_dimensions.sql
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f sql/ddl/03_create_fact_sales.sql
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f sql/ddl/04_create_audit_tables.sql
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f sql/ddl/05_create_indexes.sql

# 2. Execute Seed DML Script
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f sql/dml/01_seed_dimensions.sql
```

---

## Key SQL Architectural Specifications
- **Identity Surrogate Keys**: `BIGINT GENERATED ALWAYS AS IDENTITY` for high performance and sequence integrity.
- **Natural Key Upsert Constraints**: `UNIQUE` constraints on natural keys (`store_id`, `product_id`, `customer_id`, `employee_id`) enabling idempotent SCD Type 1 upserts.
- **Range Partitioning**: `fact_sales` is partitioned by month on `transaction_time` to maximize OLAP query pruning efficiency.
- **Referential Integrity**: Strict `FOREIGN KEY ... ON DELETE RESTRICT` linking `fact_sales` to surrogate keys.
- **Composite B-Tree Indexes**: Indexed access paths on `(store_sk, transaction_time)` and `(product_sk, transaction_time)`.
