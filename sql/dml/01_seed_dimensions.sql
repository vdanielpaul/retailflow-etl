-- ============================================================================
-- RetailFlow Data Warehouse - Seed Reference Data
-- Script: 01_seed_dimensions.sql
-- Description: Inserts initial seed data for dim_store, dim_product, dim_customer, dim_employee
-- ============================================================================

-- 1. Seed Stores
INSERT INTO dim_store (store_id, store_name, region, city, state)
VALUES
    ('STR-001', 'Downtown Flagship', 'Northeast', 'New York', 'NY'),
    ('STR-002', 'West End Plaza', 'West', 'Los Angeles', 'CA'),
    ('STR-003', 'Northside Mall', 'Midwest', 'Chicago', 'IL'),
    ('STR-004', 'Metro Center', 'South', 'Houston', 'TX')
ON CONFLICT (store_id) DO NOTHING;

-- 2. Seed Products
INSERT INTO dim_product (product_id, product_name, category, brand, unit_price)
VALUES
    ('PROD-001', 'Wireless Noise-Canceling Headphones', 'Electronics', 'SoundPulse', 149.99),
    ('PROD-002', 'Organic Arabica Coffee Beans 1lb', 'Grocery', 'RoastCraft', 14.50),
    ('PROD-003', 'Ergonomic Mesh Office Chair', 'Furniture', 'ComfortLine', 219.00),
    ('PROD-004', 'Stainless Steel Water Bottle 32oz', 'Sports', 'HydroPeak', 24.99)
ON CONFLICT (product_id) DO NOTHING;

-- 3. Seed Customers
INSERT INTO dim_customer (customer_id, first_name, last_name, email, phone)
VALUES
    ('CUST-1001', 'Alice', 'Smith', 'alice.smith@example.com', '555-0101'),
    ('CUST-1002', 'Bob', 'Johnson', 'bob.johnson@example.com', '555-0102'),
    ('CUST-1003', 'Charlie', 'Davis', 'charlie.davis@example.com', '555-0103')
ON CONFLICT (customer_id) DO NOTHING;

-- 4. Seed Employees
INSERT INTO dim_employee (employee_id, first_name, last_name, role, store_id)
VALUES
    ('EMP-5001', 'David', 'Miller', 'Shift Lead', 'STR-001'),
    ('EMP-5002', 'Emma', 'Wilson', 'Cashier', 'STR-001'),
    ('EMP-5003', 'Frank', 'Taylor', 'Cashier', 'STR-002')
ON CONFLICT (employee_id) DO NOTHING;
