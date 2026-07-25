"""100K record DirectRunner benchmark for the BusinessRuleAdapter.

Measures throughput and execution time of the validation adapter in isolation
(no Beam overhead) to establish a pre-pipeline baseline. This script is
intentionally simple — it is not a Beam pipeline benchmark; it benchmarks the
adapter's Python execution cost per element.

Usage:
    python scripts/benchmark_validation_adapter.py
"""

from __future__ import annotations

import gc
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add src to path for direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from retailflow.cloud.pipeline.adapters.business_rule_adapter import BusinessRuleAdapter


def _make_records(n: int) -> list:
    """Generate n canonical sale dicts — 90% valid, 10% with future timestamp."""
    now = datetime.now(timezone.utc).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    valid = {
        "transaction_id": "TXN-{i}",
        "store_id": "STR-01",
        "product_id": "PRD-01",
        "customer_id": "CST-01",
        "employee_id": "EMP-01",
        "quantity": 2,
        "unit_price": 19.99,
        "discount_amount": 0.0,
        "transaction_time": now,
    }
    invalid = {**valid, "transaction_time": future}

    records = []
    for i in range(n):
        rec = (invalid if i % 10 == 0 else valid).copy()
        rec["transaction_id"] = f"TXN-{i:07d}"
        records.append(rec)
    return records


def run_benchmark(n: int = 100_000) -> None:
    print(f"\n{'='*60}")
    print(f"  RetailFlow — BusinessRuleAdapter Benchmark")
    print(f"  Records: {n:,}")
    print(f"{'='*60}\n")

    # Instantiate once — mirrors setup() lifecycle in ValidateSaleRecordFn
    adapter = BusinessRuleAdapter()

    print("Generating records...", end=" ", flush=True)
    records = _make_records(n)
    print("done.")

    gc.collect()
    gc.disable()

    print(f"Running validation...", end=" ", flush=True)
    t_start = time.perf_counter()

    valid_count = 0
    invalid_count = 0
    for record in records:
        result = adapter.validate(record)
        if result.valid:
            valid_count += 1
        else:
            invalid_count += 1

    t_end = time.perf_counter()
    gc.enable()

    elapsed_s = t_end - t_start
    throughput = n / elapsed_s

    print("done.\n")
    print(f"  Duration          : {elapsed_s:.3f}s")
    print(f"  Throughput        : {throughput:,.0f} records/sec")
    print(f"  Valid records     : {valid_count:,} ({valid_count/n*100:.1f}%)")
    print(f"  Invalid records   : {invalid_count:,} ({invalid_count/n*100:.1f}%)")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    run_benchmark(100_000)
