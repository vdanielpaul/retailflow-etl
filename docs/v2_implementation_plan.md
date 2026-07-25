# RetailFlow ETL v2.0 — Engineering Implementation Plan

This document serves as the master engineering roadmap for migrating the RetailFlow ETL pipeline to Google Cloud Platform. The plan is divided into 5 sequential, testable milestones.

---

## Milestone 1: Cloud Infrastructure & Storage Setup

### Objective
Deploy the foundation layer of the serverless cloud data platform. This sets up storage buckets and BigQuery datasets.

### Scope
- **In Scope**: Terraform configuration, GCP Storage Buckets setup, BigQuery datasets, and table schema DDL definitions.
- **Out of Scope**: Cloud Functions code, Apache Beam pipelines, and Java/Python database client wrapper code.

### Prerequisites
- Active GCP Project with permissions to create IAM roles, storage buckets, and BigQuery datasets.
- Local Terraform CLI and Google Cloud SDK authenticated to the target GCP project.

### Repository Changes
- **Added**:
  - `deploy/main.tf` (Main entry point calling GCS modules)
  - `deploy/modules/storage/main.tf` (Application & state buckets configuration)
  - `deploy/modules/storage/variables.tf` (Storage module variables)
  - `deploy/modules/storage/outputs.tf` (Storage module outputs)
  - `deploy/bigquery.tf` (Terraform BigQuery datasets and metadata tables setup)
  - `sql/bigquery/01_create_bronze.sql` (Bronze raw staging table DDL)
  - `sql/bigquery/02_create_silver.sql` (Silver CDM canonical table DDL)
  - `sql/bigquery/03_create_gold.sql` (Gold star schema dimensions and partitioned facts DDL)
  - `sql/bigquery/04_create_metadata.sql` (Audit and watermark table DDL)

### Detailed Task Breakdown
1. **Task 1.1**: Set up the `deploy/` directory and configure the Terraform GCP provider.
2. **Task 1.2**: Define GCS buckets with Object Lifecycle rules. This includes the application data buckets (`raw`, `archive`, `quarantine`) and the dedicated, infrastructure-only `tfstate` bootstrap bucket.
   * *Bootstrap State Migration (Separate Post-Apply Activity)*: After `tfstate` bucket is created, uncomment the remote backend config in `backend.tf` and run `terraform init -migrate-state` to migrate state.
3. **Task 1.3**: Configure Terraform BigQuery datasets (`retailflow_bronze`, `retailflow_silver`, `retailflow_gold`, `retailflow_metadata`).
4. **Task 1.4**: Define BigQuery DDL schema scripts for Bronze, Silver, Gold, and Metadata tables.
5. **Task 1.5**: Execute schema deployment via script verification or Terraform BigQuery table resources.

### Deliverables
- Three configured GCS application buckets: `raw-bucket`, `archive-bucket`, `quarantine-bucket`.
- One dedicated GCS `tfstate` bootstrap bucket (not part of the application data flow).
- Top-level and module outputs exposing bucket names and urls.
- Completed state migration to GCS.

### Verification Checklist
- [ ] GCS application and state buckets exist and block public access.
- [ ] Terraform state migration succeeds and remote GCS state locks are active.
- [ ] BigQuery datasets exist in the designated region.
- [ ] Target schemas match table DDL definitions.

### Testing Strategy
- Execute `terraform plan` and verify resources match target specifications.
- Run database connection check queries against empty BigQuery datasets.

### Risks
- **Risk**: Terraform configuration errors or permission issues.
- **Mitigation**: Use minimal privilege IAM Service Accounts during local terraform tests.

### Exit Criteria
- `terraform apply` executes successfully, the remote state backend is migrated to GCS, and all BigQuery warehouse tables are queryable.


---

## Milestone 2: Thin Ingestion Cloud Function

### Objective
Deploy the event-driven serverless ingestion orchestrator Cloud Function that detects newly arrived storage files, validates file metadata, checks watermarks, and triggers downstream processing.

### Scope
- **In Scope**: Ingestion Cloud Function trigger code, GCS Storage finalize event binding, BigQuery watermark checks, and Pub/Sub publishing.
- **Out of Scope**: Cloud Dataflow Apache Beam execution code and SQL warehouse joins.
 
