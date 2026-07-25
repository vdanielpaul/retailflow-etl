# RetailFlow ETL v2.0 — Validation Pipeline Performance Benchmark

**Benchmark ID:** BM-001-validation-adapter
**Date:** 2026-07-25
**Task:** Milestone 3, Task 3.3 — Validation Engine Integration
**Branch:** `feature/milestone-3-validation` (merged to `develop`, tagged `v2.0.0-m3.3`)

---

## Environment

| Dimension | Value |
|---|---|
| **Hardware** | Apple MacBook (macOS) |
| **Python version** | 3.9.6 |
| **Apache Beam version** | 2.69.0 |
| **Runner** | DirectRunner (single worker, in-process) |
| **GC** | Disabled during measurement loop (`gc.disable()`) |
| **Pandas version** | (project dependency) |

> [!NOTE]
> DirectRunner benchmarks represent single-worker throughput. On Dataflow, the pipeline scales horizontally across N workers with near-linear throughput scaling for embarrassingly parallel transforms.

---

## Dataset Characteristics

| Attribute | Value |
|---|---|
| **Total records** | 100,000 |
| **Valid records** | 90,000 (90%) |
| **Invalid records** | 10,000 (10%) — future transaction date |
| **Failure injection** | Every 10th record has `transaction_time` 30 days in the future |
| **Record width** | 9 fields (canonical sale model) |
| **Generation method** | Synthetic — `scripts/benchmark_validation_adapter.py` |

---

## Results

```
============================================================
  RetailFlow — BusinessRuleAdapter Benchmark
  Records: 100,000
============================================================

  Duration          : 52.433s
  Throughput        : 1,907 records/sec
  Valid records     : 90,000 (90.0%)
  Invalid records   : 10,000 (10.0%)

============================================================
```

---

## Bottleneck Analysis

### Primary Bottleneck — Per-Element DataFrame Construction

The dominant cost is constructing a single-row `pd.DataFrame([record])` for every canonical dict in `BusinessRuleAdapter.validate()`:

```python
df = pd.DataFrame([record])  # ~0.5ms fixed overhead per call
result = self._validator.validate(df)
```

At 100,000 records: `100,000 × ~0.5ms ≈ 50s` — which matches the observed 52.4s.

This is the inherent cost of row-level adaptation to a batch-native Pandas API. The `BusinessRuleValidator` was designed to receive a full DataFrame; the adapter wraps each single record to satisfy that interface.

### Secondary Factors

| Factor | Assessment |
|---|---|
| Validator object allocation | Negligible — instantiated once in `setup()`, reused across all elements |
| Error reporting overhead | Negligible — error_summary is a small dict |
| JSON serialisation (quarantine) | Not measured in this benchmark (occurs in the DoFn, not the adapter) |

---

## Dataflow Scaling Projection

| Workers | Projected Throughput | Time for 10M Records |
|---|---|---|
| 1 | ~1,900 rec/sec | ~87 min |
| 10 | ~19,000 rec/sec | ~9 min |
| 50 | ~95,000 rec/sec | ~1.8 min |
| 100 | ~190,000 rec/sec | ~53 sec |

Scaling is near-linear because `ValidateSaleRecordFn` is stateless — there is no cross-element coordination, no shared locks, and no global state.

> [!NOTE]
> Real-world Dataflow throughput depends on bundle size, worker startup time, GCS read bandwidth, and serialisation overhead. These projections represent the compute-side ceiling, not wall-clock end-to-end time.

---

## Comparison Baseline

| Pipeline Stage | Throughput | Benchmark ID |
|---|---|---|
| CSV Parsing & Canonicalization (Task 3.2) | — | BM-002 (pending) |
| **Business Rule Validation (Task 3.3)** | **1,907 rec/sec** | **BM-001** |
| Transformation (Task 3.4) | — | BM-003 (pending) |

A cumulative end-to-end benchmark will be added after Task 3.5.

---

## Optimization Roadmap

The following optimizations are documented for a future performance sprint. **None of these are implemented in v2.0.0-m3.3.**

### 1. Bundle-Level Batch Validation

**Projected improvement:** 10–50× throughput increase per worker.

Instead of constructing a single-row DataFrame per element, accumulate records within a bundle and validate the full batch in `finish_bundle()`:

```python
def start_bundle(self):
    self._bundle: List[Dict] = []

def process(self, element):
    self._bundle.append(element)

def finish_bundle(self):
    df = pd.DataFrame(self._bundle)
    result = self._validator.validate(df)
    # Route each row to main or side output based on failed_indices
    for i, record in enumerate(self._bundle):
        if i in result.failed_indices:
            yield beam.pvalue.TaggedOutput(TAG_INVALID, ...)
        else:
            yield record
```

**Tradeoff:** Error attribution per element becomes more complex (requires tracking `failed_indices` per bundle). Bundle boundaries introduce non-determinism in error groupings.

### 2. `beam.BatchElements` Transform

Beam provides `beam.BatchElements()` which adaptively batches elements based on bundle processing time. Inserting this before `ValidateSaleRecordFn` would allow the DoFn to receive pre-formed batches without manual `start_bundle`/`finish_bundle` management.

### 3. Apache Arrow-Based Validation

Replace per-element `pd.DataFrame` construction with Arrow record batches:
```python
import pyarrow as pa
table = pa.table(records)
df = table.to_pandas()
```

Arrow's columnar format and zero-copy semantics reduce memory allocation overhead significantly for wide records.

### 4. Beam DataFrame API

Apache Beam provides a DataFrame API (`beam.dataframe`) that executes Pandas-like operations natively in the Beam execution model. If the validator logic can be expressed as DataFrame transformations, the API eliminates the row-level adaptation layer entirely.

**Assessment:** Requires refactoring `BusinessRuleValidator` to use deferred execution semantics. Significant implementation cost; evaluate after Task 3.5.

### 5. Pre-computed Validation Masks

For business rules that are expressible as vectorized Pandas operations (e.g., `quantity > 0`, `transaction_time <= now()`), pre-compute failure masks on the full bundle DataFrame before iterating rows. This reduces per-element branching overhead.

---

## Decision: No Optimization in Current Sprint

The current bottleneck (1,907 rec/sec per worker) is acceptable for the v2.0 milestone because:

1. **GCS I/O dominates at Dataflow scale.** CSV read throughput from GCS is the real bottleneck for store-scale files (250 stores × ~10MB nightly = ~2.5GB). At Dataflow speeds, parsing and transfer overhead exceeds validation CPU cost.
2. **Bundle-level optimization complicates error attribution.** The quarantine schema requires per-record error context. Row-level element processing is simpler and produces correct quarantine records.
3. **The architecture is testable and correct first.** Performance optimizations should follow measurement, not precede it.

Re-evaluate after the full pipeline end-to-end benchmark (post Task 3.5).
