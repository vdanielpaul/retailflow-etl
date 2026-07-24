# Transformation Derivation Lineage

## Overview
This document illustrates how derived financial metrics and surrogate keys in `warehouse.fact_sales` are computed from raw input CSV fields.

---

## Metric Derivation Diagrams

### 1. Financial Metrics Derivation

```mermaid
flowchart TD
    RawQty[raw.quantity] --> CoerceQty[Coerce to INT: qty]
    RawPrice[raw.unit_price] --> CoercePrice[Coerce to NUMERIC: unit_price]
    RawDisc[raw.discount_amount] --> CoerceDisc[Coerce to NUMERIC: discount_amount]

    CoerceQty & CoercePrice --> CalcGross["gross_sales_amount = qty * unit_price"]
    CalcGross & CoerceDisc --> CalcNet["net_sales_amount = gross_sales_amount - discount_amount"]
    CalcNet & CoerceDisc --> CalcDiscPct["discount_percentage = (discount_amount / gross_sales_amount) * 100"]
    CalcNet & CoerceQty --> CalcEffPrice["effective_unit_price = net_sales_amount / qty"]

    CalcNet --> TargetNet[fact_sales.net_sales_amount]
    CalcGross --> TargetGross[Analytics Layer / BI Views]
    CalcDiscPct --> TargetDisc[Analytics Layer / BI Views]
```

### 2. Surrogate Key Resolution Lineage

```mermaid
flowchart TD
    RawStoreID[raw.store_id] --> CleanStoreID[Trim & Uppercase: store_id]
    CleanStoreID --> CacheStore{StoreCache.get store_id}
    CacheStore -- Hit --> StoreSK[store_sk = Cache Match]
    CacheStore -- Miss --> FallbackStore[store_sk = -1 UNKNOWN_KEY]

    RawDate[raw.transaction_time] --> ParseDate[Parse Timestamp YYYY-MM-DD]
    ParseDate --> FormatDateSk["date_sk = YYYYMMDD (Int)"]

    StoreSK --> FactStore[fact_sales.store_sk]
    FormatDateSk --> FactDate[fact_sales.date_sk]
```
