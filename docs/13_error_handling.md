# Error Handling & Bad Record Isolation Strategy

## Overview
Enterprise production pipelines must never crash abruptly due to localized raw data anomalies. RetailFlow ETL enforces a strict **Fault Isolation Architecture**:
- Structural file errors halt the individual file process safely.
- Data-level anomalies quarantine invalid records without losing clean sibling rows in the batch.

---

## Quarantine Directory Format
Quarantined records are written to `data/bad_records/` in structured JSON lines format alongside diagnostic failure reasons.

### Example Bad Record Output (`data/bad_records/sales_bad_20260724.json`):
```json
{
  "source_file": "store_012_sales_20260724.csv",
  "row_number": 412,
  "raw_record": {
    "transaction_id": "TX-994821",
    "store_id": "STR-012",
    "product_id": "PROD-881",
    "quantity": "-5",
    "unit_price": "29.99",
    "transaction_time": "2026-07-24 10:15:00"
  },
  "error_codes": [
    "VAL_NEG_QUANTITY"
  ],
  "error_messages": [
    "Quantity cannot be negative: -5"
  ],
  "quarantined_at": "2026-07-24T12:00:00Z"
}
```

---

## Error Taxonomy

| Error Code | Classification | Severity | System Action |
|---|---|---|---|
| `ERR_FILE_NOT_FOUND` | System IO | CRITICAL | Abort batch run, notify alert hook. |
| `ERR_HEADER_MISMATCH` | Schema | ERROR | Skip file, quarantine entire file, write to audit log. |
| `VAL_NULL_PRIMARY_KEY` | Data Quality | WARNING | Quarantine row to `bad_records`, continue processing batch. |
| `VAL_INVALID_DATATYPE` | Data Quality | WARNING | Quarantine row to `bad_records`, continue processing batch. |
| `VAL_NEG_QUANTITY` | Business Rule | WARNING | Quarantine row to `bad_records`, continue processing batch. |
| `VAL_FUTURE_TIMESTAMP` | Business Rule | WARNING | Quarantine row to `bad_records`, continue processing batch. |
| `VAL_FK_NOT_FOUND` | Integrity | WARNING | Quarantine row to `bad_records`, update dimension retry queue. |
| `ERR_DB_DEADLOCK` | Database | ERROR | Roll back transaction, retry 3 times with exponential backoff. |
