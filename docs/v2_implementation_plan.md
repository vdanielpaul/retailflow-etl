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

## Milestone 2: Vertical Slice 1 — Event-Driven File Ingestion (COMPLETED)

### Objective
Establish the event-driven file ingestion workflow. When a POS CSV file lands in GCS, the system detects it, extracts metadata, validates watermarks/duplicate hashes, logs the event, and publishes an ingest event trigger.

### Scope
- **In Scope**: Pub/Sub topic and subscription setup, Cloud Function ingestion trigger, file SHA-256 hash calculation, BigQuery watermark lookup, and structured JSON logs.
- **Out of Scope**: Apache Beam processing, data transformations, and SQL warehouse joins.

### Detailed Task Breakdown
- **Task 2.1** [x]: Define GCS object finalize triggers, Pub/Sub topics, and Cloud Function infrastructure via Terraform. (Completed)
- **Task 2.2** [x]: Implement the Cloud Function handler to detect GCS uploads, validate file metadata, and calculate SHA-256 file hashes. (Completed)
- **Task 2.3** [x]: Integrate BigQuery watermark duplicate checking. (Completed)
- **Task 2.4** [x]: Implement structured JSON logging and publish trigger events to Pub/Sub. (Completed)

---

## Milestone 3: Vertical Slice 2 — Batch Processing Pipeline

### Objective
Implement the data processing core. Consume the ingestion event, read and validate raw CSV rows, normalize schema data to the Canonical Data Model (CDM), calculate financial metrics, and load records to `silver.sales_canonical`.

### Modernization Principle
> Modernize the execution engine while preserving the proven business logic.

Beam owns orchestration. Adapters translate between Beam elements and domain interfaces. Business logic is never reimplemented inside Beam transforms.

### Detailed Task Breakdown
- **Task 3.1** [x]: Pipeline foundation — options parser, `build_pipeline`, runner entrypoint, DirectRunner tests. (Completed — tagged `v2.0.0-m3.1`)
- **Task 3.2** [x]: Input adapters — GCS readers, CSV parsing, canonical model conversion. (Completed — tagged `v2.0.0-m3.2`)
- **Task 3.3** [x]: Validation engine integration — `BusinessRuleAdapter`, `ValidateSaleRecordFn`, quarantine routing. (Completed — tagged `v2.0.0-m3.3`)
- **Task 3.4** [ ]: Transformation engine — `TransformationAdapter`, cleaning, normalization, enrichment. (In Progress)
- **Task 3.5** [ ]: Silver loading — BigQuery target loads, metrics tracking, surrogate key resolution.

---

## Permanent Engineering Rules (Established During Milestone 3)

### Rule 1 — Pipeline Builder / Runner Separation

`build_pipeline()` assembles the Beam transform graph and returns PCollections. It does **not** attach I/O sinks. `runner.py` owns all sink wiring — GCS paths, BigQuery table references, quarantine output locations.

**Rationale:** Unit tests call `build_pipeline()` directly to verify transform logic without requiring real GCS buckets or BigQuery datasets. If sinks are embedded in the builder, tests trigger real cloud I/O.

**Enforcement:** All future pipeline stages must follow this pattern. New transforms go into `pipeline.py`; new sinks go into `runner.py`.

### Rule 2 — Adapter Framework Independence

Adapter classes (e.g., `BusinessRuleAdapter`, `TransformationAdapter`) must contain zero Beam, GCP, or cloud-specific imports. They are pure Python — callable from Beam DoFns, CLI tools, integration test harnesses, or future Spark/Flink adapters without modification.

### Rule 3 — Validator Lifecycle in DoFns

All adapters and domain engine instances are constructed once per worker in `setup()`, never once per element in `process()`. If a component introduces mutable state, the lifecycle decision must be explicitly re-evaluated.

### Rule 4 — No Business Logic in Beam Transforms

Business rules, transformation logic, and domain calculations belong in the existing domain modules. Beam transforms are orchestration-only: receive element → call adapter → route output. New business rules are added to existing validators or transformers, never implemented directly in DoFns.

---

## Known TODOs (Deferred Engineering Debt)

### TODO-001 — Row Number Tracking in Quarantine Records

**Location:** `validation_transform.py` → `_build_quarantine_record()` → `row_number: 0`

**Current state:** Quarantine records carry `row_number = 0` because CSV line numbers are not preserved through the `ReadFromText` → `ParseAndCanonicalizeCsvFn` pipeline. Records are identified by `transaction_id` in the `original_record`.

**Future enhancement:** Preserve original CSV line numbers throughout parsing so quarantine records identify the exact source line. This is operationally valuable for support investigations — an analyst can open the source file and jump directly to the failing row.

**Implementation approach:** Thread line number through `ParseAndCanonicalizeCsvFn` using `beam.io.ReadFromText` with `with_filename=True` or by numbering elements using `beam.transforms.combiners.ToList` + enumeration at read time.

**Priority:** Medium. Implement during a future hardening sprint.

---

## Future Performance Optimizations

> [!NOTE]
> None of the following optimizations are implemented in the current release. They are documented here to capture engineering intent and provide a roadmap for a future performance sprint.

### Reference Benchmark (Task 3.3)

| Metric | Value |
|---|---|
| Stage | Business Rule Validation |
| Throughput (single worker) | 1,907 records/sec |
| Bottleneck | Per-element `pd.DataFrame([record])` construction |
| Full report | [`docs/performance/validation_benchmark.md`](./performance/validation_benchmark.md) |

### Optimization Candidates

#### 1. Bundle-Level Batch Validation
Accumulate records in `start_bundle()` and validate the full bundle DataFrame in `finish_bundle()`. Eliminates per-element DataFrame construction overhead. Projected improvement: 10–50×. Tradeoff: per-element error attribution requires tracking `failed_indices` through the bundle.

#### 2. `beam.BatchElements` Transform
Insert `beam.BatchElements()` before validation transforms to adaptively batch elements based on measured processing time. Beam manages bundle sizing automatically.

#### 3. Apache Arrow-Based Record Construction
Replace `pd.DataFrame([record])` with Arrow record batch construction. Arrow's columnar format reduces memory allocation overhead, particularly for wide records.

#### 4. Beam DataFrame API Evaluation
Beam's deferred DataFrame API (`beam.dataframe`) executes Pandas-like operations natively in the execution model. If business rules can be expressed as vectorized operations, the row-level adaptation layer can be eliminated. Requires significant validator refactoring.

#### 5. DataFrame Reuse with Schema Pre-allocation
Pre-allocate a fixed-schema DataFrame template per worker and overwrite row 0 values for each element, avoiding repeated schema inference overhead.

---

## Milestone 4: Vertical Slice 3 — Warehouse Modeling

### Objective
Transform cleaned Silver tables into Gold analytical reporting tables using SQL-based dimensional star schemas.

### Detailed Task Breakdown
- **Task 4.1**: Define BigQuery table schemas for `fact_sales`, `dim_customer`, `dim_product`, `dim_store`, `dim_employee`.
- **Task 4.2**: Write SQL MERGE procedures to map Silver transactional natural keys into Gold surrogate keys.
- **Task 4.3**: Integrate warehouse run history logging into the `metadata.etl_audit_log` tables.

---

## Milestone 5: Vertical Slice 4 — Platform Operations

### Objective
Operationalize and secure the deployed resources using enterprise-grade platform controls.

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
