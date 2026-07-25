"""100K record DirectRunner benchmark for the TransformationAdapter.

Measures throughput and execution time of the transformation adapter in isolation
(no Beam overhead) to establish a pre-pipeline baseline. This benchmarks the
adapter's Python execution cost per element.

Usage:
    python scripts/benchmark_transformation_adapter.py
"""

from __future__ import annotations

import gc
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add src to path for direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from retailflow.cloud.pipeline.adapters.transformation_adapter import TransformationAdapter


def _make_records(n: int) -> list:
    """Generate n canonical sale dicts to transform."""
    now = datetime.now(timezone.utc).isoformat()

    valid = {
        "transaction_id": "TXN-{i}",
        "store_id": "str-01",
        "product_id": "prd-01",
        "customer_id": "cst-01",
        "employee_id": "emp-01",
        "quantity": 2,
        "unit_price": 19.99,
        "discount_amount": 1.50,
        "transaction_time": now,
        "email": "USER@EXAMPLE.COM",
    }

    records = []
    for i in range(n):
        rec = valid.copy()
        rec["transaction_id"] = f"txn-{i:07d}"
        records.append(rec)
    return records


def run_benchmark(n: int = 100_000) -> None:
    print(f"\n{'='*60}")
    print(f"  RetailFlow — TransformationAdapter Benchmark")
    print(f"  Records: {n:,}")
    print(f"{'='*60}\n")

    # Instantiate once — mirrors setup() lifecycle in ApplyTransformationFn
    adapter = TransformationAdapter()

    print("Generating records...", end=" ", flush=True)
    records = _make_records(n)
    print("done.")

    gc.collect()
    gc.disable()

    print(f"Running transformations...", end=" ", flush=True)
    t_start = time.perf_counter()

    success_count = 0
    failure_count = 0
    for record in records:
        result = adapter.transform(record)
        if result.success:
            success_count += 1
        else:
            failure_count += 1

    t_end = time.perf_counter()
    gc.enable()

    elapsed_s = t_end - t_start
    throughput = n / elapsed_s

    print("done.\n")
    print(f"  Duration          : {elapsed_s:.3f}s")
    print(f"  Throughput        : {throughput:,.0f} records/sec")
    print(f"  Successful        : {success_count:,} ({success_count/n*100:.1f}%)")
    assert success_count == n, "All benchmark records should succeed transformation."
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    run_benchmark(100_000)
