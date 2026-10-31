"""
Zepto Inventory & Sales Analysis - Advanced Analytics Engine
============================================================
Performs advanced quantitative analytics, Pareto ABC classification,
financial metric calculations, and automated summary reporting.
"""

import os
import duckdb
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ZeptoAdvancedAnalytics")

class ZeptoAdvancedAnalytics:
    def __init__(self, db_path: str = "database/zepto_warehouse.duckdb"):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"DuckDB database not found at {self.db_path}. Run ETL pipeline first.")
        self.con = duckdb.connect(self.db_path)

    def get_executive_summary(self) -> dict:
        """Computes top-level executive KPIs."""
        query = """
        SELECT 
            COUNT(sku_id) AS total_skus,
            COUNT(DISTINCT product_name) AS unique_products,
            COUNT(DISTINCT category) AS total_categories,
            SUM(CASE WHEN out_of_stock = FALSE THEN 1 ELSE 0 END) AS in_stock_skus,
            SUM(CASE WHEN out_of_stock = TRUE THEN 1 ELSE 0 END) AS out_of_stock_skus,
            ROUND(100.0 * SUM(CASE WHEN out_of_stock = TRUE THEN 1 ELSE 0 END) / COUNT(sku_id), 2) AS stockout_rate_pct,
            ROUND(SUM(inventory_holding_value_inr), 2) AS total_holding_value_inr,
            ROUND(SUM(estimated_stockout_loss_inr), 2) AS total_lost_revenue_inr,
            ROUND(AVG(discount_percent), 2) AS avg_discount_pct,
            ROUND(AVG(discounted_price_inr), 2) AS avg_selling_price_inr,
            ROUND(SUM(inventory_weight_kg), 2) AS total_weight_kg
        FROM zepto_inventory_master;
        """
        res = self.con.execute(query).df().to_dict(orient="records")[0]
        logger.info(f"Executive Summary computed: {res}")
        return res

    def get_category_breakdown(self) -> pd.DataFrame:
        """Computes comprehensive metrics per product category."""
        query = """
        SELECT 
            category,
            COUNT(sku_id) AS total_skus,
            SUM(CASE WHEN out_of_stock THEN 1 ELSE 0 END) AS out_of_stock_skus,
            ROUND(100.0 * SUM(CASE WHEN out_of_stock THEN 1 ELSE 0 END) / COUNT(sku_id), 2) AS stockout_rate_pct,
            ROUND(SUM(inventory_holding_value_inr), 2) AS total_holding_value_inr,
            ROUND(100.0 * SUM(inventory_holding_value_inr) / (SELECT SUM(inventory_holding_value_inr) FROM zepto_inventory_master), 2) AS value_share_pct,
            ROUND(SUM(estimated_stockout_loss_inr), 2) AS estimated_lost_revenue_inr,
            ROUND(AVG(discount_percent), 2) AS avg_discount_pct,
            ROUND(AVG(discounted_price_inr), 2) AS avg_price_inr,
            ROUND(SUM(inventory_weight_kg), 2) AS total_weight_kg,
            ROUND(AVG(revenue_density_per_kg), 2) AS avg_revenue_density_per_kg
        FROM zepto_inventory_master
        GROUP BY category
        ORDER BY total_holding_value_inr DESC;
        """
        return self.con.execute(query).df()

    def get_abc_classification(self) -> pd.DataFrame:
        """
        Computes ABC classification based on inventory holding value:
        - Class A: Top 70% of inventory value
        - Class B: Next 20% of inventory value (70% - 90%)
        - Class C: Remaining 10% of inventory value (90% - 100%)
        """
        query = """
        WITH ranked AS (
            SELECT 
                sku_id,
                product_name,
                category,
                mrp_inr,
                discounted_price_inr,
                available_quantity,
                inventory_holding_value_inr,
                SUM(inventory_holding_value_inr) OVER() AS grand_total,
                SUM(inventory_holding_value_inr) OVER(
                    ORDER BY inventory_holding_value_inr DESC, sku_id
                ) AS running_val
            FROM zepto_inventory_master
            WHERE out_of_stock = FALSE
        )
        SELECT 
            sku_id,
            product_name,
            category,
            mrp_inr,
            discounted_price_inr,
            available_quantity,
            inventory_holding_value_inr,
            ROUND(100.0 * running_val / grand_total, 2) AS cumulative_pct,
            CASE 
                WHEN (100.0 * running_val / grand_total) <= 70.0 THEN 'Class A'
                WHEN (100.0 * running_val / grand_total) <= 90.0 THEN 'Class B'
                ELSE 'Class C'
            END AS abc_class
        FROM ranked;
        """
        return self.con.execute(query).df()

    def get_abc_summary(self) -> pd.DataFrame:
        """Aggregates ABC classification summary metrics."""
        df_abc = self.get_abc_classification()
        summary = df_abc.groupby("abc_class").agg(
            sku_count=("sku_id", "count"),
            total_value_inr=("inventory_holding_value_inr", "sum"),
            avg_price_inr=("discounted_price_inr", "mean"),
            avg_stock_units=("available_quantity", "mean")
        ).reset_index()

        total_skus = len(df_abc)
        total_val = summary["total_value_inr"].sum()
        summary["pct_of_skus"] = (100.0 * summary["sku_count"] / total_skus).round(2)
        summary["pct_of_value"] = (100.0 * summary["total_value_inr"] / total_val).round(2)
        summary["total_value_inr"] = summary["total_value_inr"].round(2)
        summary["avg_price_inr"] = summary["avg_price_inr"].round(2)
        summary["avg_stock_units"] = summary["avg_stock_units"].round(2)
        return summary.sort_values("abc_class")

    def get_stockout_loss_ranking(self, limit: int = 25) -> pd.DataFrame:
        """Ranks out-of-stock items by estimated lost revenue."""
        query = f"""
        SELECT 
            sku_id,
            product_name,
            category,
            mrp_inr,
            discount_percent,
            discounted_price_inr,
            estimated_stockout_loss_inr,
            price_tier,
            weight_tier
        FROM zepto_inventory_master
        WHERE out_of_stock = TRUE
        ORDER BY estimated_stockout_loss_inr DESC
        LIMIT {limit};
        """
        return self.con.execute(query).df()

    def get_payload_efficiency(self) -> pd.DataFrame:
        """Analyzes dark store shelf space & delivery bag weight efficiency."""
        query = """
        SELECT 
            category,
            ROUND(SUM(inventory_weight_kg), 2) AS total_weight_kg,
            ROUND(SUM(inventory_holding_value_inr), 2) AS total_value_inr,
            ROUND(AVG(revenue_density_per_kg), 2) AS avg_revenue_per_kg,
            ROUND(SUM(inventory_holding_value_inr) / NULLIF(SUM(inventory_weight_kg), 0), 2) AS effective_value_density_ratio
        FROM zepto_inventory_master
        WHERE weight_in_gms > 0 AND out_of_stock = FALSE
        GROUP BY category
        ORDER BY effective_value_density_ratio DESC;
        """
        return self.con.execute(query).df()

    def export_all_reports(self, output_dir: str = "reports"):
        """Exports analytical tables as CSV for automated business reporting."""
        os.makedirs(output_dir, exist_ok=True)
        cat_df = self.get_category_breakdown()
        cat_df.to_csv(os.path.join(output_dir, "category_performance_report.csv"), index=False)

        abc_df = self.get_abc_summary()
        abc_df.to_csv(os.path.join(output_dir, "abc_inventory_summary.csv"), index=False)

        oos_df = self.get_stockout_loss_ranking(100)
        oos_df.to_csv(os.path.join(output_dir, "stockout_loss_ranking.csv"), index=False)

        payload_df = self.get_payload_efficiency()
        payload_df.to_csv(os.path.join(output_dir, "darkstore_payload_efficiency.csv"), index=False)
        logger.info(f"Analytical reports successfully saved to: {output_dir}")

    def close(self):
        self.con.close()

if __name__ == "__main__":
    analytics = ZeptoAdvancedAnalytics()
    summary = analytics.get_executive_summary()
    print("=== EXECUTIVE SUMMARY ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print("\n=== CATEGORY PERFORMANCE ===")
    print(analytics.get_category_breakdown().head(5))
    print("\n=== ABC INVENTORY SUMMARY ===")
    print(analytics.get_abc_summary())
    analytics.export_all_reports()
    analytics.close()
