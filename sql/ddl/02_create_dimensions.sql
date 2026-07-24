-- ============================================================================
-- RetailFlow Data Warehouse - Dimension Tables (warehouse Schema)
-- Script: 02_create_dimensions.sql
-- Description: DDL for dim_date, dim_customer, dim_product, dim_store, dim_employee
-- ============================================================================

SET search_path TO warehouse, public;

-- ----------------------------------------------------------------------------
-- 1. dim_date (Date Dimension)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_sk         INT          PRIMARY KEY, -- YYYYMMDD integer key (e.g. 20260724)
    calendar_date   DATE         NOT NULL UNIQUE,
    year            INT          NOT NULL,
    quarter         INT          NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month           INT          NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_name      VARCHAR(20)  NOT NULL,
    week            INT          NOT NULL CHECK (week BETWEEN 1 AND 53),
    day             INT          NOT NULL CHECK (day BETWEEN 1 AND 31),
    day_name        VARCHAR(20)  NOT NULL,
    is_weekend      BOOLEAN      NOT NULL,
    fiscal_year     INT          NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2. dim_customer (Customer Dimension - SCD Type 1)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouse.dim_customer (
    customer_sk     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id     VARCHAR(50)  NOT NULL UNIQUE,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(255),
    phone           VARCHAR(30),
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 3. dim_product (Product Dimension - SCD Type 1)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouse.dim_product (
    product_sk      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id      VARCHAR(50)   NOT NULL UNIQUE,
    product_name    VARCHAR(255)  NOT NULL,
    category        VARCHAR(100)  NOT NULL,
    brand           VARCHAR(100)  NOT NULL,
    unit_price      NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0.00),
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 4. dim_store (Store Dimension - SCD Type 1)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouse.dim_store (
    store_sk        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    store_id        VARCHAR(20)  NOT NULL UNIQUE,
    store_name      VARCHAR(150) NOT NULL,
    region          VARCHAR(50)  NOT NULL,
    city            VARCHAR(100) NOT NULL,
    state           VARCHAR(2)   NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 5. dim_employee (Employee Dimension - SCD Type 1)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouse.dim_employee (
    employee_sk     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id     VARCHAR(50)  NOT NULL UNIQUE,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    role            VARCHAR(50)  NOT NULL,
    store_id        VARCHAR(20)  NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
