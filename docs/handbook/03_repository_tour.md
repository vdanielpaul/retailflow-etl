# Chapter 3: Repository Tour

## 1. What Problem Does This Solve?
Unstructured codebases quickly turn into "spaghetti code." When files are scattered randomly, developers cannot locate where business rules are enforced, bug fixes introduce unintended side effects, and adding new features becomes extremely risky.

A clear, standardized enterprise directory layout ensures that every folder has a single responsibility.

---

## 2. Why Do We Need It?
Separation of Concerns (SoC) is a core software engineering principle. By separating configuration, validation, transformation, loading, database connections, and operational auditing into dedicated subpackages, we ensure:
1. Low coupling: Changing database connection pooling does not affect validation logic.
2. High cohesion: All code related to validation lives together under `src/retailflow/validation/`.
3. Testability: Each module can be unit-tested in isolation using mock objects.

---

## 3. How Our Implementation Works

```text
retailflow-etl/
├── config/                  # Environment-specific YAML configuration profiles
├── data/                    # Local storage staging lifecycle (raw, processed, bad_records)
├── docs/                    # Architectural decision records, guides, and handbook
│   ├── adr/                 # Architecture Decision Records (ADR-001 to ADR-007)
│   └── handbook/            # Complete 20-Chapter Developer Handbook
├── sample_data/             # Reusable sample datasets (small, medium, invalid, duplicates)
├── sql/                     # PostgreSQL DDL & DML scripts (warehouse & metadata schemas)
├── src/retailflow/          # Primary Python package code
│   ├── audit/               # Operational audit subsystem, timeline engine, publishers
│   ├── config/              # Layered YAML configuration loader & semantic validator
│   ├── constants/           # Global constants, error codes, stage enums
│   ├── database/            # Connection pool manager & transaction coordinator
│   ├── exceptions/          # Domain-specific exception hierarchy
│   ├── health/              # Pre-flight environment & health checker
│   ├── incremental/         # Watermark manager, SHA-256 change detector, state checkpoints
│   ├── loader/              # Bulk COPY engine, dimension loader, fact loader, transactions
│   ├── metrics/             # Performance metrics collector & stage timer
│   ├── models/              # Canonical Data Model (CDM), validation & load DTOs
│   ├── pipeline/            # PipelineContext container & state context
│   ├── transformation/      # Cleaner, normalizer, enricher, surrogate resolver, SCD1
│   ├── utils/               # Structured JSON logger & sensitive data redactor
│   ├── validation/          # Modular data quality validators & scorecard calculator
│   └── cli.py               # Operational Command-Line Interface runner
├── tests/                   # Complete test suite (unit/, integration/, e2e/, harness/)
├── benchmarks/              # Performance throughput & memory profiling benchmarks
├── pyproject.toml           # Project dependencies & linter config
├── requirements.txt         # Production dependency pins
└── README.md                # Open-source project entry point
```

---

## 4. Detailed Folder Matrix

| Folder | Primary Purpose | Key File Examples | Inter-Module Dependencies |
|---|---|---|---|
| `config/` | Environment YAML config profiles | `base.yaml`, `dev.yaml`, `prod.yaml` | Consumed by `src/retailflow/config/` |
| `sql/` | DDL schemas & seed SQL scripts | `ddl/01_create_warehouse_schema.sql` | Executed against PostgreSQL database |
| `src/retailflow/models/` | Data Transfer Objects (DTOs) & CDM | `canonical.py`, `validation.py` | Imported by validation, transformation, loader |
| `src/retailflow/validation/` | Data Quality Rules & Quarantine | `engine.py`, `validators.py` | Uses `models/canonical.py`, exports bad rows |
| `src/retailflow/transformation/`| Data Cleaning & Key Resolution | `cleaner.py`, `surrogate_keys.py` | Consumes clean DataFrame from validation |
| `src/retailflow/loader/` | High-Speed Warehouse Bulk Ingestion | `bulk.py`, `fact_loader.py` | Interacts with `database/connection.py` |
| `src/retailflow/incremental/` | Watermarking & Replay Framework | `watermark.py`, `change_detection.py` | Interacts with `metadata.etl_watermark` |
| `src/retailflow/audit/` | Observability & Timeline Engine | `service.py`, `repository.py` | Emits lifecycle events across all stages |

---

## 5. How to Explain This in an Interview

> *"Our repository strictly follows enterprise Separation of Concerns. Core application logic lives under `src/retailflow/` divided into domain subpackages (`config`, `database`, `validation`, `transformation`, `loader`, `incremental`, `audit`). Data Transfer Objects and Canonical Models are centralized under `models/`, ensuring zero circular dependencies."*
