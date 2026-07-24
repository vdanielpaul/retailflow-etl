# ADR-001: Selection of Pandas over PySpark for Core Batch Transformation Engine

## Status
Accepted

## Context
RetailFlow ETL processes nightly sales CSV feeds from 250+ retail store locations. The target batch volume is approximately 250,000 to 1,000,000 transaction records per night (~100 MB to 500 MB uncompressed CSV data). We needed to select a core data processing framework for schema validation, data cleaning, and transformation logic.

## Decision
We chose **Pandas** (version 2.2+) running on single-node execution over distributed Apache Spark (PySpark).

## Alternatives Considered
1. **PySpark (Apache Spark)**: Distributed in-memory data processing engine.
   - *Pros*: Unlimited horizontal scalability across compute clusters; native distributed dataframe operations.
   - *Cons*: High architectural overhead, JVM dependency, cluster resource configuration cost, latency overhead for smaller batch datasets (< 10 GB), complex local testing setup.
2. **Polars**: Fast Rust-backed DataFrame library.
   - *Pros*: Multithreaded execution, low memory footprint.
   - *Cons*: Smaller enterprise ecosystem adoption for legacy POS database integration compared to Pandas.
3. **Pure Python (dicts/tuples)**:
   - *Pros*: Standard library only.
   - *Cons*: High execution time and verbose code for vectorized data transformations.

## Consequences
- **Positive**: Low infrastructure complexity, zero JVM requirement, fast local development, seamless integration with `psycopg2` and SQL execution models, rich ecosystem for data validation.
- **Negative**: Constrained to single-node memory capacity. Datasets exceeding single-host RAM (e.g., > 10 GB per batch) will require chunked processing or future migration to PySpark.
