# RetailFlow ETL v2.0 — Cloud-Native Modernization Design

This document serves as the authoritative technical design and migration specification for modernizing the RetailFlow ETL v1.0 single-node pipeline into a serverless, cloud-native data platform on Google Cloud Platform (GCP).

---

## 1. Modernization Goals

### Business Goals
- **Eliminate Operational Overhead**: Transition from managing local VM cron schedules, local filesystems, and PostgreSQL servers to serverless, fully managed GCP services.
- **Support Store Scale Expansion**: Enable the pipeline to scale from 250 store locations to 2,500+ locations and online channels without database resource bottlenecks.
- **Lower Total Cost of Ownership (TCO)**: Shift from fixed local compute hardware costs to a pay-per-use utility model using on-demand serverless resources.

### Technical Goals
- **Serverless Execution**: Run validations, transformations, and warehouse ingestion on demand without maintaining virtual machines.
- **Decoupled Data Storage**: Migrate local directory states into highly available Google Cloud Storage (GCS) buckets.
- **Scale-Out Data Processing**: Migrate the single-node memory-bound validation and transformation layers into a distributed Google Cloud Dataflow runner.
- **Analytical Data Warehouse**: Migrate PostgreSQL transactional star schemas to Google BigQuery datasets.

### Non-Goals
- **Zero-Downtime Migration**: Continuous ingestion is not required; a scheduled nightly maintenance window is acceptable.
- **Real-Time Streaming Ingestion**: The migration targets daily batch store feed CSVs; real-time event ingestion is out of scope.
- **Multi-Cloud Portability**: The target architecture utilizes native GCP integrations.

### Success Criteria
- **100% Business Logic Integrity**: All data cleaning, normalization, validation, and metrics calculations must output the identical values as v1.0.
- **Zero Orphan Loads**: All warehouse insertions must be fully atomic; failed pipeline runs must never load partial records.
- **No Manual Infrastructure Deployment**: All resources (GCS buckets, Pub/Sub topics, Cloud Functions, BigQuery datasets, IAM roles) are deployed via infrastructure-as-code.

### Migration Principles
- **Preserve Business Logic**: Reuse the mature v1.0 Pandas cleaners, normalizers, and metric calculation formulas instead of writing them from scratch.
- **Replace Infrastructure First**: Move the storage, orchestrator, database, and logs to GCP services before rewriting core transformation code.
- **Managed Over Self-Managed**: Prioritize native, serverless GCP services to minimize operational maintenance.

---

## 2. Current vs Target Architecture

### Current v1.0 Architecture (Single-Node PostgreSQL)
```text
[Daily POS CSVs] 
       │
       ▼
 [data/raw/ Folder] 
       │
       ▼
 [Local Cron CLI] ──(Check SHA-256 Hash)──> [metadata.etl_watermark]
       │
       ▼
 [Validation Engine] ──(Bad Rows)──> [data/bad_records/ Folder]
       │ (Clean Rows)
       ▼
 [Pandas Transformation] ──(In-Memory Keys Cache)──> [dim_product / dim_store / dim_employee]
       │
       ▼
 [PostgreSQL COPY Ingestion] ──(Single Transaction Scope)
       │
       ▼
 [(PostgreSQL retailflow_dw Database)]
```

### Target v2.0 Architecture (Cloud-Native GCP)
```text
[Daily POS CSVs] 
       │
       ▼
[Cloud Storage (raw-bucket)]
       │ (Object Created Event)
       ▼
[Cloud Function (Orchestrator)] ──(Evaluate Hash)──> [BigQuery metadata.etl_watermark]
       │ (Publish Ingest Event)
       ▼
[Cloud Pub/Sub (ingest-topic)]
       │ (Trigger Job)
       ▼
[Cloud Dataflow (Apache Beam)] ──(Bad Rows)──> [Cloud Storage (quarantine-bucket)]
       │ (Execute Pandas Clean/Transform/Enrich)
       ▼
[BigQuery Ingestion API] ──(Atomic Write Load Job)
       │
       ▼
[(Google BigQuery Warehouse: datasets bronze, silver, gold)]
       │
    [Cloud Logging & Cloud Monitoring & Alerts]
```

