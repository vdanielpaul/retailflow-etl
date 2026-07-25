# RetailFlow ETL v2.0 — Engineering Development Standards

This document establishes the official development standards, code styles, and testing requirements for the RetailFlow ETL v2.0 modernization.

---

## 1. Repository Strategy

### Branching Strategy
- **`main` Branch**: Production-ready code. Releases are tagged (`v2.0.0`, etc.) from this branch.
- **`develop` Branch**: Main integration branch. All feature branches branch off `develop`.
- **Feature Branches**: Named `feature/milestone-<number>-<description>` (e.g. `feature/milestone-1-infra`). Developed in isolation and merged to `develop` via pull requests.

### Pull Requests & Merge Policy
- All PRs require:
  - 100% pass rate on unit and integration tests.
  - Verification logs or screenshots attached.
  - Zero linter errors and successful code compilation.
- **Merge Policy**: Squashed commits to keep a clean history.

### Versioning
Adhere to Semantic Versioning (`MAJOR.MINOR.PATCH`):
- Increment `MAJOR` for incompatible API changes.
- Increment `MINOR` for backwards-compatible feature additions (like new milestones).
- Increment `PATCH` for backwards-compatible bug fixes.

---

## 2. Python Standards

### Typing
- Explicit type annotations are **mandatory** for all function signatures and class definitions.
- For Python 3.9 compatibility, use `Optional[T]` and `Union[T, U]` from the `typing` module instead of `T | U`.

### Docstrings
All classes, modules, and public methods must include Google-style docstrings:
```python
def clean_value(value: str) -> str:
    """Trim whitespace and clean non-printable characters.

    Args:
        value: Input raw string.

    Returns:
        Cleaned and formatted output string.
    """
```

### Naming Conventions
- Variables, functions, and modules: `snake_case`.
- Classes: `PascalCase`.
- Constants: `UPPER_SNAKE_CASE`.

### Exceptions
- Standardize on the custom domain exception hierarchy (`src/retailflow/exceptions/exceptions.py`).
- Catch targeted exceptions rather than writing generic `except Exception:` blocks.

### Logging
- Use the structured JSON logger.
- Automatically redact passwords, database connection strings, and access tokens using the `SensitiveDataFilter`.

### Data Models
- Use **Pydantic v2** for external schemas and data serialization (Canonical Data Models).
- Use native Python **dataclasses** for local, internal data structures.

### Dependency Injection
- Major components must receive dependencies via constructors (`PipelineContext`) rather than instantiating them internally.

---

## 3. Testing Standards

### Coverage Expectations
- Unit and integration code coverage must exceed **90%**.
- Test files must be named `test_<module>.py` and live under the `tests/` directory mirroring the source code structure.

### Mocking Guidelines
- Mock database connections and storage APIs using `unittest.mock`.
- Never run tests against real production GCS buckets or BigQuery datasets.

### Apache Beam DirectRunner Tests
- Use Beam's `TestPipeline` to verify pipeline transforms locally without Cloud Dataflow overhead.

---

## 4. Terraform Standards

### Structure & Layout
Organize Terraform code into clean, single-responsibility files under the `deploy/` directory:
- `main.tf` (Providers, backend)
- `gcs.tf` (Storage resources)
- `bigquery.tf` (BigQuery datasets and schemas)
- `variables.tf` (Input definitions)
- `outputs.tf` (Resource metadata outputs)

### Variable Naming
- Use clear names: `var.project_id`, `var.region`, `var.environment`.
- Always provide a default description for variables.

### State Management
- Storing state files locally during development is allowed, but must be configured to use a GCS remote backend (`gcs` backend) in staging/production.

---

## 5. BigQuery Standards

### Dataset Naming
- Use the environment suffix: `retailflow_bronze_dev`, `retailflow_silver_dev`, `retailflow_gold_dev`.

### Table & Column Naming
- Tables: `snake_case` (e.g. `fact_sales`).
- Columns: `snake_case` (e.g. `transaction_time`).
- Join keys must use `_sk` suffix (e.g. `store_sk`, `product_sk`).

### SQL Style & MERGE Conventions
- Always write SQL keywords in UPPERCASE (`SELECT`, `JOIN`, `MERGE`, `ON`).
- Explicitly partition the `fact_sales` table by day and cluster on surrogate keys.

---

## 6. Cloud Standards

### Service Accounts & Least Privilege
- Service accounts must only have the minimal IAM roles needed for execution.
- Never use the owner/editor service account role for Cloud Functions or Dataflow workers.

### Secrets Handling
- Credentials and database tokens must be stored in Google Cloud Secret Manager. Cloud Functions resolve secrets at runtime using Secret Manager API queries.

---

## 7. Code Review Checklist

Before approving any PR, reviewers must check:
- [ ] **Architecture**: Does it align with the v2.0 Architecture Baseline?
- [ ] **Modularity**: Is the code modular and testable?
- [ ] **Testing**: Do all unit/integration tests pass and exceed 90% coverage?
- [ ] **Typing**: Are type annotations complete and valid?
- [ ] **Security**: Are passwords and secrets redacted from logs and configurations?
- [ ] **Performance**: Are database updates atomic and vectorized?

---

## 8. Definition of Done (DoD)

A milestone or feature is complete only when:
1. All code implementation is finished and clean.
2. All unit and integration tests pass successfully.
3. Code coverage exceeds 90%.
4. Static analysis checks (`ruff check`, `mypy`) pass with zero errors.
5. Terraform infrastructure compiles and runs without warnings.
6. Documentation, runbooks, and repositories layout are updated.
7. Verification checklists are completed and validated.
