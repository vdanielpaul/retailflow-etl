"""Canonical Data Model (CDM) representations for source-agnostic entity normalization."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CanonicalCustomer(BaseModel):
    """Canonical representation of a Customer entity."""

    model_config = ConfigDict(str_strip_whitespace=True)

    customer_id: str = Field(..., min_length=1)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: Optional[str] = None  # noqa: UP045
    phone: Optional[str] = None  # noqa: UP045


class CanonicalProduct(BaseModel):
    """Canonical representation of a Product entity."""

    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    brand: str = Field(..., min_length=1)
    unit_price: Decimal = Field(..., ge=Decimal("0.00"))


class CanonicalStore(BaseModel):
    """Canonical representation of a Store entity."""

    model_config = ConfigDict(str_strip_whitespace=True)

    store_id: str = Field(..., min_length=1)
    store_name: str = Field(..., min_length=1)
    region: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    state: str = Field(..., min_length=2, max_length=2)


class CanonicalEmployee(BaseModel):
    """Canonical representation of an Employee entity."""

    model_config = ConfigDict(str_strip_whitespace=True)

    employee_id: str = Field(..., min_length=1)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    store_id: str = Field(..., min_length=1)


class CanonicalSale(BaseModel):
    """Canonical representation of a Point-of-Sale line-item transaction."""

    model_config = ConfigDict(str_strip_whitespace=True)

    transaction_id: str = Field(..., min_length=1)
    store_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    customer_id: Optional[str] = None  # noqa: UP045
    employee_id: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=Decimal("0.00"))
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    transaction_time: datetime

    @field_validator("discount_amount", mode="before")
    @classmethod
    def default_discount(cls, v: Any) -> Any:
        if v is None or v == "" or (isinstance(v, float) and pd_isna(v)):
            return Decimal("0.00")
        return v


def pd_isna(val: Any) -> bool:
    """Helper checking if value is pandas NA/NaN."""
    try:
        import pandas as pd
        return bool(pd.isna(val))
    except ImportError:
        return False