---

## 3. GCP Service Mapping

| Current v1.0 Component | Target v2.0 GCP Equivalent | Architectural Rationale for Decision |
|---|---|---|
| **Local Folder (`data/raw/`)** | **Cloud Storage (Raw Bucket)** | Provides secure, durable, serverless object storage that triggers events upon file uploads. |
| **Local Folder (`data/bad_records/`)**| **Cloud Storage (Quarantine Bucket)**| Securely stores rejected records and validation reports in cloud object storage. |
| **CLI Execution (`cli.py`)** | **Cloud Function (Orchestrator)** | Triggered by Cloud Storage events. Inspects file metadata, runs health checks, checks watermarks, and kicks off downstream jobs. |
| **Cron Scheduling** | **Cloud Scheduler** | Standard serverless cron manager used to trigger cleanup tasks and daily telemetry alerts. |
| **PostgreSQL Database** | **Google BigQuery** | Serverless, highly scalable analytical column-store warehouse. Eliminates write locks and scales to petabytes automatically. |
| **Local Logs (`logs/`)** | **Cloud Logging** | Consolidates application output logs. Integrates with Log Router and Alert Policies. |
| **Metrics Collector** | **Cloud Monitoring** | Tracks pipeline stage latency metrics, failure metrics, and counts. Exposes dashboards. |
| **Watermark & Audit Tables** | **BigQuery Metadata Dataset** | Watermark and audit log tables are stored inside a dedicated metadata dataset in BigQuery. |
| **Environment Configs (`.yaml`)** | **Secret Manager & Environment Vars**| Database hosts and parameters are loaded via environment variables; credentials are loaded from Secret Manager. |

---

## 4. Dataflow Design & Code Reuse (Option A)

### Framework-Agnostic Extraction
We reject the approach of wrapping the legacy Pandas validation engine inside Beam workers because it introduces local filesystem dependencies and limits Beam's distributed execution scaling.

Instead, we select **Option A**:
- **Apache Beam** acts as the distributed execution and orchestration engine.
- Reusable, pure-Python logic from v1.0 (`cleaner`, `normalizer`, `enricher`, and validation rules) is extracted from Pandas-specific containers into framework-agnostic helper functions that operate on row dictionaries (`dict[str, Any]`).
- These helper functions are executed inside Beam `ParDo` transforms.

```text
               Apache Beam Execution (Dataflow)
                              │
            ┌─────────────────┴─────────────────┐
            ▼                                   ▼
 [Read GCS File]                       [Map Row Elements]
            │                                   │
            ▼                                   ▼
 [ParDo(ValidateRowFn)]                [ParDo(TransformRowFn)]
  Calls helper functions                Calls clean/normalizer helpers
  - Checks quantity > 0                 - Lowercases emails
  - Checks price >= 0                   - Rounds unit price to 2 decimals
            │                                   │
            ▼                                   ▼
 [Output PCollection]                  [Output PCollection]
  Split clean vs invalid                Ready for BigQuery Ingestion
```

---

## 5. Medallion Data Flow & BigQuery Architecture

To establish a strict Medallion architecture, data moves sequentially through three BigQuery datasets:

```text
[GCS Raw CSV File]
       │
       ▼
[BigQuery bronze.sales_raw] ──(Append-Only Raw Records with metadata)
       │
       ▼ (Dataflow Validation & Normalization)
       │
[BigQuery silver.sales_canonical] ──(Cleaned Schema-Enforced CDM Rows)
       │
       ▼ (BigQuery SQL Merges & JOINs)
       │
[BigQuery gold.fact_sales] ──(Dimension Surrogate Keys Resolved)
```

1. **Bronze Dataset (`bronze.sales_raw`)**:
   - Represents the raw, immutable ingest layer.
   - Contains raw string payload records loaded directly from GCS, appended with `ingestion_timestamp` and `source_filename`.
2. **Silver Dataset (`silver.sales_canonical`)**:
   - Represents validated, cleaned, and schema-enforced records.
   - Corresponds directly to the **Canonical Data Model** (CDM).
