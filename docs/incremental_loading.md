# Incremental Processing, Watermarking & Replay Engineering Guide

## Overview
This engineering runbook details the incremental processing subsystem of RetailFlow ETL. It explains change classification, high-watermark updates, manual replay protocols, state checkpoint recovery, and execution manifest auditing.

---

## 1. Execution Sequence Diagrams

### Normal Incremental Execution Flow

```mermaid
sequenceDiagram
    autonumber
    participant Feed as CSV Feed File
    participant IncEngine as IncrementalEngine
    participant WM as WatermarkManager
    participant Pipeline as ETL Pipeline
    participant DB as PostgreSQL DW

    Feed->>IncEngine: Evaluate incoming file
    IncEngine->>WM: Check SHA-256 file hash status
    WM-->>IncEngine: File is NEW
    IncEngine->>Pipeline: Execute Validation & Transformation
    Pipeline->>DB: Atomic Load (Dimensions + Facts)
    DB-->>Pipeline: Load Success
    Pipeline->>WM: Register Watermark & File Hash
    Pipeline->>IncEngine: Write manifest.json
```

### Duplicate Detection & Safe Skip Flow

```mermaid
sequenceDiagram
    autonumber
    participant Feed as Duplicate CSV Feed
    participant IncEngine as IncrementalEngine
    participant WM as WatermarkManager

    Feed->>IncEngine: Evaluate incoming file
    IncEngine->>WM: Check SHA-256 file hash status
    WM-->>IncEngine: File Hash Status = SUCCESS (DUPLICATE)
    IncEngine->>IncEngine: Set Classification = DUPLICATE
    IncEngine->>IncEngine: Write SKIPPED manifest.json
    IncEngine-->>Feed: Safely terminate run without DB writes
```

### Manual Replay Flow

```mermaid
sequenceDiagram
    autonumber
    participant Operator as DevOps / Data Engineer
    participant IncEngine as IncrementalEngine
    participant Pipeline as ETL Pipeline
    participant DB as PostgreSQL DW

    Operator->>IncEngine: Trigger Replay (--replay <run_id> / --file-hash <hash>)
    IncEngine->>IncEngine: Set Classification = REPROCESS
    IncEngine->>Pipeline: Force Full Pipeline Processing
    Pipeline->>DB: Upsert / Re-ingest Data
    Pipeline->>IncEngine: Write REPROCESSED manifest.json
```

### Partial Failure Checkpoint Recovery Flow

```mermaid
sequenceDiagram
    autonumber
    participant Pipeline as ETL Pipeline
    participant State as StateManager
    participant DB as PostgreSQL DW

    Pipeline->>State: Save Checkpoint: VALIDATION_PASSED
    Pipeline->>State: Save Checkpoint: TRANSFORMATION_PASSED
    Pipeline->>DB: Execute Fact Load (FAILS)
    DB-->>Pipeline: DB Disconnection Exception
    Pipeline->>State: Save Checkpoint: FACT_LOAD_FAILED
    Note over Pipeline,State: Operator restarts pipeline with run_id
    State->>Pipeline: Resume execution from TRANSFORMATION_PASSED checkpoint
```

---

## 2. Change Classification Reference

| Classification | Trigger Condition | Pipeline Action |
|---|---|---|
| **`NEW`** | File SHA-256 hash missing from `metadata.etl_watermark` | Complete validation, transformation, and warehouse load |
| **`DUPLICATE`** | File SHA-256 hash already exists with status `SUCCESS` | Log warning, generate `SKIPPED` manifest, terminate cleanly |
| **`MODIFIED`** | Filename identical, but SHA-256 content hash changed | Process as fresh feed, update watermark |
| **`STALE`** | Feed file timestamp older than configured window | Ignore feed, log operational warning |
| **`REPROCESS`** | Operator explicitly supplied `--replay` flag | Override watermark check, re-run full pipeline |
