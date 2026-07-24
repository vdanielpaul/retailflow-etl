# Directory & Package Architecture

## Detailed Enterprise Project Structure

```
retailflow-etl/
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI workflow
├── docs/                      # Technical documentation
│   ├── adr/                   # Architecture Decision Records (ADR-001 ... ADR-007)
│   ├── images/                # Architecture diagrams & screenshots
│   ├── 01_architecture.md
│   ├── 02_project_overview.md
│   ├── 03_folder_structure.md
│   ├── 04_pipeline_flow.md
│   ├── 05_warehouse_design.md
│   ├── 06_configuration_guide.md
│   ├── 07_logging_guide.md
│   ├── 08_testing_guide.md
│   ├── 09_deployment_guide.md
│   ├── 10_developer_guide.md
│   ├── 11_sql_scripts_guide.md
│   ├── 12_data_dictionary.md
│   ├── 13_error_handling.md
│   ├── 14_future_improvements.md
│   ├── 15_interview_questions.md
│   ├── 16_design_decisions.md
│   ├── 17_lessons_learned.md
│   ├── coding_standards.md    # Code style & documentation guidelines
│   └── pipeline_lifecycle.md  # Detailed execution blueprint
├── src/                       # Production Python package
│   └── retailflow/
│       ├── __init__.py
│       ├── config/            # YAML configuration loader & validation schemas
│       ├── constants/         # Application constants, error codes, defaults
│       ├── database/          # Connection manager, transactions, repositories
│       ├── exceptions/        # Domain exception hierarchy
│       ├── loader/            # Bulk PostgreSQL database ingestion
│       ├── models/            # Pydantic schemas, DTOs, data quality models
│       ├── pipeline/          # Orchestrator, stage execution & runner
│       ├── transformation/    # Cleaning, deduplication, surrogate mapping (SCD 1)
│       ├── utils/             # Logging, IO helpers, database utilities
│       ├── validation/        # Schema enforcement & row validation rules
│       └── audit/             # Operational audit logging & metric tracking
├── config/                    # Multi-environment configuration templates
│   ├── base.yaml              # Global default settings
│   ├── development.yaml       # Development overrides
│   ├── production.yaml        # Production overrides
│   └── config.example.yaml    # Reference template
├── data/                      # Multi-stage data lifecycle directories
│   ├── sample/                # Synthetic test input samples
│   ├── raw/                   # Incoming raw store CSV drops
│   ├── staging/               # Validated staging files
│   ├── processed/             # Transformed warehouse-ready files
│   ├── archive/               # Timestamped historical archive
│   └── bad_records/           # Quarantined malformed rows & JSON failure logs
├── logs/                      # Centralized application logs
├── sql/                       # PostgreSQL database scripts
│   ├── ddl/                   # Star Schema tables, indexes, constraints, views
│   └── dml/                   # Seed data & analytics queries
├── tests/                     # Automated unit and integration test suite
│   ├── unit/                  # Modular component unit tests
│   └── integration/           # End-to-end pipeline execution tests
├── scripts/                   # CLI helpers, seed generators, deployment scripts
├── CHANGELOG.md               # Keep a Changelog standard release history
├── Makefile                   # Cross-platform developer command runner
├── VERSION                    # Plaintext version tracking (0.1.0)
├── requirements.txt           # Production dependency specifications
├── pyproject.toml             # Package build, ruff, mypy, & pytest configuration
└── README.md                  # Main repository README
```

---

## Submodule Domain Responsibilities

| Submodule | Responsibilities |
|---|---|
| `retailflow/models/` | Pydantic data schemas, DataFrame DTO models, data quality rule representations. |
| `retailflow/database/` | Database connection pooling (`psycopg2`), transaction contexts, repository classes. |
| `retailflow/pipeline/` | ETL orchestrator engine, stage control, pipeline runner. |
| `retailflow/exceptions/` | Custom error classes (`RetailFlowError`, `ValidationError`, `DatabaseError`, `ConfigError`). |
| `retailflow/constants/` | Status enums (`PipelineStatus`), default paths, validation error codes. |
| `retailflow/config/` | Hierarchical configuration parser loading base + env overrides. |
| `retailflow/validation/` | File header checking, data type enforcement, business rule validation. |
| `retailflow/transformation/` | String cleaning, deduplication, SCD Type 1 surrogate key resolution. |
| `retailflow/loader/` | Batch ingestion to PostgreSQL tables (`dim_*`, `fact_sales`). |
| `retailflow/audit/` | Operations tracking, execution runtime metrics, `etl_audit_log` records. |
