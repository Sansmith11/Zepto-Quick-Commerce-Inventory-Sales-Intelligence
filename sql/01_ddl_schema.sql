-- ============================================================================
-- 01_ddl_schema.sql
-- Zepto E-Commerce Enterprise Inventory & Sales Intelligence
-- Star Schema DDL (Compatible with PostgreSQL, DuckDB, SQLite)
-- ============================================================================

-- Drop existing tables if re-initializing
DROP TABLE IF EXISTS fact_inventory;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_category;
DROP TABLE IF EXISTS zepto_inventory_master;

-- ----------------------------------------------------------------------------
-- 1. Dimension: Product Categories
-- ----------------------------------------------------------------------------
CREATE TABLE dim_category (
    category_id INTEGER PRIMARY KEY,
    category_name VARCHAR(120) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. Dimension: Products Catalog (Normalized SKUs)
-- ----------------------------------------------------------------------------
CREATE TABLE dim_product (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES dim_category(category_id),
    weight_in_gms INTEGER NOT NULL CHECK (weight_in_gms >= 0),
    weight_tier VARCHAR(50) NOT NULL,
    price_tier VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 3. Fact Table: Dark Store Hyperlocal Inventory Snapshot
-- ----------------------------------------------------------------------------
CREATE TABLE fact_inventory (
    sku_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES dim_product(product_id),
    category_id INTEGER NOT NULL REFERENCES dim_category(category_id),
    mrp_inr NUMERIC(10, 2) NOT NULL CHECK (mrp_inr >= 0),
    discount_percent NUMERIC(5, 2) NOT NULL CHECK (discount_percent >= 0 AND discount_percent <= 100),
    discounted_price_inr NUMERIC(10, 2) NOT NULL CHECK (discounted_price_inr >= 0),
    discount_amount_inr NUMERIC(10, 2) NOT NULL,
    available_quantity INTEGER NOT NULL CHECK (available_quantity >= 0),
    out_of_stock BOOLEAN NOT NULL,
    inventory_holding_value_inr NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    estimated_stockout_loss_inr NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    weight_in_gms INTEGER NOT NULL,
    inventory_weight_kg NUMERIC(10, 3) NOT NULL DEFAULT 0.000,
    price_per_gram_inr NUMERIC(10, 4),
    revenue_density_per_kg NUMERIC(12, 2),
    snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 4. High-Performance Analytical Master Table (Denormalized)
-- ----------------------------------------------------------------------------
CREATE TABLE zepto_inventory_master (
    sku_id INTEGER PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(120) NOT NULL,
    category_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    mrp_paise BIGINT NOT NULL,
    discount_percent NUMERIC(5, 2) NOT NULL,
    available_quantity INTEGER NOT NULL,
    discounted_price_paise BIGINT NOT NULL,
    weight_in_gms INTEGER NOT NULL,
    out_of_stock BOOLEAN NOT NULL,
    pack_quantity INTEGER NOT NULL,
    mrp_inr NUMERIC(10, 2) NOT NULL,
    discounted_price_inr NUMERIC(10, 2) NOT NULL,
    discount_amount_inr NUMERIC(10, 2) NOT NULL,
    effective_discount_percent NUMERIC(5, 2) NOT NULL,
    inventory_holding_value_inr NUMERIC(12, 2) NOT NULL,
    mrp_inventory_value_inr NUMERIC(12, 2) NOT NULL,
    estimated_stockout_loss_inr NUMERIC(12, 2) NOT NULL,
    price_per_gram_inr NUMERIC(10, 4),
    revenue_density_per_kg NUMERIC(12, 2),
    inventory_weight_kg NUMERIC(10, 3) NOT NULL,
    weight_tier VARCHAR(50) NOT NULL,
    discount_tier VARCHAR(50) NOT NULL,
    price_tier VARCHAR(50) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 5. Performance Indexes
-- ----------------------------------------------------------------------------
CREATE INDEX idx_fact_prod_id ON fact_inventory(product_id);
CREATE INDEX idx_fact_cat_id ON fact_inventory(category_id);
CREATE INDEX idx_fact_stock_status ON fact_inventory(out_of_stock);
CREATE INDEX idx_master_category ON zepto_inventory_master(category);
CREATE INDEX idx_master_mrp ON zepto_inventory_master(mrp_inr);
CREATE INDEX idx_master_discount ON zepto_inventory_master(discount_percent);
