"""Unit tests for RetailFlow transformation engine and sub-components."""

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from retailflow.config.settings import Settings
from retailflow.pipeline.context import PipelineContext
from retailflow.transformation.cleaner import clean_dataframe
from retailflow.transformation.engine import TransformationEngine
from retailflow.transformation.enricher import enrich_sales_dataframe
from retailflow.transformation.normalizer import normalize_dataframe
from retailflow.transformation.scd import SCD1Processor
from retailflow.transformation.surrogate_keys import SurrogateKeyResolver


@pytest.fixture
def sample_context(tmp_path: Path) -> PipelineContext:
    """Fixture providing PipelineContext instance."""
    settings = Settings()
    mock_db = MagicMock()
    mock_logger = MagicMock()

    return PipelineContext(
        configuration=settings,
        database=mock_db,
        logger=mock_logger,
    )


def test_clean_dataframe() -> None:
    """Test whitespace trimming and NULL string standardization."""
    df = pd.DataFrame(
        {
            "store_id": [" str-001 ", "STR-002"],
            "email": [" alice@example.com ", "N/A"],
        }
    )

    cleaned = clean_dataframe(df)

    assert cleaned["store_id"][0] == "str-001"
    assert cleaned["email"][0] == "alice@example.com"
    assert cleaned["email"][1] is None


def test_normalize_dataframe() -> None:
    """Test email lowercasing, business code uppercasing, and currency precision rounding."""
    df = pd.DataFrame(
        {
            "store_id": ["str-001"],
            "email": ["Alice.Smith@Example.COM"],
            "unit_price": ["149.989"],
            "discount_amount": ["5.00"],
            "quantity": ["2"],
        }
    )

    norm = normalize_dataframe(df)

    assert norm["store_id"][0] == "STR-001"
    assert norm["email"][0] == "alice.smith@example.com"
    assert norm["unit_price"][0] == 149.99
    assert norm["discount_amount"][0] == 5.00
    assert norm["quantity"][0] == 2


def test_enrich_sales_dataframe() -> None:
    """Test calculation of derived financial metrics."""
    df = pd.DataFrame(
        {
            "quantity": [5],
            "unit_price": [10.00],
            "discount_amount": [5.00],
        }
    )

    enriched = enrich_sales_dataframe(df)

    assert enriched["gross_sales_amount"][0] == 50.00
    assert enriched["net_sales_amount"][0] == 45.00
    assert enriched["discount_percentage"][0] == 10.00
    assert enriched["effective_unit_price"][0] == 9.00


def test_surrogate_key_resolver_caching() -> None:
    """Test in-memory lookup caching for natural business keys."""
    resolver = SurrogateKeyResolver()
    resolver._store_cache = {"STR-001": 101}
    resolver._product_cache = {"PROD-001": 202}

    assert resolver.resolve_store_sk("STR-001") == 101
    assert resolver.resolve_store_sk("UNKNOWN") == -1
    assert resolver.resolve_product_sk("PROD-001") == 202


def test_scd1_processor_delta_detection() -> None:
    """Test SCD Type 1 processor identifies inserts and attribute changes."""
    processor = SCD1Processor(natural_key="store_id", tracked_attributes=["store_name", "region"])

    existing_df = pd.DataFrame(
        {
            "store_id": ["STR-001", "STR-002"],
            "store_name": ["Old Store 1", "Store 2"],
            "region": ["East", "West"],
        }
    )

    incoming_df = pd.DataFrame(
        {
            "store_id": ["STR-001", "STR-002", "STR-003"],
            "store_name": ["New Store 1", "Store 2", "Store 3"],
            "region": ["East", "West", "South"],
        }
    )

    inserts_df, updates_df, metrics = processor.compute_scd1_delta(incoming_df, existing_df)

    assert metrics.rows_compared == 3
    assert metrics.rows_inserted == 1
    assert metrics.rows_changed == 1
    assert len(inserts_df) == 1
    assert len(updates_df) == 1


def test_transformation_engine_full_flow(sample_context: PipelineContext) -> None:
    """Test end-to-end transformation engine processing raw DataFrame into fact payload."""
    df = pd.DataFrame(
        {
            "transaction_id": ["tx-001"],
            "store_id": ["str-001"],
            "product_id": ["prod-001"],
            "employee_id": ["emp-001"],
            "customer_id": ["cust-001"],
            "quantity": ["2"],
            "unit_price": ["25.00"],
            "discount_amount": ["0.00"],
            "transaction_time": ["2026-07-24 10:00:00"],
        }
    )

    engine = TransformationEngine()
    engine.key_resolver._store_cache = {"STR-001": 1}
    engine.key_resolver._product_cache = {"PROD-001": 2}
    engine.key_resolver._employee_cache = {"EMP-001": 3}
    engine.key_resolver._customer_cache = {"CUST-001": 4}

    fact_df, report = engine.transform_sales_feed(df, sample_context)

    assert len(fact_df) == 1
    assert fact_df["store_sk"][0] == 1
    assert fact_df["product_sk"][0] == 2
    assert fact_df["net_sales_amount"][0] == 50.00
    assert fact_df["date_sk"][0] == 20260724
    assert report.rows_transformed == 1
