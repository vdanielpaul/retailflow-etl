# Chapter 17: Lessons Learned & Architectural Trade-Offs

## 1. Executive Summary
Building production software requires making explicit architectural trade-offs. Perfect architecture does not exist; every engineering decision trades off complexity, performance, development velocity, and operational overhead.

---

## 2. Key Trade-Off Evaluations

### Trade-Off 1: In-Memory Surrogate Key Resolution vs Database Queries
- **Chosen Option**: Pre-load dimension keys into Python dictionaries at pipeline startup.
- **Advantage**: Reduces key lookup latency from O(N network queries) to O(1) in-memory lookups, boosting throughput to **>25,000 rows/sec**.
- **Disadvantage**: Requires RAM memory. If dimension tables grow to 50 million rows, lookup caches could exceed worker node memory limits.
- **v2 Resolution**: Use Redis distributed cache or SQL JOINs inside staging tables for multi-million row dimensions.

### Trade-Off 2: Single-Transaction Loading Scope vs Concurrency
- **Chosen Option**: Wrap all database writes (dimensions, facts, watermarks, audit logs) inside a single `BEGIN ... COMMIT` block.
- **Advantage**: Guarantees 100% all-or-nothing atomicity with zero orphan records or partial data corruption.
- **Disadvantage**: Holds exclusive table locks during loading, which could block concurrent queries if batch sizes are extremely large.

### Trade-Off 3: SCD Type 1 vs SCD Type 2
- **Chosen Option**: Overwrite dimension attributes in-place (SCD Type 1).
- **Advantage**: Keeps dimension schemas compact, simplifies SQL JOINs, and fulfills current-state reporting requirements.
- **Disadvantage**: Does not maintain historical versions if a store changes regions or a product changes categories.

---

## 3. What We Would Change in Version 2.0
1. **Asynchronous Telemetry Publishing**: Move telemetry event dispatching (`AuditService`) to background worker threads to prevent slow APM endpoints from adding latency to the main execution thread.
2. **Dynamic Range Partition Creation**: Automate PostgreSQL SQL partition creation (`fact_sales_yYYYYmMM`) ahead of time via a scheduled maintenance cron script.

---

## 4. How to Explain This in an Interview

> *"Our design choices reflect deliberate trade-offs: we prioritized sub-second surrogate key lookup speed via in-memory caching, 100% database write atomicity via single-transaction scoping, and simple current-state reporting using SCD Type 1 dimensions. In v2, we would introduce asynchronous audit publishing and dynamic partition maintenance."*
