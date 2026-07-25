# RetailFlow ETL v2.0 — Engineering Implementation Plan

This document serves as the master engineering roadmap for migrating the RetailFlow ETL pipeline to Google Cloud Platform. The plan is organized around **Vertical Slices** of business capabilities.

---

## Milestone 1: Foundation Infrastructure & Storage Setup (COMPLETED)

### Objective
Deploy GCS storage bucket containers and BigQuery analytical dataset containers to establish the workspace layout.

### Detailed Task Status
- **Task 1.1** [x]: Set up the `deploy/` directory and configure the Terraform GCP provider. (Completed)
- **Task 1.2** [x]: Define GCS buckets with Object Lifecycle rules. This includes the application data buckets (`raw`, `archive`, `quarantine`) and the dedicated, infrastructure-only `tfstate` bootstrap bucket. (Completed)
- **Task 1.3** [x]: Configure Terraform BigQuery datasets (`retailflow_bronze`, `retailflow_silver`, `retailflow_gold`, `retailflow_metadata`). (Completed)

---

## Milestone 2: Vertical Slice 1 — Event-Driven File Ingestion

### Objective
Establish the event-driven file ingestion workflow. When a POS CSV file lands in GCS, the system detects it, extracts metadata, validates watermarks/duplicate hashes, logs the event, and publishes an ingest event trigger.

### Scope
- **In Scope**: Pub/Sub topic and subscription setup, Cloud Function ingestion trigger, file SHA-256 hash calculation, BigQuery watermark lookup, and structured JSON logs.
- **Out of Scope**: Apache Beam processing, data transformations, and SQL warehouse joins.

### Detailed Task Breakdown
- **Task 2.1**: Define GCS object finalize triggers, Pub/Sub topics, and Cloud Function infrastructure via Terraform.
- **Task 2.2**: Implement the Cloud Function handler to detect GCS uploads, validate file metadata, and calculate SHA-256 file hashes.
- **Task 2.3**: Integrate BigQuery watermark duplicate checking (verifying if file hash has already been processed).
- **Task 2.4**: Implement structured JSON logging and publish trigger events to Pub/Sub to signal downstream Dataflow.

### Deliverables
- Active GCS trigger binding to Pub/Sub topic `retailflow-ingest-trigger-topic`.
- Deployed thin Cloud Function orchestrating GCS events.
- Structured watermark log tables checked and updated.

### Verification Checklist
- [ ] Uploading a POS CSV file to `gs://raw-bucket/` triggers the Cloud Function.
- [ ] Duplicate uploads are detected and logged as duplicates, and do not publish events.
- [ ] Pub/Sub receives ingestion trigger events containing file path and run metrics.

### Testing Strategy
- **Unit Tests**: Mock GCS events and BigQuery watermark database select statements.
- **Integration Tests**: Verify event trigger bindings inside local GCP emulators.

---

## Milestone 3: Vertical Slice 2 — Batch Processing Pipeline

### Objective
Implement the data processing core. Consume the ingestion event, read and validate raw CSV rows, normalize schema data to the Canonical Data Model (CDM), calculate financial metrics, and load records to `silver.sales_canonical`.

### Scope
- **In Scope**: Apache Beam pipeline definitions, raw GCS file reader, row validations (negative quantites, future dates), CDM mapping, and BigQuery write load jobs.
- **Out of Scope**: IAM roles, SQL joins, and reporting table updates.

### Detailed Task Breakdown
- **Task 3.1**: Create `StorageProvider` GCS adapter and refactor validation rules into pure-python functions.
- **Task 3.2**: Develop the Apache Beam pipeline transforms running on Cloud Dataflow.
- **Task 3.3**: Configure Beam output partitioning to write clean rows to BigQuery Silver and bad records to the GCS quarantine bucket.

---

## Milestone 4: Vertical Slice 3 — Warehouse Modeling

### Objective
Transform cleaned Silver tables into Gold analytical reporting tables using SQL-based dimensional star schemas.

### Scope
- **In Scope**: BigQuery Gold table DDLs, SQL MERGE queries, key mapping joins, and watermark status updates.
- **Out of Scope**: CI/CD automation and alerting.

### Detailed Task Breakdown
- **Task 4.1**: Define BigQuery table schemas for `fact_sales`, `dim_customer`, `dim_product`, `dim_store`, `dim_employee`.
- **Task 4.2**: Write SQL MERGE procedures to map Silver transactional natural keys into Gold surrogate keys.
- **Task 4.3**: Integrate warehouse run history logging into the `metadata.etl_audit_log` tables.

---

## Milestone 5: Vertical Slice 4 — Platform Operations

### Objective
Operationalize and secure the deployed resources using enterprise-grade platform controls.

### Scope
- **In Scope**: IAM policies, Service Account scopes, Secret Manager credentials integration, Cloud Monitoring dashboards, and GCS remote backend state migration.

### Detailed Task Breakdown
- **Task 5.1**: Deploy Service Accounts with least-privilege policies.
- **Task 5.2**: Move Terraform backend state from local to the GCS `tfstate` bucket.
- **Task 5.3**: Deploy alerting triggers for pipeline errors and create metrics dashboards.

---

## Milestone 6: Vertical Slice 5 — CI/CD & Production Readiness

### Objective
Prepare the repository for long-term production maintenance.

### Scope
- **In Scope**: GitHub Actions pipelines, deployment playbooks, disaster recovery runbooks, and end-to-end integration tests.
