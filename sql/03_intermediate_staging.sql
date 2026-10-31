-- ============================================================================
-- 03_intermediate_staging.sql
-- Dimensional Views and Intermediate Analytical Transformations
-- ============================================================================

-- ----------------------------------------------------------------------------
-- View 1: Category Health & Efficiency Metrics
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_category_health AS
SELECT 
    c.category_name,
    COUNT(f.sku_id) AS total_skus,
    SUM(CASE WHEN f.out_of_stock THEN 1 ELSE 0 END) AS oos_count,
    ROUND(100.0 * SUM(CASE WHEN f.out_of_stock THEN 1 ELSE 0 END) / COUNT(f.sku_id), 2) AS stockout_rate_pct,
    ROUND(AVG(f.discount_percent), 2) AS avg_discount_pct,
    ROUND(AVG(f.discounted_price_inr), 2) AS avg_selling_price_inr,
    ROUND(SUM(f.inventory_holding_value_inr), 2) AS total_inventory_value_inr,
    ROUND(SUM(f.estimated_stockout_loss_inr), 2) AS estimated_lost_revenue_inr,
    ROUND(SUM(f.inventory_weight_kg), 2) AS total_stored_weight_kg,
    ROUND(AVG(f.revenue_density_per_kg), 2) AS avg_rev_density_per_kg
FROM fact_inventory f
JOIN dim_category c ON f.category_id = c.category_id
GROUP BY c.category_name;

-- ----------------------------------------------------------------------------
-- View 2: Product Tier Distribution Matrix
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_product_tier_matrix AS
SELECT 
    p.price_tier,
    p.weight_tier,
    COUNT(f.sku_id) AS sku_count,
    ROUND(SUM(f.inventory_holding_value_inr), 2) AS total_value_inr,
    ROUND(AVG(f.discount_percent), 2) AS avg_discount_pct,
    ROUND(100.0 * SUM(CASE WHEN f.out_of_stock THEN 1 ELSE 0 END) / COUNT(f.sku_id), 2) AS stockout_pct
FROM fact_inventory f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.price_tier, p.weight_tier
ORDER BY total_value_inr DESC;

-- ----------------------------------------------------------------------------
-- View 3: Out of Stock Vulnerability Staging
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_oos_vulnerability AS
SELECT 
    m.sku_id,
    m.product_name,
    m.category,
    m.mrp_inr,
    m.discounted_price_inr,
    m.discount_percent,
    m.estimated_stockout_loss_inr,
    m.price_tier,
    NTILE(4) OVER(PARTITION BY m.category ORDER BY m.mrp_inr DESC) AS category_price_quartile
FROM zepto_inventory_master m
WHERE m.out_of_stock = TRUE;