3. **Gold Dataset (`gold.fact_sales`)**:
   - Represents the dimensional warehouse layer.
   - Data is joined with Gold dimension tables (`dim_customer`, `dim_product`, `dim_store`) to resolve surrogate keys.

---

## 6. BigQuery Write Strategy Comparison

We compare the three primary database loading options to select the optimal write strategy for daily batch retail feeds:

| Ingestion Method | Latency Profile | Write Cost | Transaction Support | Recommendation |
|---|---|---|---|---|
| **BigQuery Load Jobs** | Batch (Minutes) | **Free** (Unlimited daily slots) | Atomic table-level replacement | **Recommended** |
| **Storage Write API** | High-throughput stream | Pay-per-GB written | Stream-level commits | Exceeded for batch scale |
| **Streaming Inserts** | Real-time (Seconds) | Pay-per-row written | Row-level consistency | Exceeded for batch scale |

### Selection Rationale
- We select **BigQuery Load Jobs** in batch write mode. Since daily retail store sales are exported as batch files overnight, real-time streaming is not required. BigQuery Load Jobs are **free of ingestion cost**, support automatic schema auto-detection, and provide robust atomic table-level write boundaries.

---

## 7. Watermark State Storage Comparison

We evaluate where to store pipeline watermark timestamps and file hashes:

| Storage Backend | Read/Write Latency | Operational Cost | Concurrency Control | Recommendation |
|---|---|---|---|---|
| **BigQuery Table** | High (2-3 seconds) | Scan costs per query | No locking mechanisms | Exceeded for watermarks |
| **Google Cloud SQL** | Low (Millisecond) | High (Requires dedicated VM) | ACID database locks | Over-engineered |
| **Cloud Firestore** | **Extremely Low** | **Free Tier** (10k writes/day) | Document-level transactions | **Recommended** |

### Selection Rationale
- We select **Google Cloud Firestore** (in Datastore mode) for high-watermark state storage. Firestore is a serverless, highly available NoSQL database that offers sub-millisecond document lookups. It provides atomic transaction locks to prevent concurrency conflicts when multiple store files are uploaded simultaneously, and easily fits within GCP's free usage tier for batch scale.

---

## 8. Cloud Function & Dataflow Responsibilities

To keep Cloud Functions thin and avoid running business logic inside triggers, responsibilities are split:

```text
 ┌────────────────────────────────────────────────────────┐
 │ Cloud Function: Ingest Orchestrator (Thin Trigger)     │
 ├────────────────────────────────────────────────────────┤
 │ - GCS object finalized trigger detection               │
 │ - File metadata validation (size > 0, suffix validation)│
 │ - Calculate SHA-256 file content hash                  │
 │ - Query Firestore to check for duplicate file hashes   │
 │ - Publish trigger event message to Pub/Sub             │
 └──────────────────────────┬─────────────────────────────┘
                            │
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ Cloud Dataflow Engine (Apache Beam Distributed Runner)  │
 ├────────────────────────────────────────────────────────┤
 │ - Read raw CSV lines from GCS bucket                   │
 │ - Execute framework-agnostic row validation rules      │
 │ - Write rejected rows to GCS quarantine bucket        │
 │ - Normalize validated records into Canonical CDM format│
 │ - Compute financial sales metric derivations           │
 │ - Trigger BigQuery Load Job to ingest bronze dataset   │
 └────────────────────────────────────────────────────────┘
```

---

## 9. Surrogate Key Resolution Design

We compare options for resolving natural keys (`store_id`, `product_id`) into warehouse keys (`store_sk`, `product_sk`) at scale:

| Key Resolution Option | CPU Overhead | Memory Overhead | Network Latency | Recommendation |
|---|---|---|---|---|
| **Dataflow Side Inputs** | Low | High (Loads entire dim to RAM) | None | Exceeded for large dims |
| **Beam external lookups**| High | Low | High (Row-level DB queries) | Not recommended |
| **BigQuery SQL JOIN** | **Extremely Low** | **None** | None (Executes in BQ engine) | **Recommended** |