### Prerequisites
- Milestone 1 deployed successfully.
- GCS raw bucket configured to emit finalize events.
 
### Repository Changes
- **Added**:
  - `src/retailflow/cloud/main.py` (Cloud Function trigger handler)
  - `src/retailflow/cloud/requirements.txt` (Cloud Function dependency pins)
  - `deploy/cloud_functions.tf` (Terraform Cloud Function resource definition)
  - `deploy/pubsub.tf` (Terraform Pub/Sub topic definition)
- **Modified**:
  - `deploy/main.tf` (Append Cloud Function IAM policy bindings)
 
### Detailed Task Breakdown
1. **Task 2.1**: Define Pub/Sub topic `retailflow-ingest-trigger-topic` and subscription via Terraform.
2. **Task 2.2**: Write Cloud Function entry point function to calculate file hashes and check duplicate files via BigQuery watermark queries.
3. **Task 2.3**: Implement Pub/Sub message payload creation containing `source_file` metadata and `run_id`.
4. **Task 2.4**: Configure Terraform deployment definitions for Cloud Functions packaging.
 
### Deliverables
- Deployed Pub/Sub topic and subscription.
- Active Cloud Function triggered by GCS object creation events.
 
### Verification Checklist
- [ ] Uploading a file to `gs://raw-bucket/` triggers the Cloud Function.
- [ ] Cloud Function logs output structured JSON logs.
- [ ] Pub/Sub receives the ingest event message.
 
### Testing Strategy
- **Unit Tests**: Mock GCS events and BigQuery metadata queries using python mocks.

- **Integration Tests**: Verify end-to-end event flow using local emulators.

### Risks
- **Risk**: Event loops caused by duplicate trigger executions.
- **Mitigation**: Ensure Cloud Function handles duplicate triggers idempotently by checking watermark status before publishing.

### Exit Criteria
- Uploading a new file successfully triggers Pub/Sub events; uploading a duplicate file is safely skipped.

---

## Milestone 3: Apache Beam & Distributed Dataflow Pipeline

### Objective
Evolve the core validation and transformation engine into a scalable, distributed execution pipeline using Apache Beam.

### Scope
- **In Scope**: Apache Beam pipeline runner, framework-agnostic row validation functions, data normalization, and metrics accumulation.
- **Out of Scope**: BigQuery SQL joins and loaders.

### Prerequisites
- Milestones 1 and 2 successfully deployed.
- Python Apache Beam package installed in virtual environment.

### Repository Changes
- **Added**:
  - `src/retailflow/beam/pipeline.py` (Apache Beam DAG definition)
  - `src/retailflow/beam/transforms.py` (Custom Beam ParDo transforms)
  - `src/retailflow/adapters/storage.py` (StorageProvider abstraction)
- **Modified**:
  - `src/retailflow/application/validation.py` (Refactor rules into pure-python functions)
  - `src/retailflow/application/transformation.py` (Refactor normalizers into pure-python functions)

### Detailed Task Breakdown
1. **Task 3.1**: Create `StorageProvider` interfaces and implement local vs GCS adapters.
2. **Task 3.2**: Refactor validation engines from v1.0 into pure-python row validator functions.
3. **Task 3.3**: Implement Beam custom `ParDo` classes to run validation and cleaning transforms.
4. **Task 3.4**: Write Apache Beam pipeline to read files from GCS and output to Silver GCS staging.

### Deliverables
- Deployed Apache Beam DirectRunner and Dataflow pipeline classes.
- Validated canonical schema dataset files exported to GCS.

### Verification Checklist
- [ ] Beam pipeline parses CSV rows correctly.
- [ ] Validation exceptions are successfully routed to the GCS quarantine bucket.
- [ ] Pipeline executes locally using the DirectRunner.

### Testing Strategy
- **Beam Tests**: Use Beam `TestPipeline` to verify row transformations in isolation.
- **Unit Tests**: Verify validator functions output correct boolean masks.

