# Enterprise Reporting Use Cases & BI Analytics

## Overview
This document details 10 realistic Business Intelligence (BI) use cases and SQL queries designed to demonstrate the analytical capabilities of the **RetailFlow Star Schema Data Warehouse**.

---

## 1. Daily Revenue by Store
**Business Context**: Operational dashboard tracking daily gross and net revenue generated per store location.
```sql
SELECT
    d.calendar_date,
    s.store_id,
    s.store_name,
    COUNT(DISTINCT f.transaction_id) AS total_orders,
    SUM(f.net_sales_amount) AS daily_revenue
FROM warehouse.fact_sales f
JOIN warehouse.dim_date d ON f.date_sk = d.date_sk
JOIN warehouse.dim_store s ON f.store_sk = s.store_sk
WHERE d.calendar_date = CURRENT_DATE - INTERVAL '1 day'
GROUP BY d.calendar_date, s.store_id, s.store_name
ORDER BY daily_revenue DESC;
```

---

## 2. Top 10 Selling Products by Volume & Revenue
**Business Context**: Inventory management reporting identifying high-velocity merchandise SKUs.
```sql
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(f.quantity) AS total_units_sold,
    SUM(f.net_sales_amount) AS total_revenue
FROM warehouse.fact_sales f
JOIN warehouse.dim_product p ON f.product_sk = p.product_sk
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_revenue DESC
LIMIT 10;
```

---

## 3. Monthly Sales Growth & Trend Analysis
**Business Context**: Executive finance reporting tracking month-over-month revenue velocity.
```sql
SELECT
    d.year,
    d.month,
    d.month_name,
    COUNT(DISTINCT f.transaction_id) AS order_volume,
    SUM(f.net_sales_amount) AS monthly_revenue
FROM warehouse.fact_sales f
JOIN warehouse.dim_date d ON f.date_sk = d.date_sk
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year DESC, d.month DESC;
```

---

## 4. Cashier & Employee Shift Sales Performance
**Business Context**: HR and store operations evaluating employee checkout throughput.
```sql
SELECT
    e.store_id,
    e.employee_id,
    e.first_name || ' ' || e.last_name AS employee_name,
    COUNT(DISTINCT f.transaction_id) AS transactions_processed,
    SUM(f.net_sales_amount) AS total_sales_generated
FROM warehouse.fact_sales f
JOIN warehouse.dim_employee e ON f.employee_sk = e.employee_sk
GROUP BY e.store_id, e.employee_id, employee_name
ORDER BY total_sales_generated DESC;
```

---

## 5. Customer Purchasing Frequency Analysis
**Business Context**: CRM loyalty team analyzing repeat customer purchase frequency.
```sql
SELECT
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    COUNT(DISTINCT f.transaction_id) AS lifetime_orders,
    SUM(f.net_sales_amount) AS lifetime_spend
FROM warehouse.fact_sales f
JOIN warehouse.dim_customer c ON f.customer_sk = c.customer_sk
GROUP BY c.customer_id, customer_name
HAVING COUNT(DISTINCT f.transaction_id) > 1
ORDER BY lifetime_spend DESC;
```

---

## 6. Weekend vs. Weekday Revenue Breakdown
**Business Context**: Staffing and promotional analysis evaluating weekend sales spikes.
```sql
SELECT
    d.is_weekend,
    COUNT(DISTINCT f.transaction_id) AS total_orders,
    SUM(f.net_sales_amount) AS total_revenue,
    ROUND(AVG(f.net_sales_amount), 2) AS avg_order_value
FROM warehouse.fact_sales f
JOIN warehouse.dim_date d ON f.date_sk = d.date_sk
GROUP BY d.is_weekend;
```

---

## 7. Revenue Performance by Region
**Business Context**: Regional Vice Presidents tracking sales distribution across geographic territories.
```sql
SELECT
    s.region,
    COUNT(DISTINCT s.store_id) AS store_count,
    SUM(f.net_sales_amount) AS regional_revenue,
    ROUND(SUM(f.net_sales_amount) / COUNT(DISTINCT s.store_id), 2) AS avg_revenue_per_store
FROM warehouse.fact_sales f
JOIN warehouse.dim_store s ON f.store_sk = s.store_sk
GROUP BY s.region
ORDER BY regional_revenue DESC;
```

---

## 8. Product Category Merchandise Velocity
**Business Context**: Category managers benchmarking category profitability.
```sql
SELECT
    p.category,
    COUNT(DISTINCT p.product_sk) AS distinct_products,
    SUM(f.quantity) AS total_units_sold,
    SUM(f.net_sales_amount) AS total_category_revenue
FROM warehouse.fact_sales f
JOIN warehouse.dim_product p ON f.product_sk = p.product_sk
GROUP BY p.category
ORDER BY total_category_revenue DESC;
```

---

## 9. Average Order Value (AOV) per Transaction Line Item
**Business Context**: Pricing strategy team evaluating basket sizes and discount impacts.
```sql
SELECT
    s.store_name,
    ROUND(AVG(f.net_sales_amount), 2) AS avg_line_item_value,
    SUM(f.discount_amount) AS total_discounts_given
FROM warehouse.fact_sales f
JOIN warehouse.dim_store s ON f.store_sk = s.store_sk
GROUP BY s.store_name
ORDER BY avg_line_item_value DESC;
```

---

## 10. Top 10 Revenue Generating Stores
**Business Context**: Operational leaderboard recognizing top revenue-generating retail outlets.
```sql
SELECT
    s.store_id,
    s.store_name,
    s.city,
    s.state,
    SUM(f.net_sales_amount) AS annual_store_revenue
FROM warehouse.fact_sales f
JOIN warehouse.dim_store s ON f.store_sk = s.store_sk
GROUP BY s.store_id, s.store_name, s.city, s.state
ORDER BY annual_store_revenue DESC
LIMIT 10;
```
