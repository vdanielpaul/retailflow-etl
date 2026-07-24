# Configuration Management Guide

## Configuration Architecture
RetailFlow ETL enforces strict separation between code and configuration. Pipeline execution parameters are driven by YAML files parsed into strongly-typed Pydantic settings models.

---

## Configuration Hierarchy
1. **Default Settings**: Base configuration defined in `config/config.example.yaml`.
2. **Environment Variables**: Overrides sensitive or environment-specific values (e.g., `POSTGRES_PASSWORD`, `POSTGRES_USER`, `LOG_LEVEL`).
3. **CLI Arguments**: Runtime parameters passed via command-line interface (e.g., `--file-path`, `--batch-size`).

---

## Environment Variable Resolution
The configuration loader automatically resolves environment variables declared using the `env_var:NAME` syntax inside configuration YAML files.

### Example YAML snippet:
```yaml
database:
  host: "localhost"
  port: 5432
  name: "retailflow_dw"
  user: "retailflow_user"
  password: "env_var:POSTGRES_PASSWORD"
```

---

## Complete Options Reference

| Section | Setting | Type | Description | Default |
|---|---|---|---|---|
| `pipeline` | `environment` | `string` | Environment target (`development`, `staging`, `production`) | `"development"` |
| `pipeline` | `batch_size` | `integer` | Database chunk insert size | `10000` |
| `pipeline` | `stop_on_error` | `boolean` | Terminate run if unrecoverable exception occurs | `false` |
| `database` | `host` | `string` | PostgreSQL server hostname | `"localhost"` |
| `database` | `port` | `integer` | PostgreSQL port | `5432` |
| `paths` | `input_dir` | `string` | Directory for raw store CSV drops | `"data/input"` |
| `paths` | `archive_dir` | `string` | Storage for historical processed CSVs | `"data/archive"` |
| `paths` | `bad_records_dir` | `string` | Destination for quarantined invalid rows | `"data/bad_records"` |
| `logging` | `level` | `string` | Log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `"INFO"` |
| `validation` | `reject_future_dates` | `boolean` | Flag transactions dated in the future as invalid | `true` |
