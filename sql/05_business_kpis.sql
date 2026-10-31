-- ============================================================================
-- 05_business_kpis.sql
-- Executive Business KPIs & Financial Performance Metrics
-- ============================================================================

-- ----------------------------------------------------------------------------
-- KPI 1: Executive Dark Store Summary Scorecard
-- High-level overview of portfolio valuation, assortment size, and health.
-- ----------------------------------------------------------------------------
SELECT 
    COUNT(sku_id) AS total_catalog_skus,
    COUNT(DISTINCT product_name) AS unique_products,
    COUNT(DISTINCT category) AS active_categories,
    SUM(CASE WHEN out_of_stock = FALSE THEN 1 ELSE 0 END) AS active_in_stock_skus,
    SUM(CASE WHEN out_of_stock = TRUE THEN 1 ELSE 0 END) AS out_of_stock_skus,
    ROUND(100.0 * SUM(CASE WHEN out_of_stock = TRUE THEN 1 ELSE 0 END) / COUNT(sku_id), 2) AS stockout_rate_pct,
    ROUND(SUM(inventory_holding_value_inr), 2) AS total_inventory_valuation_inr,
    ROUND(SUM(estimated_stockout_loss_inr), 2) AS total_potential_lost_gmv_inr,
    ROUND(AVG(discount_percent), 2) AS overall_avg_discount_pct,
    ROUND(SUM(inventory_weight_kg), 2) AS total_warehouse_stored_weight_kg
FROM zepto_inventory_master;

-- ----------------------------------------------------------------------------
-- KPI 2: Category Financial Performance Breakdown
-- Compares holding value, discount depth, stockout rates, and lost revenue.
-- ----------------------------------------------------------------------------
SELECT 
    category,
    COUNT(sku_id) AS total_skus,
    ROUND(100.0 * SUM(CASE WHEN out_of_stock = TRUE THEN 1 ELSE 0 END) / COUNT(sku_id), 2) AS stockout_rate_pct,
    ROUND(SUM(inventory_holding_value_inr), 2) AS total_holding_value_inr,
    ROUND(100.0 * SUM(inventory_holding_value_inr) / (SELECT SUM(inventory_holding_value_inr) FROM zepto_inventory_master), 2) AS pct_of_total_inventory_capital,
    ROUND(SUM(estimated_stockout_loss_inr), 2) AS potential_lost_revenue_inr,
    ROUND(AVG(discount_percent), 2) AS avg_discount_pct,
    ROUND(AVG(discounted_price_inr), 2) AS avg_realized_price_inr
FROM zepto_inventory_master
GROUP BY category
ORDER BY total_holding_value_inr DESC;

-- ----------------------------------------------------------------------------
-- KPI 3: Capital Allocation vs Warehouse Weight Disparity
-- Identifies categories that consume excessive physical storage but yield low capital value.
-- ----------------------------------------------------------------------------
SELECT 
    category,
    ROUND(SUM(inventory_holding_value_inr), 2) AS total_value_inr,
    ROUND(100.0 * SUM(inventory_holding_value_inr) / (SELECT SUM(inventory_holding_value_inr) FROM zepto_inventory_master), 2) AS value_share_pct,
    ROUND(SUM(inventory_weight_kg), 2) AS total_weight_kg,
    ROUND(100.0 * SUM(inventory_weight_kg) / (SELECT SUM(inventory_weight_kg) FROM zepto_inventory_master), 2) AS weight_share_pct,
    ROUND((100.0 * SUM(inventory_holding_value_inr) / (SELECT SUM(inventory_holding_value_inr) FROM zepto_inventory_master)) /
          NULLIF((100.0 * SUM(inventory_weight_kg) / (SELECT SUM(inventory_weight_kg) FROM zepto_inventory_master)), 0), 2) AS space_capital_efficiency_ratio
FROM zepto_inventory_master
GROUP BY category
ORDER BY space_capital_efficiency_ratio DESC;

-- ----------------------------------------------------------------------------
-- KPI 4: Discount Elasticity & Discount Band Performance
-- Evaluates assortment count and inventory capital across discount tiers.
-- ----------------------------------------------------------------------------
SELECT 
    discount_tier,
    COUNT(sku_id) AS sku_count,
    ROUND(100.0 * COUNT(sku_id) / (SELECT COUNT(*) FROM zepto_inventory_master), 2) AS sku_share_pct,
    ROUND(SUM(inventory_holding_value_inr), 2) AS total_value_inr,
    ROUND(AVG(mrp_inr), 2) AS avg_mrp_inr,
    ROUND(AVG(discounted_price_inr), 2) AS avg_selling_price_inr,
    ROUND(100.0 * SUM(CASE WHEN out_of_stock THEN 1 ELSE 0 END) / COUNT(sku_id), 2) AS stockout_rate_pct
FROM zepto_inventory_master
GROUP BY discount_tier
ORDER BY total_value_inr DESC;
