# Data Lineage & Mapping Specification

## Overview
This document traces the complete end-to-end data lineage of every field from raw source CSV exports (`data/raw/`) through validation, cleaning, surrogate key resolution, and final persistence into `warehouse` and `metadata` tables.

---

## 1. Sales Transaction Lineage (`store_{store_id}_sales_{YYYYMMDD}.csv`)

```mermaid
flowchart LR
    subgraph Raw Source CSV
        A1[transaction_id]
        A2[store_id]
        A3[product_id]
        A4[customer_id]
        A5[employee_id]
        A6[quantity]
        A7[unit_price]
        A8[discount_amount]
        A9[transaction_time]
    end

    subgraph Validation Layer
        V1[Header & Non-null Check]
        V2[Regex & Type Coercion]
        V3[Domain Rule Validation]
    end

    subgraph Transformation & Lookup
        T1[String Normalization]
        T2[SK Lookup: dim_store]
        T3[SK Lookup: dim_product]
        T4[SK Lookup: dim_customer]
        T5[SK Lookup: dim_employee]
        T6[SK Lookup: dim_date]
        T7[Calc: net_sales_amount]
    end

    subgraph Target Table: warehouse.fact_sales
        F1[transaction_id]
        F2[store_sk FK]
        F3[product_sk FK]
        F4[customer_sk FK]
        F5[employee_sk FK]
        F6[date_sk FK]
        F7[quantity]
        F8[unit_price]
        F9[discount_amount]
        F10[net_sales_amount]
        F11[transaction_time]
    end

    A1 --> V1 --> T1 --> F1
    A2 --> V1 --> T2 --> F2
    A3 --> V1 --> T3 --> F3
    A4 --> V2 --> T4 --> F4
    A5 --> V1 --> T5 --> F5
    A9 --> V2 --> T6 --> F6
    A6 --> V3 --> F7
    A7 --> V3 --> F8
    A8 --> V3 --> F9
    A6 & A7 & A8 --> T7 --> F10
    A9 --> V3 --> F11
```

---

## 2. Field-by-Field Column Mapping Matrix

| Source File | Source Column | Transformation Rule | Target Schema.Table | Target Column | Target Data Type |
|---|---|---|---|---|---|
| `sales.csv` | `transaction_id` | Trim whitespace | `warehouse.fact_sales` | `transaction_id` | `VARCHAR(100)` |
| `sales.csv` | `store_id` | Dimension lookup on `dim_store.store_id` | `warehouse.fact_sales` | `store_sk` | `BIGINT` |
| `sales.csv` | `product_id` | Dimension lookup on `dim_product.product_id` | `warehouse.fact_sales` | `product_sk` | `BIGINT` |
| `sales.csv` | `customer_id` | Dimension lookup on `dim_customer.customer_id` (NULL if blank) | `warehouse.fact_sales` | `customer_sk` | `BIGINT` |
| `sales.csv` | `employee_id` | Dimension lookup on `dim_employee.employee_id` | `warehouse.fact_sales` | `employee_sk` | `BIGINT` |
| `sales.csv` | `transaction_time` | Format to `YYYYMMDD` integer for `dim_date.date_sk` lookup | `warehouse.fact_sales` | `date_sk` | `INT` |
| `sales.csv` | `quantity` | Coerce to `INT`, reject if `<= 0` | `warehouse.fact_sales` | `quantity` | `INT` |
| `sales.csv` | `unit_price` | Coerce to `NUMERIC(10,2)`, reject if `< 0.00` | `warehouse.fact_sales` | `unit_price` | `NUMERIC(10,2)` |
| `sales.csv` | `discount_amount` | Default `0.00` if empty | `warehouse.fact_sales` | `discount_amount` | `NUMERIC(10,2)` |
| Derived | N/A | `(quantity * unit_price) - discount_amount` | `warehouse.fact_sales` | `net_sales_amount` | `NUMERIC(12,2)` |
