-- ============================================================================
-- RetailFlow Data Warehouse - Analytical Validation Queries
-- Script: 02_sample_queries.sql
-- Description: Business queries demonstrating Star Schema aggregation performance
-- ============================================================================

-- Query 1: Total Revenue and Net Sales by Store Region (Monthly)
SELECT
    s.region,
    s.store_name,
    COUNT(DISTINCT f.transaction_id) AS total_transactions,
    SUM(f.quantity) AS total_units_sold,
    SUM(f.net_sales_amount) AS total_net_revenue,
    ROUND(AVG(f.net_sales_amount), 2) AS avg_transaction_line_value
FROM fact_sales f
JOIN dim_store s ON f.store_sk = s.store_sk
GROUP BY s.region, s.store_name
ORDER BY total_net_revenue DESC;

-- Query 2: Top 5 Selling Products by Category
SELECT
    p.category,
    p.product_name,
    SUM(f.quantity) AS total_quantity_sold,
    SUM(f.net_sales_amount) AS category_revenue
FROM fact_sales f
JOIN dim_product p ON f.product_sk = p.product_sk
GROUP BY p.category, p.product_name
ORDER BY category_revenue DESC
LIMIT 5;

-- Query 3: ETL Audit & Rejection Metrics Summary
SELECT
    pipeline_name,
    status,
    COUNT(*) AS total_runs,
    SUM(rows_read) AS aggregate_rows_read,
    SUM(rows_loaded) AS aggregate_rows_loaded,
    SUM(rows_rejected) AS aggregate_rows_rejected,
    ROUND(AVG(duration_seconds), 3) AS avg_run_duration_sec
FROM etl_audit_log
GROUP BY pipeline_name, status;
