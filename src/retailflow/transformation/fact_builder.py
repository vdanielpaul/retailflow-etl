"""Fact table builder constructing warehouse-ready fact payloads."""

from __future__ import annotations

import pandas as pd

from retailflow.pipeline.context import PipelineContext


def build_fact_sales_payload(df: pd.DataFrame, context: PipelineContext) -> pd.DataFrame:
    """Construct final fact_sales DataFrame containing surrogate keys, financial metrics, and audit run metadata.

    Target Schema Columns:
    - transaction_id
    - date_sk
    - customer_sk
    - product_sk
    - store_sk
    - employee_sk
    - transaction_time
    - quantity
    - unit_price
    - discount_amount
    - net_sales_amount
    - audit_run_id

    Args:
        df: Enriched DataFrame with surrogate keys resolved.
        context: Shared pipeline context.

    Returns:
        PostgreSQL warehouse-ready DataFrame for warehouse.fact_sales.
    """
    fact_df = pd.DataFrame()

    fact_df["transaction_id"] = df["transaction_id"]
    fact_df["date_sk"] = df["date_sk"]
    fact_df["customer_sk"] = df["customer_sk"] if "customer_sk" in df.columns else None
    fact_df["product_sk"] = df["product_sk"]
    fact_df["store_sk"] = df["store_sk"]
    fact_df["employee_sk"] = df["employee_sk"]
    fact_df["transaction_time"] = pd.to_datetime(df["transaction_time"])
    fact_df["quantity"] = df["quantity"].astype(int)
    fact_df["unit_price"] = df["unit_price"].astype(float)
    fact_df["discount_amount"] = df["discount_amount"].astype(float)
    fact_df["net_sales_amount"] = df["net_sales_amount"].astype(float)
    fact_df["audit_run_id"] = context.metadata.get("audit_run_id", 0)

    return fact_df
