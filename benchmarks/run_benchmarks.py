"""Performance benchmarking and memory profiling suite for RetailFlow ETL."""

from __future__ import annotations

import time
import tracemalloc
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd

from retailflow.config.settings import Settings
from retailflow.pipeline.context import PipelineContext
from retailflow.transformation.engine import TransformationEngine
from retailflow.validation.engine import ValidationEngine
from tests.harness.data_generator import SyntheticDataGenerator


def benchmark_dataset(row_count: int) -> dict[str, float]:
    """Run performance benchmark across validation and transformation for target row count.

    Args:
        row_count: Number of synthetic feed rows to generate and process.

    Returns:
        Dictionary of performance metrics (throughput, stage latency, peak memory).
    """
    print(f"\n--- Running Benchmark for {row_count:,} Rows ---")
    df = SyntheticDataGenerator.generate_sales_feed(row_count=row_count, duplicate_pct=0.01)

    settings = Settings()
    context = PipelineContext(
        configuration=settings,
        database=MagicMock(),
        logger=MagicMock(),
    )

    tracemalloc.start()
    start_total = time.perf_counter()

    # 1. Validation Benchmark
    start_val = time.perf_counter()
    val_engine = ValidationEngine()
    clean_df, val_report = val_engine.validate_feed(df, context)
    val_duration_ms = (time.perf_counter() - start_val) * 1000.0

    # 2. Transformation Benchmark
    start_trans = time.perf_counter()
    trans_engine = TransformationEngine()
    fact_df, trans_report = trans_engine.transform_sales_feed(clean_df, context)
    trans_duration_ms = (time.perf_counter() - start_trans) * 1000.0

    total_duration_sec = time.perf_counter() - start_total
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mem_mb = peak_mem / (1024 * 1024)
    rows_per_sec = (row_count / total_duration_sec) if total_duration_sec > 0 else 0.0

    metrics = {
        "rows": float(row_count),
        "total_runtime_sec": round(total_duration_sec, 3),
        "validation_latency_ms": round(val_duration_ms, 2),
        "transformation_latency_ms": round(trans_duration_ms, 2),
        "throughput_rows_per_sec": round(rows_per_sec, 2),
        "peak_memory_mb": round(peak_mem_mb, 2),
    }

    print(f"Total Runtime: {total_duration_sec:.3f} seconds")
    print(f"Throughput: {rows_per_sec:,.2f} rows/sec")
    print(f"Peak Memory: {peak_mem_mb:.2f} MB")
    return metrics


def main() -> None:
    """Execute benchmark suite across 1,000, 10,000, and 50,000 row feeds."""
    print("=========================================================")
    print("      RetailFlow ETL Performance & Memory Benchmarks     ")
    print("=========================================================")

    sizes = [1000, 10000, 50000]
    results = []

    for size in sizes:
        res = benchmark_dataset(size)
        results.append(res)

    print("\n=========================================================")
    print("                     Benchmark Summary                   ")
    print("=========================================================")
    print(f"{'Rows':<10} | {'Runtime (s)':<12} | {'Throughput (r/s)':<18} | {'Peak Mem (MB)':<12}")
    print("-" * 60)
    for r in results:
        print(f"{int(r['rows']):<10,} | {r['total_runtime_sec']:<12.3f} | {r['throughput_rows_per_sec']:<18,.2f} | {r['peak_memory_mb']:<12.2f}")


if __name__ == "__main__":
    main()