### Selection Rationale
- We select **BigQuery SQL JOIN** executed during the Silver-to-Gold database execution step. By executing key mapping in BigQuery, we eliminate loading large dimension tables into Dataflow worker memory, optimize BigQuery's distributed join architecture, and keep Dataflow workers focused solely on validation and cleaning.

---

## 10. Repository Evolution Layout

The repository evolves from v1.0 without losing its modularity. Legacy business logic remains reusable for local execution, while cloud infrastructure and Beam pipelines are isolated:

```text
retailflow-etl/
├── config/                  # Environment YAML profiles (local, development, production)
├── deploy/                  # Terraform IaC configurations
│   ├── main.tf              # Main resources provider
│   ├── gcs.tf               # Cloud Storage buckets setup
│   ├── bigquery.tf          # BigQuery datasets & schemas setup
│   ├── pubsub.tf            # Pub/Sub topics configuration
│   └── secrets.tf           # Secret Manager parameters
├── src/retailflow/          # Main application package
│   ├── functions/           # Cloud Functions source code
│   │   ├── orchestrator/    # entry point for storage trigger function
│   │   └── main.py          # Trigger handler
│   ├── pipeline/            # Reusable core pipeline libraries
│   │   ├── beam_pipeline.py # Apache Beam Dataflow pipeline definition
│   │   ├── validation.py    # Reusable validator components
│   │   └── transformation.py# Reusable transform cleaner/enricher rules
│   ├── database/            # BigQuery client wrapper
│   │   └── bigquery_client.py
│   ├── loader/              # BigQuery data loaders
│   │   └── bq_loader.py     # Writes tables using load jobs
│   └── audit/               # BigQuery metadata audit publishers
├── sql/                     # BigQuery DDL schema scripts
│   └── bigquery/            # BigQuery DDL setup files
├── tests/                   # Reusable Pytest suite
└── pyproject.toml
```

---

## 11. BigQuery Modeling Details

### Dataset Naming
- `retailflow_bronze`: Staging dataset for raw ingestion tables.
- `retailflow_silver`: Validated canonical database tables.
- `retailflow_gold`: Dimensional star schema tables.
- `retailflow_metadata`: Watermarks and audit execution databases.

### Table Naming
- Fact Table: `retailflow_gold.fact_sales`
- Dimension Tables: `retailflow_gold.dim_customer`, `retailflow_gold.dim_product`, `retailflow_gold.dim_store`, `retailflow_gold.dim_employee`, `retailflow_gold.dim_date`

### Audit & Partitioning Parameters
- `ingestion_timestamp`: UTC timestamp tracking when the row entered BigQuery.
- `source_filename`: Name of the source feed file.
- `audit_run_id`: Run ID tracking the pipeline execution instance.
- **Partitioning**: `fact_sales` partitioned by day on `transaction_time`.
- **Clustering**: `fact_sales` clustered on `store_sk` and `product_sk`.

### Schema Evolution Strategy
- Additions of columns are allowed (`schema_update_option = ALLOW_FIELD_ADDITION`). Reductions or type changes require deploying a new target table version and running a migration script.

---

## 12. Terraform Managed Infrastructure

All GCP resources are managed via **Terraform**:
- **Storage Buckets**: `raw-bucket`, `archive-bucket`, `quarantine-bucket` (with Object Lifecycle policies).
- **BigQuery Datasets**: `bronze`, `silver`, `gold`, `metadata`.
- **Pub/Sub Topics**: `ingestion-trigger-topic` and subscriptions.
- **Service Accounts**: `sa-orchestrator` and `sa-dataflow-worker` with minimal IAM roles.
- **Secret Manager**: Secret variables for system credentials.
- **Cloud Monitoring**: Alert Policies and dashboard views.

---

## 13. CI/CD Pipeline Design

We configure a serverless build and deployment lifecycle using **GitHub Actions**:

```text
                        GitHub Actions Pipeline
                                   │
                 ┌─────────────────┴─────────────────┐
                 ▼                                   ▼
        [Test & Static Analysis]            [Terraform Deployment]
                 │                                   │
                 ▼                                   ▼
        - Run ruff/mypy checks              - Plan infrastructure changes
        - Run Pytest suites                 - Apply configuration to GCP
                 │                                   │
                 └─────────────────┬─────────────────┘
                                   ▼
                     [GCP Application Deployment]
                                   │
                                   ▼
                    - Build Cloud Function archive
                    - Deploy code to Cloud Functions
```

### Rollback Strategy
- **Infrastructure**: If a Terraform apply step fails, run `terraform destroy` or roll back to the last stable configuration commit.
- **Application Code**: Deploy previous stable Cloud Function zip archives from GCS using automated version tagging.

---

## 14. Development Roadmap & Milestones

The implementation of RetailFlow ETL v2.0 is structured into **5 sequential development milestones**. Each milestone must be built in a dedicated feature branch off the `develop` branch, tested in isolation, and merged back into `develop` via a Pull Request.

```text
                          [develop branch]
                                 │
           ┌─────────────────────┼─────────────────────┐
           ▼ (Feature Branch)    ▼ (Feature Branch)    ▼ (Feature Branch)
     [milestone-1]         [milestone-2]         [milestone-3]
     Infra & Storage       Ingest Trigger        Dataflow Pipeline
           │                     │                     │
           ▼ (Merge PR)          ▼ (Merge PR)          ▼ (Merge PR)
     [develop branch] ───> [develop branch] ───> [develop branch]
```

### Milestone 1: Cloud Infrastructure & Storage Setup
- **Branch**: `feature/milestone-1-infra`
- **Scope**: Define and deploy GCS buckets, BigQuery datasets, Pub/Sub topics, and Firestore collections using Terraform.
- **Verification**: Run `terraform apply` to verify successful resource creation in your target GCP project.

### Milestone 2: Thin Ingestion Cloud Function
- **Branch**: `feature/milestone-2-trigger`
- **Scope**: Write the Cloud Function trigger to calculate file hashes, query Firestore for duplicates, and publish messages to Pub/Sub.
- **Verification**: Upload mock files to GCS and verify the Pub/Sub topic receives the trigger message.

### Milestone 3: Apache Beam & Distributed Dataflow Pipeline
- **Branch**: `feature/milestone-3-dataflow`
- **Scope**: Re-organize v1.0 validation and transformation rules into modular helper functions and write the Beam pipeline.
- **Verification**: Execute the Beam job locally using the DirectRunner on sample datasets.

### Milestone 4: BigQuery Loader & SQL Transforms
- **Branch**: `feature/milestone-4-loader`
- **Scope**: Implement the BigQuery Write Load Job engine and SQL merge scripts to transform Silver canonical tables into Gold dimension/fact tables.
- **Verification**: Query BQ tables to verify data loading and key mapping consistency.

### Milestone 5: End-to-End Testing & Observability
- **Branch**: `feature/milestone-5-e2e`
- **Scope**: Deploy Cloud Monitoring dashboards and verify the complete end-to-end event flow.
- **Verification**: Upload `sales_1k.csv` to GCS raw bucket and verify ingestion into BigQuery gold tables.

---

## 15. Future v3 Evolution

The following capabilities are deferred to v3:
- **Real-Time Streaming**: Streaming POS transaction events using Apache Kafka and BigQuery Storage Write API streaming.
- **Change Data Capture (CDC)**: Capture source database changes using Debezium and stream them directly to BigQuery.
- **Dataform / dbt Integration**: Manage SQL transforms inside the Silver-to-Gold layer using Dataform or dbt.
- **Orchestration Workflow**: Implement Apache Airflow/Cloud Composer to orchestrate complex dependencies.

---

## 16. Final Recommendation & Review

### Principal Data Engineer Assessment
- **Realism**: The revised architecture represents a standard modern enterprise GCP data platform.
- **Hiring Manager Appeal**: The design demonstrates a solid understanding of GCP data engineering principles, and aligns well with what is expected of a candidate with 1-2 years of experience.
- **Simplicity Check**: The architecture is clean and avoids over-engineering by using serverless integrations instead of managing complex systems like Apache Airflow or Kubernetes.
