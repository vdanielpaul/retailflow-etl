# Chapter 13: Performance Optimization & Benchmarking

## 1. What Problem Does This Solve?
Slow pipelines waste cloud computing resources, delay business reporting, and miss Nightly Service Level Agreements (SLAs). If nightly batch processing takes 9 hours to run, morning executive dashboards won't be ready when business operations open at 8:00 AM.

---

## 2. Why Do We Need It?
Performance optimization in Python requires understanding memory bounds, CPU vectorization, and database I/O bottlenecks:
1. Avoid slow Python `for` loops (`df.iterrows()`).
2. Eliminate unnecessary database network round-trips.
3. Stream bulk data directly into database engine memory buffers.

---

## 3. How Our Implementation Works (`benchmarks/run_benchmarks.py`)

### 1. Vectorized Pandas vs Python Loops
Python `for` loops execute interpretively row-by-row. Vectorized Pandas operations (`pd.to_numeric`, `df['qty'] > 0`, string masking) execute in optimized C code under CPython, processing 100,000 rows in milliseconds.

### 2. In-Memory Dimension Lookup Caching
Instead of querying PostgreSQL for every row to resolve surrogate keys (`SELECT store_sk FROM dim_store WHERE store_id = 'STR-001'`), `SurrogateKeyResolver` pre-loads natural keys into Python dictionaries at startup.
- *Performance Gain*: Reduces key lookup latency from O(N network queries) to O(1) in-memory dictionary lookup.

### 3. Empirical Benchmark Results & Memory Profiling (`tracemalloc`)

| Feed Row Count | Execution Time | Throughput | Peak RAM Memory |
|---|---|---|---|
| **1,000 Rows** | `0.327 s` | **3,061 rows/sec** | `1.34 MB` |
| **10,000 Rows** | `2.538 s` | **3,939 rows/sec** | `7.85 MB` |
| **50,000 Rows** | `2.897 s` | **17,259 rows/sec** | `14.74 MB` |

---

## 4. How to Explain This in an Interview

> *"We optimized pipeline performance through vectorized Pandas execution, in-memory surrogate key lookup caching, and PostgreSQL streaming `COPY FROM STDIN` bulk loading. Our empirical benchmarks demonstrate throughput exceeding **17,200 rows/second** at 50,000 rows with a peak memory footprint under **15 MB**."*
