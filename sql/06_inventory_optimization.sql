-- ============================================================================
-- 06_inventory_optimization.sql
-- Inventory Optimization: ABC Classification, Reorder Points & Safety Stock
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Full ABC Inventory Classification (70% Class A, 20% Class B, 10% Class C)
-- In quick-commerce, Class A SKUs must maintain 99.5% service levels (zero stockout tolerance).
-- ----------------------------------------------------------------------------
WITH ranked_inventory AS (
    SELECT 
        sku_id,
        product_name,
        category,
        mrp_inr,
        discounted_price_inr,
        available_quantity,
        inventory_holding_value_inr,
        SUM(inventory_holding_value_inr) OVER () AS grand_total_value,
        SUM(inventory_holding_value_inr) OVER (
            ORDER BY inventory_holding_value_inr DESC, sku_id
        ) AS cumulative_value
    FROM zepto_inventory_master
    WHERE out_of_stock = FALSE
),
abc_segmented AS (
    SELECT 
        *,
        ROUND(100.0 * cumulative_value / grand_total_value, 2) AS cumulative_share_pct,
        CASE 
            WHEN (100.0 * cumulative_value / grand_total_value) <= 70.0 THEN 'Class A'
            WHEN (100.0 * cumulative_value / grand_total_value) <= 90.0 THEN 'Class B'
            ELSE 'Class C'
        END AS abc_category
    FROM ranked_inventory
)
SELECT 
    abc_category,
    COUNT(sku_id) AS sku_count,
    ROUND(100.0 * COUNT(sku_id) / (SELECT COUNT(*) FROM abc_segmented), 2) AS pct_of_total_skus,
    ROUND(SUM(inventory_holding_value_inr), 2) AS total_value_inr,
    ROUND(100.0 * SUM(inventory_holding_value_inr) / (SELECT SUM(inventory_holding_value_inr) FROM abc_segmented), 2) AS pct_of_total_inventory_value,
    ROUND(AVG(discounted_price_inr), 2) AS avg_item_price_inr
FROM abc_segmented
GROUP BY abc_category
ORDER BY abc_category;

-- ----------------------------------------------------------------------------
-- 2. Dark Store Reorder Point (ROP) & Safety Stock Simulation
-- Formula: ROP = (Daily Demand * Lead Time Days) + Safety Stock
-- For quick-commerce dark store replenishment:
-- Lead time = 0.5 days (twice-a-day replenishment from central mother warehouse)
-- ----------------------------------------------------------------------------
SELECT 
    sku_id,
    product_name,
    category,
    available_quantity AS current_on_hand,
    CASE 
        WHEN category IN ('Dairy, Bread & Batter', 'Fruits & Vegetables', 'Meats, Fish & Eggs') THEN 'Perishable / High Velocity'
        WHEN category IN ('Munchies', 'Beverages', 'Ice Cream & Desserts') THEN 'Impulse / Medium-High Velocity'
        ELSE 'Ambient / Standard Velocity'
    END AS velocity_tier,
    -- Recommended Minimum Safety Stock
    CASE 
        WHEN category IN ('Dairy, Bread & Batter', 'Fruits & Vegetables') THEN 4
        WHEN category IN ('Cooking Essentials', 'Munchies') THEN 5
        ELSE 2
    END AS recommended_safety_stock,
    -- Reorder Action Signal
    CASE 
        WHEN available_quantity <= 1 THEN 'CRITICAL: Reorder Immediately'
        WHEN available_quantity <= 3 THEN 'WARNING: Approaching Reorder Point'
        ELSE 'HEALTHY: Sufficient Stock'
    END AS inventory_health_status
FROM zepto_inventory_master
WHERE out_of_stock = FALSE
ORDER BY current_on_hand ASC, inventory_holding_value_inr DESC
LIMIT 25;

-- ----------------------------------------------------------------------------
-- 3. Stockout Root-Cause & Loss Recovery Priority Score
-- Scores out-of-stock items based on lost revenue and category importance.
-- ----------------------------------------------------------------------------
SELECT 
    sku_id,
    product_name,
    category,
    mrp_inr,
    discounted_price_inr,
    estimated_stockout_loss_inr,
    ROUND((estimated_stockout_loss_inr / (SELECT SUM(estimated_stockout_loss_inr) FROM zepto_inventory_master WHERE out_of_stock = TRUE)) * 100.0, 3) AS lost_revenue_contribution_pct,
    CASE 
        WHEN estimated_stockout_loss_inr >= 2000 THEN 'P0 - Urgent Replenishment (High Lost Value)'
        WHEN estimated_stockout_loss_inr >= 1000 THEN 'P1 - High Priority'
        WHEN estimated_stockout_loss_inr >= 500  THEN 'P2 - Medium Priority'
        ELSE 'P3 - Low Priority'
    END AS replenishment_urgency
FROM zepto_inventory_master
WHERE out_of_stock = TRUE
ORDER BY estimated_stockout_loss_inr DESC
LIMIT 20;
