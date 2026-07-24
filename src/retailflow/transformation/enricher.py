"""Data enrichment stage: derived financial business metrics and reporting flags."""

from __future__ import annotations

import pandas as pd


def enrich_sales_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate derived financial metrics: gross sales, net sales, discount percentage, effective unit price.

    Formulas:
    - gross_sales_amount = quantity * unit_price
    - net_sales_amount = (quantity * unit_price) - discount_amount
    - discount_percentage = (discount_amount / gross_sales_amount) * 100
    - effective_unit_price = net_sales_amount / quantity

    Args:
        df: Normalized sales DataFrame.

    Returns:
        Enriched DataFrame with calculated financial metrics.
    """
    enriched_df = df.copy()

    # Calculate Gross Sales
    qty = enriched_df["quantity"].astype(float)
    unit_price = enriched_df["unit_price"].astype(float)
    discount = enriched_df["discount_amount"].astype(float)

    gross_sales = (qty * unit_price).round(2)
    net_sales = (gross_sales - discount).round(2)

    # Prevent division by zero for discount percentage
    disc_pct = (discount / gross_sales.replace(0, 1.0) * 100.0).round(2)
    disc_pct = disc_pct.where(gross_sales > 0, 0.0)

    # Effective Unit Price
    eff_unit_price = (net_sales / qty.replace(0, 1.0)).round(2)

    enriched_df["gross_sales_amount"] = gross_sales
    enriched_df["net_sales_amount"] = net_sales
    enriched_df["discount_percentage"] = disc_pct
    enriched_df["effective_unit_price"] = eff_unit_price
    enriched_df["transaction_line_total"] = net_sales

    return enriched_df
