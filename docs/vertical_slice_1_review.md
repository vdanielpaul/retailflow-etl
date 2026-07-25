# Vertical Slice 1 Engineering Review — Event-Driven File Ingestion

This document reviews the design, implementation, and operational characteristics of the first vertical slice completed for RetailFlow ETL v2.0.

---

## 1. Business Capability Delivered

RetailFlow ETL v2.0 is designed to ingestion store files automatically as stores publish them. Vertical Slice 1 delivers **Event-Driven File Ingestion**, which automates the entry point of the pipeline:
- **Daily Store File Detection**: Stores upload daily sales files (POS CSV format) directly to Cloud Storage. The system detects files instantly without scheduled polling.
- **Deduplication Safeguards**: If a store re-uploads an identical sales file (determined by SHA-256 content hashing), the system flags it as a duplicate and terminates execution. This prevents downstream analytical tables from corrupting and saves on cloud compute costs.
- **Ingestion Run Traceability**: Every ingestion file is assigned a tracking `run_id` and a `correlation_id` trace identifier. This links the storage events, Cloud Function logs, and database watermarks together.
- **Downstream Readiness Alerting**: Validated files are published to a downstream Pub/Sub queue, alerting processing systems (like Dataflow) to execute.

---

## 2. End-to-End Ingestion Flow

The following sequence coordinates ingestion:

```
+----------------+      +-------------------+      +-------------------------+
|  Store daily   | ---> | GCS Raw Bucket    | ---> | Storage Notification    |
|  POS CSV File  |      |                   |      | (OBJECT_FINALIZE Event) |
+----------------+      +-------------------+      +-------------------------+
                                                                |
                                                                v
+----------------+      +-------------------+      +-------------------------+
| Ingestion      | <--- | Cloud Function    | <--- | Pub/Sub Topic A         |
| Application    |      | (Gen2, Stateless) |      | (ingestion-events)      |
| Service        |      +-------------------+      +-------------------------+
+----------------+
        |
        +-----> [Audit Log] Writes run status: INGESTING.
        |
        +-----> [GcsStorageService] Calculate streaming SHA-256 hash.
        |
        +-----> [MetadataRepository] Check if hash exists in BQ `etl_watermark`:
        |          |
        |          +---> If Duplicate: Log REJECTED_DUPLICATE -> Exit.
        |          +---> If New File: Write hash to Watermarks.
        |
        +-----> [EventPublisher] Publish contract payload to Topic B: processing-events.
        |
        +-----> [Audit Log] Writes run status: INGESTED.
```

---

## 3. Component Responsibilities

| Component | Responsibility | Inputs | Outputs | Dependencies |
|---|---|---|---|---|
| **Cloud Storage** | Durable raw file landing zone. | Daily POS store uploads. | OBJECT_FINALIZE events. | None. |
| **Pub/Sub Topic A** | Raw ingestion alert channel. | GCS file finalize notifications. | Buffered message queue. | None. |
| **Cloud Function Gen2** | Stateless runtime wrapper. | CloudEvent containing Pub/Sub metadata. | Decoded message dictionary. | `IngestionDependencyContainer` |
| **IngestionApplicationService** | Workflow coordinator. | Parsed GCS metadata parameters. | Operation status (ACCEPTED / REJECTED). | `MetadataRepository`, `StorageService`, `EventPublisher` |
| **Metadata Repository** | Persistent metadata layer. | Hashed values, filenames, runs. | Database duplicate lookup, watermarks, audits. | `google-cloud-bigquery` Client |
| **Event Publisher** | Downstream messaging wrapper. | `FileAcceptedEvent` data payload. | Trigger messages on Topic B. | `google-cloud-pubsub` Client |

---

## 4. Architectural Decisions

- **Two-Topic Separation** ([ADR-016](file:///Users/danielpaul/Developer/retailflow-etl/docs/adr/ADR-016.md)): Separating `ingestion-events` (raw alerts) from `processing-events` (validated files) ensures downstream processing systems are never triggered by duplicate uploads.
- **Repository Pattern** ([ADR-017](file:///Users/danielpaul/Developer/retailflow-etl/docs/adr/ADR-017.md)): Decouples database querying from coordination services. The application core works with the `MetadataRepository` abstraction, isolating BigQuery SQL queries inside infrastructure adapters.
- **Stateless Cloud Function**: The function entry point is a thin shell. If the runtime container gets warm-restarted, no local state is lost since all metadata persists in BigQuery.
- **Streaming SHA-256 Hashing**: Streams GCS content in 256KB chunks instead of downloading entire files. This maintains a small memory footprint, ensuring stability for large files.
- **Distributed Correlation Tracing**: Passing `correlation_id` trace values inside log payloads and Pub/Sub headers allows matching query traces from GCS triggers to BigQuery tables.

---

## 5. Operational Characteristics

- **Idempotency**: If the same file is uploaded multiple times, the duplicate check catches it, logs a warning, and prevents downstream events.
- **Failure Isolation**: If the BigQuery metadata warehouse is down, the run fails at the watermark boundary and logs an error without publishing processing events.
- **Retry behavior**: Gen2 Cloud Functions utilize Pub/Sub push retry policies. Standard errors exit cleanly with log warnings to prevent infinite Eventarc retries.
- **Observability**: Every action logs structured JSON payloads with trace identifiers (`correlation_id`, `ingestion_id`).

---

## 6. Deferred Work
The following elements are out of scope for Vertical Slice 1 and deferred to future milestones:
- Downstream Dataflow processing and Apache Beam batch pipeline transforms.
- Store file schema parsing and business domain validations.
- Gold medallion table DDL schemas and dimensional loading.
- System metrics dashboards and alerting monitors.

---

## 7. Lessons Learned

- **What Worked Well**: Using a dependency injection container made mocking infrastructure adapters easy, resulting in robust offline unit tests.
- **Unexpected Complexity**: Centralizing the BigQuery Client initialization in the DI container caused unit tests to fail on local developers' machines due to missing GCP credentials. Catching the credential exceptions during local testing and allowing mock overrides resolved the issue.
- **Future Considerations**: Returning rich lookup objects (`DuplicateLookupResult`) instead of standard booleans makes logging the original processing `run_id` for duplicate audits straightforward.

---

## 8. Interview Talking Points

- **Q: Why did you split the Pub/Sub workflow into two separate topics?**
  - *Answer*: Downstream processing clusters (like Google Cloud Dataflow) charge for spin-up and CPU execution time. Triggering them on raw GCS uploads means duplicate files or incomplete writes would spin up clusters unnecessarily. The `ingestion-events` topic receives raw files, the Cloud Function runs a fast deduplication check, and only validated files publish to `processing-events` to trigger the Dataflow job.
- **Q: How did you ensure your serverless Cloud Function doesn't run out of memory when processing large store files?**
  - *Answer*: Standard `f.read()` loads the entire object into memory. We implemented chunk-based streaming reads (`blob.open("rb")` in 256KB chunks), feeding the stream directly into Python's `hashlib.sha256()`. This bounds memory usage to ~256KB regardless of whether the file is 1MB or 10GB.
- **Q: Why write custom SQL instead of utilizing a Python ORM in the Cloud Function?**
  - *Answer*: Standard ORMs like SQLAlchemy add significant package overhead, slow down cold start times, and are not natively optimized for BigQuery's column-oriented architecture. Raw parameterized SQL queries in BigQuery are faster and more lightweight.
