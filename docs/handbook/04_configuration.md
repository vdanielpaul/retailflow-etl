# Chapter 4: Configuration & PipelineContext

## 1. What Problem Does This Solve?
Hardcoding settings (database passwords, file directory paths, batch page sizes) inside source code is catastrophic in enterprise engineering. Changing a database password would require modifying code, re-testing, and deploying code.

Additionally, passing 10+ arguments (`db_conn`, `logger`, `config`, `run_id`, `source_file`, etc.) into every function creates messy function signatures ("parameter bloat").

---

## 2. Why Do We Need It?

### Configuration Management
Using externalized, layered YAML configuration files (`base.yaml` overridden by `development.yaml` or `production.yaml`) allows us to change pipeline behavior instantly per environment without touching Python code.

### Dependency Injection
Instead of classes instantiating their own database connections or loggers inside constructors, dependencies are created at the top level (`cli.py`) and passed into downstream components via constructors.

---

## 3. How Our Implementation Works

### 1. Configuration Inheritance Mechanism
```text
base.yaml (Global Defaults)
   └── development.yaml (Local Overrides)
   └── production.yaml (Production Credentials via Environment Variables)
```

`load_config()` loads `base.yaml` first, then merges environment overrides. Values starting with `env_var:POSTGRES_PASSWORD` are automatically resolved at runtime from OS environment variables.

### 2. PipelineContext Container (Explained Like You're 5)
Imagine a backpack that a hiker carries up a mountain. Instead of holding a water bottle in your right hand, a map in your left hand, compass in your pocket, and flashlight under your arm, you put everything into **one backpack**.

`PipelineContext` is that backpack for our pipeline:

```python
class PipelineContext:
    run_id: str             # Unique execution ID (e.g. "run-20260724-100000")
    batch_id: str           # Batch identifier
    environment: str        # "development" | "production" | "testing"
    configuration: Settings # Loaded settings object
    database: DatabaseManager # Database connection manager
    logger: Logger          # Structured JSON logger
    source_file: Path       # Target CSV feed file
```

Whenever any stage (Validation, Transformation, Loading) needs to run, it simply receives the single `context` backpack!

---

## 4. How to Explain This in an Interview

> *"We implement a configuration-driven architecture using layered YAML files with environment variable interpolation for secret management. We eliminate parameter bloat by using Dependency Injection and a unified `PipelineContext` container that encapsulates run metadata, logger instances, database connection pools, and environment settings."*
