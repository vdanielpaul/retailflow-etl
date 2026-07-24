# Lessons Learned & Engineering Best Practices

## Retrospective Findings

### 1. Data Type Coercion Edge Cases
- **Challenge**: POS feeds intermittently formatted numeric prices with currency symbols (`$12.99`) or empty string placeholders (`""`).
- **Solution**: Early normalization in the validation phase strips monetary formatting characters before attempting float/decimal conversion.

### 2. Idempotent Ingestion Requirements
- **Challenge**: Re-running the pipeline on input directories containing already ingested files led to duplicate primary key errors in staging.
- **Solution**: Implemented SHA-256 file hashing stored in `etl_audit_log` to check file hashes prior to ingestion, guaranteeing 100% idempotent execution.

### 3. Pydantic Configuration Validation
- **Challenge**: Missing environment variables or malformed YAML paths caused runtime errors midway through batch execution.
- **Solution**: Enforced strict startup validation using Pydantic settings models, ensuring invalid configurations fail immediately during initialization before touching data files.
