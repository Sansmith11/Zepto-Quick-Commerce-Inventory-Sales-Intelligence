-- ============================================================================
-- 02_data_cleaning_audit.sql
-- Advanced SQL Data Quality Audit & Hygiene Checks
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Audit Check 1: Zero or Negative Price Inconsistencies
-- In quick-commerce, free items or scraping errors must be flagged.
-- ----------------------------------------------------------------------------
SELECT 
    sku_id,
    product_name,
    category,
    mrp_inr,
    discounted_price_inr,
    CASE 
        WHEN mrp_inr <= 0 THEN 'Corrupt MRP'
        WHEN discounted_price_inr <= 0 THEN 'Corrupt Selling Price'
        WHEN discounted_price_inr > mrp_inr THEN 'Selling Price Greater than MRP'
        ELSE 'Valid'
    END AS price_integrity_status
FROM zepto_inventory_master
WHERE mrp_inr <= 0 
   OR discounted_price_inr <= 0 
   OR discounted_price_inr > mrp_inr;

-- ----------------------------------------------------------------------------
-- Audit Check 2: Discount Calculation Discrepancies
-- Flag records where advertised discount differs significantly from computed discount.
-- ----------------------------------------------------------------------------
SELECT 
    sku_id,
    product_name,
    category,
    mrp_inr,
    discounted_price_inr,
    discount_percent AS advertised_discount_pct,
    ROUND(((mrp_inr - discounted_price_inr) / mrp_inr) * 100.0, 1) AS computed_discount_pct,
    ROUND(ABS(discount_percent - (((mrp_inr - discounted_price_inr) / mrp_inr) * 100.0)), 1) AS discount_discrepancy
FROM zepto_inventory_master
WHERE mrp_inr > 0 
  AND ROUND(ABS(discount_percent - (((mrp_inr - discounted_price_inr) / mrp_inr) * 100.0)), 1) > 2.0
ORDER BY discount_discrepancy DESC
LIMIT 15;

-- ----------------------------------------------------------------------------
-- Audit Check 3: Multi-SKU Variant Distribution
-- Identify products appearing across multiple pack sizes or weights.
-- ----------------------------------------------------------------------------
WITH sku_counts AS (
    SELECT 
        product_name,
        category,
        COUNT(sku_id) AS sku_variant_count,
        MIN(weight_in_gms) AS min_weight_gms,
        MAX(weight_in_gms) AS max_weight_gms,
        MIN(discounted_price_inr) AS min_price_inr,
        MAX(discounted_price_inr) AS max_price_inr
    FROM zepto_inventory_master
    GROUP BY product_name, category
    HAVING COUNT(sku_id) > 1
)
SELECT *
FROM sku_counts
ORDER BY sku_variant_count DESC, max_price_inr DESC
LIMIT 15;

-- ----------------------------------------------------------------------------
-- Audit Check 4: Stock Status & Quantity Integrity Check
-- Ensure out_of_stock boolean matches available_quantity = 0.
-- ----------------------------------------------------------------------------
SELECT 
    out_of_stock,
    COUNT(*) AS total_items,
    MIN(available_quantity) AS min_quantity,
    MAX(available_quantity) AS max_quantity,
    AVG(available_quantity) AS avg_quantity
FROM zepto_inventory_master
GROUP BY out_of_stock;

-- ----------------------------------------------------------------------------
-- Audit Check 5: Statistical Outliers in Price per Gram using SQL IQR
-- ----------------------------------------------------------------------------
WITH quartiles AS (
    SELECT 
        category,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_per_gram_inr) AS q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_per_gram_inr) AS q3
    FROM zepto_inventory_master
    WHERE price_per_gram_inr IS NOT NULL AND price_per_gram_inr > 0
    GROUP BY category
)
SELECT 
    m.sku_id,
    m.product_name,
    m.category,
    m.discounted_price_inr,
    m.weight_in_gms,
    m.price_per_gram_inr,
    ROUND(q.q1, 4) AS category_q1,
    ROUND(q.q3, 4) AS category_q3,
    ROUND(q.q3 + 1.5 * (q.q3 - q.q1), 4) AS upper_bound
FROM zepto_inventory_master m
JOIN quartiles q ON m.category = q.category
WHERE m.price_per_gram_inr > (q.q3 + 1.5 * (q.q3 - q.q1))
ORDER BY m.price_per_gram_inr DESC
LIMIT 10;
