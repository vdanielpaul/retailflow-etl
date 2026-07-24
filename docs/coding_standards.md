# RetailFlow ETL Coding Standards & Guidelines

## 1. Naming Conventions

### 1.1 File & Module Naming
- Use `snake_case` for all Python files: `user_repository.py`, `sales_transformer.py`.
- Module names must be clear and descriptive; avoid ambiguous abbreviations (e.g. use `sales_transformer.py`, not `sls_trsf.py`).

### 1.2 Class Naming
- Use `PascalCase` for all classes: `SalesTransformer`, `PostgreSQLConnectionPool`, `PipelineOrchestrator`.
- Custom Exception classes must end with `Error`: `ValidationError`, `DatabaseConnectionError`.

### 1.3 Function & Variable Naming
- Use `snake_case` for functions, methods, and variables: `calculate_net_sales()`, `quarantine_records()`.
- Module-level constants must use `SCREAMING_SNAKE_CASE`: `DEFAULT_BATCH_SIZE = 10000`, `MAX_RETRY_COUNT = 3`.

---

## 2. Import Ordering Standard
All imports must be grouped into three distinct blocks separated by single blank lines (enforced via `ruff` / `isort` rules):
1. **Standard Library Imports**: `os`, `sys`, `typing`, `pathlib`, `logging`.
2. **Third-Party Library Imports**: `pandas`, `psycopg2`, `yaml`, `pydantic`.
3. **Local Application Imports**: `from retailflow.config import Settings`, `from retailflow.exceptions import ValidationError`.

*Always prefer absolute imports over relative imports:*
```python
# Preferred
from retailflow.utils.logger import get_logger

# Avoid
from ..utils.logger import get_logger
```

---

## 3. Logging Standards
- **Never use `print()` statements** in production code. All operational messages must use Python `logging`.
- Obtain loggers via module name: `logger = logging.getLogger(__name__)`.
- Log entries must include contextual key-value pairs where applicable:
```python
logger.info("Validated batch file", extra={"file_name": file_path.name, "rows_read": total_rows})
```

---

## 4. Exception Handling Standards
- Catch specific, expected exceptions rather than generic `except Exception:`.
- Reraise custom domain exceptions defined in `retailflow.exceptions` with clear error messages.
- Always log exception tracebacks at `ERROR` or `CRITICAL` log levels before escalating or quarantining.

---

## 5. Documentation Standards
- Every public module, class, and function must include Google-style Python docstrings.
- Docstrings must specify `Args`, `Returns`, and `Raises`:
```python
def transform_sales_records(df: pd.DataFrame, store_id: str) -> pd.DataFrame:
    """Standardize raw sales feed and compute calculated fields.

    Args:
        df: Raw validated Pandas DataFrame for the store batch.
        store_id: Natural key identifier of the store location.

    Returns:
        Transformed DataFrame enriched with calculated net sales metrics.

    Raises:
        TransformationError: If required calculation columns are missing.
    """
    ...
```

---

## 6. SQL Formatting Guidelines
- SQL keywords must be uppercase (`SELECT`, `INSERT INTO`, `WHERE`, `ON CONFLICT DO UPDATE`).
- Table names and column names must be lowercase `snake_case` (`fact_sales`, `customer_sk`).
- DDL scripts must explicitly state primary keys, foreign key constraints, and nullability rules.
