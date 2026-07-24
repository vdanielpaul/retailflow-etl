# Developer Guide & Contribution Standards

## Coding Standards & Environment Rules

### 1. Code Style & Tooling
- Follow **PEP 8** style guidelines enforced by `ruff`.
- Maintain strict type annotations (`mypy`).
- Line length: 120 characters.

### 2. Mandatory Documentation
- Every public function, class, and module must contain Google-style docstrings.
- Docstrings must specify `Args`, `Returns`, and `Raises` exceptions.

```python
def validate_email_address(email: str) -> bool:
    """Validate email string format against standard RFC regex.

    Args:
        email: The raw email address string to evaluate.

    Returns:
        True if the email matches valid format rules, False otherwise.
    """
    ...
```

---

## Local Development Workflow

```bash
# 1. Format & Lint
ruff format .
ruff check --fix .

# 2. Type Check
mypy src/

# 3. Run Unit Tests
pytest
```
