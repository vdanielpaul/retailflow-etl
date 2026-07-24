# ADR-007: Fault Isolation & Bad Record Quarantine Strategy

## Status
Accepted

## Context
Nightly raw POS exports often contain corrupted rows, missing customer IDs, negative sale amounts, or invalid emails. Aborting an entire batch execution when encountering a single invalid row delays analytical access to thousands of valid transaction records.

## Decision
We implemented a **Fault Isolation Quarantine Strategy**. Bad records are quarantined to `data/bad_records/{filename}_bad_{timestamp}.json` with error diagnostic metadata, allowing valid records within the batch feed to process seamlessly.

## Alternatives Considered
1. **Fail-Fast (Abort Execution on First Error)**:
   - *Pros*: Guarantees zero unhandled edge cases enter pipeline logic.
   - *Cons*: Single malformed line halts data loading for all 250 stores.
2. **Silent Drop (Ignore Bad Records)**:
   - *Pros*: Pipeline execution completes without interruption.
   - *Cons*: Unauditable data loss; zero visibility into store POS export issues.

## Consequences
- **Positive**: High operational availability, clean warehouse state, transparent error debugging metadata for data quality teams.
- **Negative**: Requires validation engine overhead and post-processing quarantine maintenance procedures.
