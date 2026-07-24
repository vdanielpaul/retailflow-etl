# Data Dictionary & Schema Specification

## 1. Source CSV Layouts (Ingestion Specifications)

### 1.1 Sales Feed (`store_{store_id}_sales_{YYYYMMDD}.csv`)
Nightly POS export containing individual sales transaction line items.

| Source Column | Raw Data Type | Nullable | Validation Rules | Target Table.Column |
|---|---|---|---|---|
| `transaction_id` | `VARCHAR(100)` | No | Must be non-empty string | `fact_sales.transaction_id` |
| `store_id` | `VARCHAR(20)` | No | Must match `STR-[0-9]{3,}` format | `dim_store.store_id` -> `store_sk` |
| `customer_id` | `VARCHAR(50)` | Yes | Optional natural key | `dim_customer.customer_id` -> `customer_sk` |
| `product_id` | `VARCHAR(50)` | No | Natural product SKU | `dim_product.product_id` -> `product_sk` |
| `employee_id` | `VARCHAR(50)` | No | Cashier natural key | `dim_employee.employee_id` -> `employee_sk` |
| `quantity` | `INTEGER` | No | Must be integer > 0 | `fact_sales.quantity` |
| `unit_price` | `NUMERIC(10,2)` | No | Must be float/decimal >= 0.00 | `fact_sales.unit_price` |
| `discount_amount` | `NUMERIC(10,2)` | Yes | Default 0.00, must be >= 0.00 | `fact_sales.discount_amount` |
| `transaction_time` | `TIMESTAMP` | No | ISO 8601 string, cannot be in future | `fact_sales.transaction_time` |

---

### 1.2 Customer Master Feed (`customers_master_{YYYYMMDD}.csv`)
| Source Column | Raw Data Type | Nullable | Validation Rules | Target Table.Column |
|---|---|---|---|---|
| `customer_id` | `VARCHAR(50)` | No | Unique natural key | `dim_customer.customer_id` |
| `first_name` | `VARCHAR(100)` | No | Non-empty string | `dim_customer.first_name` |
| `last_name` | `VARCHAR(100)` | No | Non-empty string | `dim_customer.last_name` |
| `email` | `VARCHAR(255)` | Yes | Email regex check | `dim_customer.email` |
| `phone` | `VARCHAR(30)` | Yes | Standard phone characters | `dim_customer.phone` |

---

### 1.3 Product Master Feed (`products_master_{YYYYMMDD}.csv`)
| Source Column | Raw Data Type | Nullable | Validation Rules | Target Table.Column |
|---|---|---|---|---|
| `product_id` | `VARCHAR(50)` | No | Unique natural SKU | `dim_product.product_id` |
| `product_name` | `VARCHAR(255)` | No | Item description | `dim_product.product_name` |
| `category` | `VARCHAR(100)` | No | Merchandise category | `dim_product.category` |
| `brand` | `VARCHAR(100)` | No | Manufacturer brand | `dim_product.brand` |
| `unit_price` | `NUMERIC(10,2)` | No | Must be >= 0.00 | `dim_product.unit_price` |

---

## 2. Target Warehouse Tables (Star Schema)

### 2.1 `dim_customer`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `customer_sk` | `BIGINT` | `PRIMARY KEY` | Auto-incrementing surrogate key |
| `customer_id` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Natural key from CRM system |
| `first_name` | `VARCHAR(100)` | `NOT NULL` | Customer first name |
| `last_name` | `VARCHAR(100)` | `NOT NULL` | Customer last name |
| `email` | `VARCHAR(255)` | `NULLABLE` | Verified customer email |
| `phone` | `VARCHAR(30)` | `NULLABLE` | Contact phone number |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Insert timestamp |
| `updated_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Last SCD Type 1 update timestamp |

---

### 2.2 `dim_product`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `product_sk` | `BIGINT` | `PRIMARY KEY` | Auto-incrementing surrogate key |
| `product_id` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | SKU or natural product code |
| `product_name` | `VARCHAR(255)` | `NOT NULL` | Item description |
| `category` | `VARCHAR(100)` | `NOT NULL` | Product merchandise category |
| `brand` | `VARCHAR(100)` | `NOT NULL` | Manufacturer brand name |
| `unit_price` | `NUMERIC(10,2)` | `NOT NULL, CHECK (unit_price >= 0)` | Standard retail price |
| `updated_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Last SCD Type 1 update timestamp |

---

### 2.3 `dim_store`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `store_sk` | `BIGINT` | `PRIMARY KEY` | Auto-incrementing surrogate key |
| `store_id` | `VARCHAR(20)` | `NOT NULL, UNIQUE` | Store identifier (e.g. STR-001) |
| `store_name` | `VARCHAR(150)` | `NOT NULL` | Store location name |
| `region` | `VARCHAR(50)` | `NOT NULL` | Geographic region |
| `city` | `VARCHAR(100)` | `NOT NULL` | City name |
| `state` | `VARCHAR(2)` | `NOT NULL` | 2-character state code |
| `updated_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Last SCD Type 1 update timestamp |

---

### 2.4 `dim_employee`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `employee_sk` | `BIGINT` | `PRIMARY KEY` | Auto-incrementing surrogate key |
| `employee_id` | `VARCHAR(50)` | `NOT NULL, UNIQUE` | Natural employee code |
| `first_name` | `VARCHAR(100)` | `NOT NULL` | Employee first name |
| `last_name` | `VARCHAR(100)` | `NOT NULL` | Employee last name |
| `role` | `VARCHAR(50)` | `NOT NULL` | Job title / POS role |
| `store_id` | `VARCHAR(20)` | `NOT NULL` | Assigned home store ID |
| `updated_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Last update timestamp |

---

### 2.5 `fact_sales`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `sales_sk` | `BIGINT` | `PRIMARY KEY` | Auto-incrementing surrogate key |
| `transaction_id` | `VARCHAR(100)` | `NOT NULL` | POS transaction UUID |
| `customer_sk` | `BIGINT` | `FOREIGN KEY` | Refers to `dim_customer.customer_sk` |
| `product_sk` | `BIGINT` | `FOREIGN KEY` | Refers to `dim_product.product_sk` |
| `store_sk` | `BIGINT` | `FOREIGN KEY` | Refers to `dim_store.store_sk` |
| `employee_sk` | `BIGINT` | `FOREIGN KEY` | Refers to `dim_employee.employee_sk` |
| `transaction_time` | `TIMESTAMP` | `NOT NULL` | POS timestamp |
| `quantity` | `INT` | `CHECK (quantity > 0)` | Units purchased |
| `unit_price` | `NUMERIC(10,2)` | `CHECK (unit_price >= 0)` | Price per unit sold |
| `discount_amount` | `NUMERIC(10,2)` | `DEFAULT 0.00` | Discount applied |
| `net_sales_amount` | `NUMERIC(12,2)` | `NOT NULL` | `(quantity * unit_price) - discount_amount` |
| `audit_run_id` | `BIGINT` | `FOREIGN KEY` | Refers to `etl_audit_log.run_id` |
