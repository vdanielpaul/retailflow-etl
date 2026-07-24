# Future Improvements & Scale-Out Roadmap

## Overview
While RetailFlow ETL is built as a single-node Python and PostgreSQL pipeline for batch processing 250+ store locations, enterprise volume growth requires scaling architectures.

---

## Architectural Scaling Roadmap

### 1. Distributed Compute Upgrade (PySpark / Delta Lake)
- **Current Bottleneck**: Pandas loads full file feeds into memory on single-node runner.
- **Future Solution**: Migrate validation and transformation logic to PySpark on AWS EMR or Databricks.
- **Benefit**: Linear horizontal scaling handling millions of transactions per minute across thousands of store locations.

### 2. Orchestration & Workflow Scheduling (Apache Airflow / Prefect)
- **Current Setup**: Python script execution via cron or manual trigger.
- **Future Solution**: Wrap pipeline tasks inside an Apache Airflow DAG with SLAs, dynamic retry tasks, dependency graphs, and Slack alert integrations.

### 3. Cloud Data Warehouse Migration (Snowflake / AWS Redshift / BigQuery)
- **Current Target**: PostgreSQL local/RDS server.
- **Future Solution**: Migrate target warehouse tables to Snowflake or Redshift using micro-batch loading (Snowpipe or Redshift Copy commands from S3).

### 4. Real-time Streaming Ingestion (Kafka / Flink)
- **Current Frequency**: Nightly CSV batch uploads.
- **Future Solution**: Deploy Kafka POS event producers and Apache Flink stream consumers for real-time sales dashboards.
