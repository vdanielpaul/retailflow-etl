-- ============================================================================
-- RetailFlow Data Warehouse - Fact Table (warehouse Schema)
-- Script: 03_create_fact_sales.sql
-- Description: DDL for fact_sales partitioned table in warehouse schema
-- ============================================================================

SET search_path TO warehouse, metadata, public;

CREATE TABLE IF NOT EXISTS warehouse.fact_sales (
    sales_sk            BIGINT GENERATED ALWAYS AS IDENTITY,
    transaction_id      VARCHAR(100)  NOT NULL,
    date_sk             INT           NOT NULL REFERENCES warehouse.dim_date(date_sk) ON DELETE RESTRICT,
    customer_sk         BIGINT        REFERENCES warehouse.dim_customer(customer_sk) ON DELETE RESTRICT,
    product_sk          BIGINT        NOT NULL REFERENCES warehouse.dim_product(product_sk) ON DELETE RESTRICT,
    store_sk            BIGINT        NOT NULL REFERENCES warehouse.dim_store(store_sk) ON DELETE RESTRICT,
    employee_sk         BIGINT        NOT NULL REFERENCES warehouse.dim_employee(employee_sk) ON DELETE RESTRICT,
    transaction_time    TIMESTAMP     NOT NULL,
    quantity            INT           NOT NULL CHECK (quantity > 0),
    unit_price          NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0.00),
    discount_amount     NUMERIC(10,2) NOT NULL DEFAULT 0.00 CHECK (discount_amount >= 0.00),
    net_sales_amount    NUMERIC(12,2) NOT NULL,
    audit_run_id        BIGINT,
    PRIMARY KEY (sales_sk, transaction_time)
) PARTITION BY RANGE (transaction_time);

-- ----------------------------------------------------------------------------
-- Create Default & Initial Partition Tables
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS warehouse.fact_sales_y2026m07 PARTITION OF warehouse.fact_sales
    FOR VALUES FROM ('2026-07-01 00:00:00') TO ('2026-08-01 00:00:00');

CREATE TABLE IF NOT EXISTS warehouse.fact_sales_y2026m08 PARTITION OF warehouse.fact_sales
    FOR VALUES FROM ('2026-08-01 00:00:00') TO ('2026-09-01 00:00:00');

CREATE TABLE IF NOT EXISTS warehouse.fact_sales_default PARTITION OF warehouse.fact_sales DEFAULT;
