"""Data normalization stage: email casing, code formatting, and currency precision rounding."""

from __future__ import annotations

import pandas as pd


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize formatted fields like email lowercase, store codes uppercase, and monetary decimal rounding.

    Args:
        df: Cleaned DataFrame.

    Returns:
        Normalized Pandas DataFrame.
    """
    norm_df = df.copy()

    # 1. Lowercase email addresses
    if "email" in norm_df.columns:
        norm_df["email"] = norm_df["email"].astype(str).str.lower()
        norm_df.loc[norm_df["email"] == "none", "email"] = None

    # 2. Uppercase business codes (store_id, product_id, employee_id, transaction_id)
    code_cols = ["store_id", "product_id", "employee_id", "customer_id", "transaction_id"]
    for col in code_cols:
        if col in norm_df.columns:
            mask = norm_df[col].notna()
            norm_df.loc[mask, col] = norm_df.loc[mask, col].astype(str).str.upper()

    # Ensure discount_amount exists
    if "discount_amount" not in norm_df.columns:
        norm_df["discount_amount"] = 0.00

    # 3. Currency decimal precision rounding (2 decimal places)
    monetary_cols = ["unit_price", "discount_amount"]
    for col in monetary_cols:
        if col in norm_df.columns:
            norm_df[col] = pd.to_numeric(norm_df[col], errors="coerce").round(2)
            norm_df[col] = norm_df[col].fillna(0.00)

    # 4. Quantity integer cast
    if "quantity" in norm_df.columns:
        norm_df["quantity"] = pd.to_numeric(norm_df["quantity"], errors="coerce").fillna(1).astype(int)

    return norm_df
