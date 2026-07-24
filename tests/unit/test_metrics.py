"""Unit tests for MetricsCollector."""

from retailflow.metrics.collector import MetricsCollector


def test_metrics_collector_recording() -> None:
    """Test recording row counts and stage durations."""
    metrics = MetricsCollector()
    metrics.record_rows(read=1000, valid=950, invalid=50, loaded=950, duplicates=10)
    metrics.record_stage_time("SCHEMA_VALIDATION", 120.5)
    metrics.record_stage_time("FACT_LOADING", 350.0)

    summary = metrics.to_dict()
    assert summary["rows_read"] == 1000
    assert summary["rows_valid"] == 950
    assert summary["rows_invalid"] == 50
    assert summary["rows_loaded"] == 950
    assert summary["duplicate_rows"] == 10
    assert summary["validation_time_ms"] == 120.5
    assert summary["loading_time_ms"] == 350.0
