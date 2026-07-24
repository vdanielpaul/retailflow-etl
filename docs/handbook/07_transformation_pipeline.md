# Chapter 7: Modular Transformation Pipeline

## 1. What Problem Does This Solve?
Raw data cannot be dumped directly into warehouse tables. Input strings contain messy leading/trailing whitespace, inconsistent capitalization (`john.doe@gmail.com` vs `JOHN.DOE@GMAIL.COM`), missing financial metrics (`net_sales_amount`), and natural business keys (`STR-001`) rather than integer warehouse surrogate keys (`store_sk=1`).

Putting all cleaning, calculation, key resolution, and SCD logic into a single monolithic script creates untestable, brittle code.

---

## 2. Why Do We Need It?
A modular transformation pipeline divides data transformation into a chain of single-responsibility stages:

```mermaid
flowchart LR
    CleanDF[Clean DataFrame] --> Cleaner[1. Data Cleaner]
    Cleaner --> Normalizer[2. Data Normalizer]
    Normalizer --> Enricher[3. Financial Enricher]
    Enricher --> Surrogate[4. In-Memory Surrogate Resolver]
    Surrogate --> SCD1[5. SCD Type 1 Processor]
    SCD1 --> Fact[6. Fact Payload Builder]
```

---

## 3. How Our Implementation Works

### Stage 1: Data Cleaner (`cleaner.py`)
- **Purpose**: Trims whitespace, strips non-printable unicode characters, and standardizes empty string representations (`""`, `"N/A"`, `"NULL"`) into proper `NaN` / `None` values.
- **Before**: `"  STR-001  "`, `"N/A"`
- **After**: `"STR-001"`, `None`

### Stage 2: Data Normalizer (`normalizer.py`)
- **Purpose**: Normalizes case and formats monetary values. Lowercases emails, uppercases store and product codes, and rounds unit prices to 2 decimal places.
- **Before**: `John.Doe@Gmail.COM`, `str-001`, `49.989999`
- **After**: `john.doe@gmail.com`, `STR-001`, `49.99`

### Stage 3: Financial Metrics Enricher (`enricher.py`)
- **Purpose**: Derives calculated financial metrics required for business reporting.
- **Formulas**:
  - $\text{gross\_sales\_amount} = \text{quantity} \times \text{unit\_price}$
  - $\text{net\_sales\_amount} = \text{gross\_sales\_amount} - \text{discount\_amount}$
  - $\text{discount\_percentage} = \frac{\text{discount\_amount}}{\text{gross\_sales\_amount}} \times 100$
  - $\text{effective\_unit\_price} = \frac{\text{net\_sales\_amount}}{\text{quantity}}$

### Stage 4 & 5: In-Memory Surrogate Key Resolution & SCD Type 1 (`surrogate_keys.py` & `scd.py`)
- **Purpose**: Maps natural keys (`STR-001`, `PROD-001`, `CUST-0001`) to integer warehouse surrogate keys (`store_sk=1`, `product_sk=42`, `customer_sk=105`).
- **In-Memory Caching**: Pre-loads dimension maps into Python dictionary lookup caches (`StoreCache`, `ProductCache`, `CustomerCache`) to eliminate row-by-row SQL queries.
- **SCD Type 1 Delta Processor**: Compares incoming dimension attributes against target warehouse tables to execute in-place updates for changed attributes.

### Stage 6: Fact Payload Builder (`fact_builder.py`)
- **Purpose**: Assembles the final `fact_sales` DataFrame matching warehouse column signatures, date surrogate key format (`date_sk = YYYYMMDD`), and attaching `audit_run_id`.

---

## 4. How to Explain This in an Interview

> *"Our transformation pipeline consists of 6 modular stages: string cleaning, case normalization, financial metric enrichment, in-memory surrogate key resolution, SCD Type 1 delta processing, and fact payload construction. Decoupling transformation into dedicated modules ensures high testability and sub-second vectorized processing."*