### Risks
- **Risk**: Out-of-memory errors on worker nodes.
- **Mitigation**: Avoid side inputs for large dimensions; delegate joins to BigQuery.

### Exit Criteria
- Test datasets run through the Beam pipeline locally and export validated Silver CSV payloads.

---

## Milestone 4: BigQuery Loader & SQL Transforms

### Objective
Deploy the target warehouse loading mechanism and database schema transformations in BigQuery.

### Scope
- **In Scope**: BigQuery Loader class, BigQuery Load Jobs API integration, and SQL MERGE scripts for Star Schema joins.
- **Out of Scope**: Cloud scheduler automation and custom dashboards.

### Prerequisites
- Milestones 1, 2, and 3 successfully deployed.

### Repository Changes
- **Added**:
  - `src/retailflow/adapters/warehouse.py` (WarehouseClient abstraction)
  - `src/retailflow/loader/bq_loader.py` (BigQuery write load job manager)
  - `sql/bigquery/05_merge_fact_sales.sql` (SQL MERGE fact ingestion query)
- **Modified**:
  - `src/retailflow/adapters/database.py` (Deprecate PostgreSQL driver code)

### Detailed Task Breakdown
1. **Task 4.1**: Implement `BigQueryWarehouse` wrapper executing Write Load Jobs.
2. **Task 4.2**: Write BigQuery SQL MERGE query to map Silver transaction rows to Gold surrogate keys.
3. **Task 4.3**: Implement target transaction updates and historical watermarks records.

### Deliverables
- Deployed BigQuery database load adapters.
- Deployed warehouse schema DDLs and SQL merge procedures.

### Verification Checklist
- [ ] BigQuery Load Jobs write canonical records to Silver datasets successfully.
- [ ] SQL MERGE queries resolve surrogate keys and insert facts into Gold tables.
- [ ] All database updates execute within atomic write limits.

### Testing Strategy
- **Integration Tests**: Execute BigQuery Load Jobs using mock parameters.
- **SQL Tests**: Run merge statements on mock Silver tables and verify output dimensions.

### Risks
- **Risk**: Slow query performance or scan cost growth during joins.
- **Mitigation**: Cluster target tables on surrogate key join columns.

### Exit Criteria
- Uploaded data is successfully loaded into Gold tables with resolved surrogate keys.

---

## Milestone 5: End-to-End Testing & Observability

### Objective
Deploy operational monitoring, error alerting, and CI/CD pipelines. Execute E2E validation tests.

### Scope
- **In Scope**: GitHub Actions pipelines, Cloud Monitoring alert rules, logging log queries, and E2E test runs.
- **Out of Scope**: New functional feature additions.

### Prerequisites
- Milestones 1 through 4 successfully deployed.

### Repository Changes
- **Added**:
  - `.github/workflows/deploy.yml` (Terraform and Application CI/CD workflow)
  - `deploy/monitoring.tf` (Terraform monitoring and alerts definition)
  - `tests/e2e/test_gcp_pipeline.py` (Cloud end-to-end validation test)

### Detailed Task Breakdown
1. **Task 5.1**: Define Cloud Monitoring dashboards and Dataflow status monitoring rules via Terraform.
2. **Task 5.2**: Write GitHub Actions build pipelines with automated Terraform plans.
3. **Task 5.3**: Build and execute E2E test suites inside the target GCP pre-production project.

### Deliverables
- CI/CD release workflow configured in GitHub.
- Deployed Cloud Monitoring alert dashboards.
- Fully verified end-to-end cloud pipeline.

### Verification Checklist
- [ ] Complete pipeline executes from raw file upload to Gold BigQuery insertion without manual steps.
- [ ] GCS bucket events trigger Cloud Functions, Pub/Sub, Dataflow, and BigQuery.
- [ ] Monitoring dashboard displays correct data volume metrics.

### Testing Strategy
- Execute cloud end-to-end integration tests using synthetic datasets.

### Risks
- **Risk**: Flaky integration tests or deployment credential leaks.
- **Mitigation**: Use restricted IAM roles for GitHub Actions execution.

### Exit Criteria
- Complete E2E integration test runs successfully in under 10 minutes and code coverage metrics exceed 90%.
