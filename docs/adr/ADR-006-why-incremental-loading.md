# ADR-006: Incremental Loading & Idempotency Strategy

## Status
Accepted

## Context
Nightly retail feeds arrive incrementally per store. Re-processing all historical data every night is computationally expensive and inefficient. Furthermore, network drops or retries might deliver duplicate CSV feed files to `data/raw/`.

## Decision
We implemented a **Watermark & SHA-256 Hash Incremental Loading Strategy**.
1. Compute SHA-256 hash for every raw CSV feed and check against `etl_audit_log` before ingestion.
2. Maintain a watermark table (`etl_watermark`) tracking the maximum `transaction_time` and batch run state per store location.

## Alternatives Considered
1. **Full Refresh / Truncate and Reload**:
   - *Pros*: Extremely simple pipeline logic.
   - *Cons*: O(N) runtime scaling with cumulative store sales growth; unacceptable ingestion windows for 250+ stores.
2. **Database Change Data Capture (CDC)**:
   - *Pros*: Sub-second stream propagation.
   - *Cons*: Demands direct database access to 250+ store POS databases rather than CSV file exports.

## Consequences
- **Positive**: Low pipeline execution runtime, 100% idempotent re-run capabilities, minimal storage write overhead.
- **Negative**: Requires maintaining audit table logs and watermark state.
