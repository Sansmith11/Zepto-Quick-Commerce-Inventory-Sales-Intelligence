-- ============================================================================
-- 04_advanced_analytics.sql
-- Advanced Real-World OLAP Queries & Window Functions
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Q1. Pareto Cumulative Revenue Contribution (80/20 Rule)
-- Computes running total and cumulative percentage of dark store inventory value.
-- ----------------------------------------------------------------------------
WITH ranked_skus AS (
    SELECT 
        sku_id,
        product_name,
        category,
        inventory_holding_value_inr,
        SUM(inventory_holding_value_inr) OVER () AS total_portfolio_value,
        SUM(inventory_holding_value_inr) OVER (
            ORDER BY inventory_holding_value_inr DESC, sku_id
        ) AS cumulative_holding_value
    FROM zepto_inventory_master
    WHERE out_of_stock = FALSE
)
SELECT 
    sku_id,
    product_name,
    category,
    inventory_holding_value_inr,
    ROUND(cumulative_holding_value, 2) AS cumulative_value_inr,
    ROUND(100.0 * cumulative_holding_value / total_portfolio_value, 2) AS cumulative_pct,
    CASE 
        WHEN (100.0 * cumulative_holding_value / total_portfolio_value) <= 70.0 THEN 'Class A (High Value)'
        WHEN (100.0 * cumulative_holding_value / total_portfolio_value) <= 90.0 THEN 'Class B (Medium Value)'
        ELSE 'Class C (Low Value / Long Tail)'
    END AS pareto_class
FROM ranked_skus
LIMIT 20;

-- ----------------------------------------------------------------------------
-- Q2. Top 3 Revenue-Driving SKUs per Category (Dense Rank Window Function)
-- Identifies category anchors that drive the bulk of store inventory investment.
-- ----------------------------------------------------------------------------
WITH category_sku_ranks AS (
    SELECT 
        category,
        product_name,
        discounted_price_inr,
        available_quantity,
        inventory_holding_value_inr,
        DENSE_RANK() OVER (
            PARTITION BY category 
            ORDER BY inventory_holding_value_inr DESC
        ) AS intra_category_rank
    FROM zepto_inventory_master
    WHERE out_of_stock = FALSE
)
SELECT 
    category,
    intra_category_rank,
    product_name,
    discounted_price_inr,
    available_quantity,
    inventory_holding_value_inr
FROM category_sku_ranks
WHERE intra_category_rank <= 3
ORDER BY category, intra_category_rank;

-- ----------------------------------------------------------------------------
-- Q3. Relative Price Index (RPI) vs Category Benchmark
-- Identifies premium vs economy SKUs by comparing selling price to category average.
-- ----------------------------------------------------------------------------
SELECT 
    sku_id,
    product_name,
    category,
    discounted_price_inr,
    ROUND(AVG(discounted_price_inr) OVER(PARTITION BY category), 2) AS category_avg_price,
    ROUND((discounted_price_inr / AVG(discounted_price_inr) OVER(PARTITION BY category)), 2) AS relative_price_index,
    CASE 
        WHEN discounted_price_inr > 1.5 * AVG(discounted_price_inr) OVER(PARTITION BY category) THEN 'Ultra-Premium (>1.5x avg)'
        WHEN discounted_price_inr < 0.6 * AVG(discounted_price_inr) OVER(PARTITION BY category) THEN 'Budget Saver (<0.6x avg)'
        ELSE 'Core Mid-Market'
    END AS price_positioning
FROM zepto_inventory_master
ORDER BY relative_price_index DESC
LIMIT 25;

-- ----------------------------------------------------------------------------
-- Q4. Margin Bleed Analysis: Over-Discounted High Ticket Items
-- Highlights expensive products (>₹400) given steep discounts (>20%), risking margin erosion.
-- ----------------------------------------------------------------------------
SELECT 
    sku_id,
    product_name,
    category,
    mrp_inr,
    discount_percent,
    discount_amount_inr,
    discounted_price_inr,
    ROUND(discount_amount_inr * available_quantity, 2) AS total_discount_given_inr
FROM zepto_inventory_master
WHERE mrp_inr >= 400.0 
  AND discount_percent >= 20.0
ORDER BY discount_amount_inr DESC
LIMIT 15;

-- ----------------------------------------------------------------------------
-- Q5. Category Breadth vs Depth Analysis
-- Evaluates assortment variety (unique products) vs depth (average available units per SKU).
-- ----------------------------------------------------------------------------
SELECT 
    category,
    COUNT(DISTINCT product_name) AS unique_product_assortment,
    COUNT(sku_id) AS total_sku_count,
    ROUND(1.0 * COUNT(sku_id) / COUNT(DISTINCT product_name), 2) AS sku_variant_ratio,
    ROUND(AVG(CASE WHEN out_of_stock = FALSE THEN available_quantity ELSE NULL END), 2) AS avg_stock_depth_per_active_sku,
    ROUND(SUM(inventory_holding_value_inr), 2) AS total_category_holding_value
FROM zepto_inventory_master
GROUP BY category
ORDER BY total_category_holding_value DESC;

-- ----------------------------------------------------------------------------
-- Q6. Price Deciles / Quartiles Distribution (NTILE Window Function)
-- Segments products into price quartiles within each category.
-- ----------------------------------------------------------------------------
SELECT 
    sku_id,
    product_name,
    category,
    discounted_price_inr,
    NTILE(4) OVER(PARTITION BY category ORDER BY discounted_price_inr) AS price_quartile,
    ROUND(PERCENT_RANK() OVER(PARTITION BY category ORDER BY discounted_price_inr) * 100, 1) AS category_percentile
FROM zepto_inventory_master
ORDER BY category, discounted_price_inr DESC
LIMIT 25;

-- ----------------------------------------------------------------------------
-- Q7. Dark Store Delivery Payload Optimization: Heavy vs High-Value Items
-- Delivery bags have strict weight limits (~12 kg). Find items with low revenue density.
-- ----------------------------------------------------------------------------
SELECT 
    sku_id,
    product_name,
    category,
    weight_in_gms,
    discounted_price_inr,
    revenue_density_per_kg,
    CASE 
        WHEN weight_in_gms >= 1000 AND revenue_density_per_kg < 150 THEN 'High Weight / Low Margin Burden'
        WHEN weight_in_gms <= 250 AND revenue_density_per_kg > 1000 THEN 'Ideal Quick-Commerce SKU (Light & High Value)'
        ELSE 'Balanced'
    END AS delivery_efficiency_tag
FROM zepto_inventory_master
WHERE weight_in_gms > 0
ORDER BY revenue_density_per_kg ASC
LIMIT 20;

-- ----------------------------------------------------------------------------
-- Q8. Stockout Impact & Lost Revenue Opportunity Ranking
-- Prioritizes which out-of-stock SKUs should be restocked first based on opportunity cost.
-- ----------------------------------------------------------------------------
SELECT 
    sku_id,
    product_name,
    category,
    mrp_inr,
    discounted_price_inr,
    estimated_stockout_loss_inr,
    DENSE_RANK() OVER(ORDER BY estimated_stockout_loss_inr DESC) AS overall_restock_priority,
    DENSE_RANK() OVER(PARTITION BY category ORDER BY estimated_stockout_loss_inr DESC) AS category_restock_priority
FROM zepto_inventory_master
WHERE out_of_stock = TRUE
ORDER BY overall_restock_priority ASC
LIMIT 15;
