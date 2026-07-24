# Testing & Quality Assurance Guide

## Testing Strategy
RetailFlow ETL includes a automated `pytest` test suite covering unit, integration, and performance validation.

---

## Test Directory Layout

```
tests/
├── unit/
│   ├── test_config.py          # Configuration loading & validation
│   ├── test_validation.py      # Schema enforcement & row rules
│   ├── test_transformation.py  # Deduplication & SCD Type 1 mapping
│   ├── test_loader.py          # Database ingestion logic
│   └── test_audit.py           # Audit logger & row count metrics
└── integration/
    ├── test_full_pipeline.py   # End-to-end batch processing test
    └── test_db_transactions.py # Database rollback & error handling
```

---

## Running Automated Tests

```bash
# Run unit tests
pytest tests/unit

# Run full test suite with coverage report
pytest --cov=src/retailflow --cov-report=term-missing tests/

# Run static type checking
mypy src/

# Run linter and formatting checks
ruff check src/ tests/
```

---

## Testing Principles
1. **Isolated Data Fixtures**: Tests use in-memory synthetic CSV DataFrames and mock PostgreSQL database connections.
2. **Deterministic Quality Enforcement**: Explicit tests assert that invalid dates, negative amounts, and bad emails are properly quarantined.
3. **Idempotency Assertions**: Integration tests verify that re-processing identical source files results in 0 duplicate records in target warehouse tables.
