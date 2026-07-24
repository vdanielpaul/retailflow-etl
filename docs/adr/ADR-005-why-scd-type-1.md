# ADR-005: Adoption of SCD Type 1 for Dimension Management

## Status
Accepted

## Context
Attributes within dimension tables change over time (e.g., a customer updates their email address, a store changes manager names, or a product price is updated). We needed to define a Slowly Changing Dimension (SCD) strategy.

## Decision
We implemented **SCD Type 1 (Overwrite)** for dimension entity maintenance across `dim_customer`, `dim_product`, `dim_store`, and `dim_employee`.

## Alternatives Considered
1. **SCD Type 2 (Historical Tracking with Version Flags)**:
   - *Pros*: Full point-in-time historical audit tracking (`effective_date`, `expiration_date`, `is_current`).
   - *Cons*: Increased join complexity in fact tables, larger storage footprint, extra surrogate key matching logic for POS batch feeds that lack point-in-time event timestamps.
2. **SCD Type 3 (Previous Column Tracking)**:
   - *Pros*: Stores current and previous value side-by-side.
   - *Cons*: Limited to tracking only one historical change.

## Consequences
- **Positive**: Simple SQL upsert operations (`INSERT ... ON CONFLICT DO UPDATE`), low storage overhead, deterministic surrogate key resolution.
- **Negative**: Historical attribute state prior to the update is not preserved in the dimension table.
