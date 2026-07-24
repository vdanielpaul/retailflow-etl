"""Transformation module handling cleaning, normalization, enrichment, surrogate keys, SCD Type 1, and fact building."""

from retailflow.transformation.cleaner import clean_dataframe
from retailflow.transformation.engine import TransformationEngine
from retailflow.transformation.enricher import enrich_sales_dataframe
from retailflow.transformation.fact_builder import build_fact_sales_payload
from retailflow.transformation.normalizer import normalize_dataframe
from retailflow.transformation.scd import SCD1Metrics, SCD1Processor
from retailflow.transformation.surrogate_keys import (
    UNKNOWN_SURROGATE_KEY,
    SurrogateKeyResolver,
    UnknownKeyStrategy,
)

__all__ = [
    "TransformationEngine",
    "clean_dataframe",
    "normalize_dataframe",
    "enrich_sales_dataframe",
    "build_fact_sales_payload",
    "SurrogateKeyResolver",
    "UnknownKeyStrategy",
    "UNKNOWN_SURROGATE_KEY",
    "SCD1Processor",
    "SCD1Metrics",
]
