# Chapter 19: Visual Learning & System Architecture Diagrams

This chapter consolidates all architectural sequence and flow diagrams across RetailFlow ETL.

---

## 1. Overall System Architecture

```mermaid
flowchart TD
    StoreCSV[Nightly Store POS CSV Feeds] --> IncCheck{Incremental Change Detector}
    IncCheck -- DUPLICATE --> Skip[Skip Ingestion / SKIPPED Manifest]
    IncCheck -- NEW / REPROCESS --> ValEngine[Data Quality Validation Engine]

    ValEngine -- Invalid Rows --> Quarantine[Per-Run Quarantine: data/bad_records/run_id/]
    ValEngine -- Valid Rows --> Scorecard[Data Quality Scorecard: 0-100%]
    ValEngine -- Valid Rows --> CDM[Canonical Data Model: CanonicalSale]

    CDM --> Cleaner[Data Cleaner: Whitespace & Unicode Cleanup]
    Cleaner --> Normalizer[Data Normalizer: Email & SKU Normalization]
    Normalizer --> Enricher[Financial Metrics Enricher]
    Enricher --> SurrogateLookup[In-Memory Surrogate Key Resolver]
    SurrogateLookup --> SCD1[SCD Type 1 Processor]

    SCD1 --> FactBuilder[Fact Table Payload Builder]
    FactBuilder --> Loader[PostgreSQL Bulk Loader: COPY / execute_values]

    Loader --> DW[(PostgreSQL Star Schema DW)]
    Loader --> Watermark[Register Watermark & Audit Logs]
    Loader --> Manifest[Write Manifest: data/processed/run_id/manifest.json]
```

---

## 2. Validation & Quarantine Subsystem

```mermaid
flowchart LR
    Raw[Raw Feed DataFrame] --> FileVal[File & Schema Validator]
    FileVal --> TypeVal[Data Type Coercion Validator]
    TypeVal --> RuleVal[Business Rule Validator]
    RuleVal --> DupVal[Duplicate Key Validator]

    DupVal --> Split{Split Rows}
    Split -- Clean Rows --> CleanDF[Clean DataFrame -> Ingestion]
    Split -- Invalid Rows --> BadCSV[Quarantine Writer: bad_records/run_id/invalid_rows.csv]
```

---

## 3. High-Performance Bulk Load Transaction Scope

```mermaid
sequenceDiagram
    participant App as WarehouseLoaderEngine
    participant Tx as TransactionCoordinator
    participant DB as PostgreSQL Database

    App->>Tx: atomic_transaction()
    Tx->>DB: BEGIN TRANSACTION
    App->>DB: Upsert Dimensions (SCD Type 1)
    App->>DB: COPY / execute_values (fact_sales)
    alt Failure Occurs
        App->>Tx: Exception Raised
        Tx->>DB: ROLLBACK
        Note over DB: All changes discarded!
    else Success
        App->>DB: Register Watermark & Audit Log
        Tx->>DB: COMMIT
        Note over DB: Changes persisted atomically!
    end
```

---

## 4. Operational Telemetry & Audit Dispatch

```mermaid
flowchart TD
    Stage[Pipeline Execution Stages] --> AuditSvc[AuditService]
    AuditSvc --> Event[Instantiate AuditEvent]

    Event --> PubConsole[ConsolePublisher]
    Event --> PubProm[PrometheusPublisherStub]
    Event --> PubAlert[AlertPublisherStub: Slack / Teams]

    Event --> Repo[AuditRepository]
    Repo --> DB[(metadata.etl_audit_log Table)]
```

---

## 5. Warehouse Star Schema ERD

```mermaid
erDiagram
    dim_date ||--o{ fact_sales : "date_sk"
    dim_store ||--o{ fact_sales : "store_sk"
    dim_product ||--o{ fact_sales : "product_sk"
    dim_customer ||--o{ fact_sales : "customer_sk"
    dim_employee ||--o{ fact_sales : "employee_sk"

    fact_sales {
        bigint sales_sk PK
        integer date_sk FK
        integer store_sk FK
        integer product_sk FK
        integer customer_sk FK
        integer employee_sk FK
        varchar transaction_id
        numeric net_sales_amount
        integer quantity
    }
```
