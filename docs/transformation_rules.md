# Transformation Rules Specification

## Overview
This document specifies the exact cleaning, normalization, enrichment, and surrogate key mapping rules applied by the `retailflow.transformation` engine.

---

## Column Transformation Rules Matrix

| Target Column | Stage | Rule / Algorithm | Input Example | Output Example |
|---|---|---|---|---|
| `transaction_id` | Cleaner / Normalizer | Trim whitespace, uppercase string | `" tx-994821 "` | `"TX-994821"` |
| `store_id` | Cleaner / Normalizer | Trim whitespace, uppercase, remove non-printable characters | `" str-001 "` | `"STR-001"` |
| `email` | Cleaner / Normalizer | Trim whitespace, lowercase string, convert `"N/A"`/`"null"` to `None` | `" Alice.Smith@Example.COM "` | `"alice.smith@example.com"` |
| `quantity` | Normalizer | Coerce to integer, default `1` if invalid | `" 5 "` | `5` |
| `unit_price` | Normalizer | Coerce to float, round to 2 decimal places | `"149.989"` | `149.99` |
| `discount_amount` | Normalizer | Default `0.00` if empty, round to 2 decimal places | `""` | `0.00` |
| `gross_sales_amount` | Enricher | `quantity * unit_price` | `5 * 10.00` | `50.00` |
| `net_sales_amount` | Enricher | `(quantity * unit_price) - discount_amount` | `50.00 - 5.00` | `45.00` |
| `discount_percentage` | Enricher | `(discount_amount / gross_sales_amount) * 100` | `5.00 / 50.00 * 100` | `10.00` |
| `effective_unit_price` | Enricher | `net_sales_amount / quantity` | `45.00 / 5` | `9.00` |
| `store_sk` | Surrogate Key | Lookup `store_id` in `SurrogateKeyResolver._store_cache` | `"STR-001"` | `1` |
| `product_sk` | Surrogate Key | Lookup `product_id` in `SurrogateKeyResolver._product_cache` | `"PROD-001"` | `42` |
| `date_sk` | Surrogate Key | Convert `transaction_time` to integer `YYYYMMDD` | `"2026-07-24 10:15:00"` | `20260724` |
