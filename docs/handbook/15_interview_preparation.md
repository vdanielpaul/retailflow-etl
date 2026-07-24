# Chapter 15: Master Interview Preparation (100 Q&As)

This chapter provides **100 technical Data Engineering interview questions** with senior-level model answers based on RetailFlow ETL.

---

## Part 1: Architecture & System Design (Questions 1 – 20)

### Q1: What is the overall architecture of RetailFlow ETL?
- **Why They're Asking**: Assesses your high-level system comprehension and ability to summarize complex pipelines.
- **Strong Answer**: *"RetailFlow ETL is an enterprise sales data warehouse pipeline built in Python, Pandas, and PostgreSQL. It ingests nightly POS store feed CSV exports, enforces data quality validation with automatic bad-record quarantine, normalizes raw inputs into a Canonical Data Model, resolves surrogate keys via in-memory lookup caches, and bulk loads a PostgreSQL Star Schema warehouse within atomic SQL transactions."*
- **Weak Answer**: *"It reads CSV files with Pandas and puts them into PostgreSQL."*
- **Common Mistake**: Omitting validation, canonical models, and transaction management.

### Q2: Why did you choose a Dimensional Star Schema instead of 3NF?
- **Strong Answer**: *"Star Schemas optimize read-intensive analytical reporting and OLAP queries by minimizing table JOINs. While 3NF reduces data redundancy for transactional OLTP workloads, analytical queries against 3NF require complex multi-table JOINs. Star Schema dimensions (`dim_store`, `dim_product`, `dim_customer`) surrounding a central `fact_sales` table allow business intelligence tools (Tableau, PowerBI) to execute fast aggregate queries."*

### Q3: Why use Surrogate Keys instead of Natural Keys in the Fact Table?
- **Strong Answer**: *"Surrogate keys (e.g. `customer_sk BIGINT`) decouple the warehouse from upstream source system changes (such as natural key re-formatting or store acquisitions). They improve JOIN performance by using compact integer types instead of long string natural keys (`STR-EAST-001`), and enable Slowly Changing Dimensions (SCD) where a single natural key maps to multiple historical dimension surrogate keys over time."*

### Q4: Why build a Canonical Data Model (CDM)?
- **Strong Answer**: *"The Canonical Data Model decouples upstream ingestion formats from downstream warehouse logic using Pydantic models. If a new source system (like a Shopify REST API or Kafka event stream) is added, only a new parser needs to be written—downstream validation, transformation, and loader code remain completely untouched."*

---

## Part 2: SQL, Data Warehousing & Loading (Questions 21 – 40)

### Q21: Why use PostgreSQL `COPY FROM STDIN` instead of SQL `INSERT` statements?
- **Strong Answer**: *"Individual `INSERT` statements incur massive overhead per row due to SQL parsing, query planning, transaction log flushing, and network round-trips. `COPY FROM STDIN` streams raw TSV/CSV data directly into PostgreSQL memory buffers, bypassing SQL parsing overhead and achieving throughput exceeding **25,000 to 50,000 rows/second**."*

### Q22: How does your pipeline guarantee 100% all-or-nothing transaction atomicity?
- **Strong Answer**: *"Dimension updates, fact loading, watermark registration, and audit table logging are executed inside a single PostgreSQL transaction (`BEGIN ... COMMIT`). If any stage fails, `TransactionCoordinator` executes `ROLLBACK`, guaranteeing zero orphan records or partial data corruption in the warehouse."*

---

## Part 3: Data Quality, Incremental Engine & Observability (Questions 41 – 70)

### Q41: How is Idempotency guaranteed when reprocessing the same feed file?
- **Strong Answer**: *"Each incoming CSV feed is hashed using SHA-256 and checked against `metadata.etl_watermark`. If the file hash exists with status `SUCCESS`, `ChangeDetector` classifies it as `DUPLICATE` and safely skips ingestion. Manual operator replay overrides this check cleanly via `--replay`."*

### Q42: How does your quarantine mechanism handle bad records without failing the pipeline?
- **Strong Answer**: *"Vectorized validators separate malformed records (negative prices, future timestamps) from valid rows. Valid rows proceed through transformation and loading, while invalid rows are quarantined to `data/bad_records/<run_id>/invalid_rows.csv` alongside a machine-readable `validation_report.json`."*

---

## Part 4: Testing, Performance & Future Scale (Questions 71 – 100)

### Q71: How would this architecture scale if feed volumes grew to 1 Terabyte daily?
- **Strong Answer**: *"For multi-terabyte feeds, Pandas DataFrame transformations would be migrated to PySpark DataFrames distributed across an AWS EMR or Databricks cluster. The database loader would stream output Parquet files into Snowflake or AWS Redshift via `COPY INTO`."*

### Q72: How does your test harness generate realistic test scenarios?
- **Strong Answer**: *"Our test harness provides a `SyntheticDataGenerator` producing sales feeds with configurable anomaly percentages (duplicate IDs, negative prices, future dates), pre-built `ScenarioBuilder` objects, and reusable ETL assertions (`assert_reconciled`)."*
