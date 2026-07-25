# RetailFlow ETL v2.0 — Transformation Pipeline Performance Benchmark

**Benchmark ID:** BM-003-transformation-adapter
**Date:** 2026-07-25
**Task:** Milestone 3, Task 3.4 — Transformation Engine Integration
**Branch:** `feature/milestone-3-transformation` (in development)

---

## Environment

| Dimension | Value |
|---|---|
| **Hardware** | Apple MacBook (macOS) |
| **Python version** | 3.9.6 |
| **Apache Beam version** | 2.69.0 |
| **Runner** | DirectRunner (single worker, in-process) |
| **GC** | Disabled during measurement loop (`gc.disable()`) |
| **Pandas version** | 2.2.2 |

---

## Dataset Characteristics

| Attribute | Value |
|---|---|
| **Total records** | 100,000 |
| **Valid records** | 100,000 (100%) |
| **Record width** | 10 fields (canonical sale model + email) |
| **Generation method** | Synthetic — `scripts/benchmark_transformation_adapter.py` |

---

```
============================================================
  RetailFlow — TransformationAdapter Benchmark
  Records: 100,000
============================================================

  Duration          : 445.222s
  Throughput        : 225 records/sec
  Successful        : 100,000 (100.0%)

============================================================
```


---

## Bottleneck Analysis

### Primary Bottleneck — Per-Element DataFrame Copies & Manipulation

The transformation throughput dropped to **225 records/sec** (an 8.5x decrease compared to the validation baseline of **1,907 records/sec**). 

The root cause remains the row-level adaptation of a batch-oriented DataFrame API. However, whereas validation only runs a relatively simple check-only sweep, the transformation stage performs heavy read-write manipulations across three distinct phases:

1. **Repeated DataFrame Copies (`df.copy()`):**
   Each of the three functions (`clean_dataframe`, `normalize_dataframe`, `enrich_sales_dataframe`) starts by calling `df.copy()`. In Pandas, copying even a 1-row DataFrame involves allocating new underlying numpy/arrow arrays, recreating Index structures, and duplicating metadata. This happens 3 times per record.
   
2. **String Accessors & Regex Operations (`clean_dataframe`):**
   For every string/object column, the cleaner calls `.astype(str).str.strip()` followed by a regex replace `.str.replace(r"[\x00-\x1F\x7F-\x9F]", "", regex=True)`. String accessors (`.str`) in Pandas are notoriously slow in Python loops because they wrap standard library string operations. Regex matching on single-character or single-word values has huge overhead compared to raw Python strings.
   
3. **Columnar Type Conversion and Rounding (`normalize_dataframe` & `enrich_sales_dataframe`):**
   The normalizer runs `pd.to_numeric()` and `.round(2)` on monetary columns, which performs type checks and parses values. The enricher casts columns to float and does math, then rounds. For a single-row DataFrame, these vectorized Pandas methods compile down to single-element operations with all the wrapper overhead of Pandas.

### Comparative Performance Breakdown

| Stage | Throughput (Single Worker) | Key Operations |
|---|---|---|
| Validation (Task 3.3) | ~1,907 rec/sec | Boolean check rules, no DataFrame copy, minimal writes |
| **Transformation (Task 3.4)** | **225 rec/sec** | 3 copies, regex replace, lower/upper string modifications, type casts, decimal rounding |

This comparison highlights that the adapter pattern is highly viable for correctness and logic preservation, but incurs a steep performance cost when wrapping fine-grained transformations in a batch-native library like Pandas.

---

## Optimization Roadmap

The optimization options for the transformation stage are identical to those identified in [`validation_benchmark.md`](./validation_benchmark.md):

1. **Bundle-Level Batch Transformation:** Accumulate dicts in a bundle, convert them all to a single large DataFrame, apply cleaning/normalization/enrichment as vectorized operations, and then yield individual elements. This is expected to improve performance by 10-50x.
2. **Arrow-Based Processing:** Leverage PyArrow for fast serialization and zero-copy conversion.
3. **Beam DataFrame API:** Evaluate Beam's built-in Pandas integration.
