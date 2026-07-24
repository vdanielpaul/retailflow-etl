# Chapter 14: Step-by-Step Data Walkthrough

## 1. What Problem Does This Solve?
Understanding pipeline architecture abstractly is good, but tracing a single record step-by-step through every transformation function bridges the gap between theory and code execution.

---

## 2. The Input CSV Line Item

Consider a raw line item arriving in `data/raw/sales_20260724.csv`:

```csv
transaction_id,store_id,product_id,employee_id,customer_id,quantity,unit_price,discount_amount,transaction_time
TX-88991,  STR-001  ,prod-442,EMP-10,CUST-999,2,49.9899,5.00,2026-07-24 14:30:00
```

---

## 3. Module-by-Module Transformation Walkthrough

### Step 1: Ingestion & Incremental Check
- `IncrementalEngine` hashes file `sales_20260724.csv` -> `SHA-256: 4f8b9a...`
- `WatermarkManager` confirms hash is `NEW`.

### Step 2: Data Quality Validation (`ValidationEngine`)
- `SchemaValidator`: Required columns present -> `PASS`
- `DataTypeValidator`: `quantity` (2) -> `int`, `unit_price` (49.9899) -> `Decimal` -> `PASS`
- `BusinessRuleValidator`: `quantity > 0` (2), `unit_price >= 0` (49.9899), `transaction_time <= current_utc` -> `PASS`

### Step 3: Canonical Model Instantiation (`CanonicalSale`)
```python
CanonicalSale(
    transaction_id="TX-88991",
    store_id="  STR-001  ",
    product_id="prod-442",
    employee_id="EMP-10",
    customer_id="CUST-999",
    quantity=2,
    unit_price=Decimal("49.9899"),
    discount_amount=Decimal("5.00"),
    transaction_time=datetime(2026, 7, 24, 14, 30, 0),
)
```

### Step 4: String Cleaning (`cleaner.py`)
- Trims whitespace from `store_id`: `"  STR-001  "` -> `"STR-001"`

### Step 5: Normalization (`normalizer.py`)
- Uppercases product code: `"prod-442"` -> `"PROD-442"`
- Rounds unit price to 2 decimal places: `49.9899` -> `49.99`

### Step 6: Financial Metrics Enrichment (`enricher.py`)
Calculates derived financial fields:
- `gross_sales_amount` = $2 \times 49.99 = \$99.98$
- `net_sales_amount` = $\$99.98 - \$5.00 = \$94.98$
- `discount_percentage` = $(\$5.00 / \$99.98) \times 100 = 5.00\%$
- `effective_unit_price` = $\$94.98 / 2 = \$47.49$

### Step 7: In-Memory Surrogate Key Resolution (`surrogate_keys.py`)
Lookup against in-memory dictionary caches:
- `store_id = "STR-001"` -> `store_sk = 1`
- `product_id = "PROD-442"` -> `product_sk = 42`
- `customer_id = "CUST-999"` -> `customer_sk = 105`
- `employee_id = "EMP-10"` -> `employee_sk = 10`
- `transaction_time = 2026-07-24` -> `date_sk = 20260724`

### Step 8: Fact Sales Payload Construction (`fact_builder.py`)
Attaches `audit_run_id = 501` to form final payload:
```python
{
    "transaction_id": "TX-88991",
    "date_sk": 20260724,
    "customer_sk": 105,
    "product_sk": 42,
    "store_sk": 1,
    "employee_sk": 10,
    "transaction_time": "2026-07-24 14:30:00+00",
    "quantity": 2,
    "unit_price": 49.99,
    "discount_amount": 5.00,
    "net_sales_amount": 94.98,
    "audit_run_id": 501,
}
```

### Step 9: Atomic Ingestion into PostgreSQL (`WarehouseLoaderEngine`)
Executed via `COPY FROM STDIN` streaming into `warehouse.fact_sales` inside atomic transaction scope `BEGIN ... COMMIT`.

---

## 4. How to Explain This in an Interview

> *"When a raw line item enters our pipeline, it is validated, instantiated into a Canonical Sale model, stripped of whitespace, normalized, enriched with financial metrics (net sales, discount percentage), mapped to integer dimension surrogate keys via in-memory caches, and bulk loaded into `warehouse.fact_sales` inside a single atomic SQL transaction."*
