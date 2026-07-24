-- ============================================================================
-- RetailFlow Data Warehouse - Performance Indexes
-- Script: 05_create_indexes.sql
-- Description: B-Tree & Composite Indexes for Star Schema Reporting Optimization
-- ============================================================================

SET search_path TO warehouse, metadata, public;

-- Composite Indexes on fact_sales for store & regional sales queries
CREATE INDEX IF NOT EXISTS idx_fact_sales_store_time
    ON warehouse.fact_sales (store_sk, transaction_time);

-- Composite Index on fact_sales for date dimension analytics
CREATE INDEX IF NOT EXISTS idx_fact_sales_date
    ON warehouse.fact_sales (date_sk);

-- Composite Index on fact_sales for product velocity & category reporting
CREATE INDEX IF NOT EXISTS idx_fact_sales_product_time
    ON warehouse.fact_sales (product_sk, transaction_time);

-- Index on fact_sales for customer purchasing analysis
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer
    ON warehouse.fact_sales (customer_sk);

-- Index on fact_sales for employee cashier shift analytics
CREATE INDEX IF NOT EXISTS idx_fact_sales_employee
    ON warehouse.fact_sales (employee_sk);

-- Index on etl_audit_log for fast SHA-256 duplicate file checking
CREATE INDEX IF NOT EXISTS idx_etl_audit_file_hash
    ON metadata.etl_audit_log (source_file_hash);
