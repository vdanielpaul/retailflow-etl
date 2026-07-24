# Data Engineering Interview Q&A Guide

## Core Architectural Questions

### Q1: Why did you choose a Star Schema design instead of a 3NF Normalized Schema?
**Answer**:
"In OLAP data warehousing, query workloads are dominated by analytical aggregations (e.g., total sales by region, category revenue over time). A Star Schema denormalizes descriptive attributes into dimensions (`dim_store`, `dim_product`), reducing complex multi-table JOINs required by 3NF models. This significantly improves query performance, reduces query writing complexity for BI tools, and speeds up analytical aggregation."

---

### Q2: How does your pipeline handle bad records without failing the entire batch run?
**Answer**:
"We implement a Fault Isolation pattern using a multi-stage validation engine. Before any record reaches the transformation layer, it passes through schema enforcement, type coercion, and business rule validators. If a row violates a non-nullable constraint or contains negative quantities, it is routed to `data/bad_records/` with JSON failure metadata detailing line numbers and exact error codes. Valid rows continue through ingestion, preserving batch throughput."

---

### Q3: How do you handle Slowly Changing Dimensions (SCD) in your design?
**Answer**:
"We use SCD Type 1 for dimensions like customer profiles and product catalog updates, overwriting existing attribute values with the latest incoming record based on natural key matches and updating `updated_at` timestamps. In our SQL layer, this is implemented using transactional `INSERT ... ON CONFLICT (natural_key) DO UPDATE` SQL statements."

---

### Q4: How would this architecture change if data volume grew 100x (e.g. 25,000 stores)?
**Answer**:
"At 100x volume, single-node Pandas processing and monolithic PostgreSQL ingestion become bottlenecks. I would transition:
1. **Compute**: From Pandas to PySpark / Delta Lake for distributed transformations.
2. **Ingestion**: From local filesystem drops to S3 bucket events triggering AWS Lambda / EventBridge.
3. **Storage**: From PostgreSQL to Snowflake or Redshift using `COPY INTO` bulk loading.
4. **Orchestration**: From cron scripts to Airflow DAGs with parallel task execution."
