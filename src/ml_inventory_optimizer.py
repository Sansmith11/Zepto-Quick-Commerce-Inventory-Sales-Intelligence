"""
Zepto Inventory & Sales Analysis - Machine Learning & Inventory Optimization Module
===================================================================================
Features:
1. K-Means Clustering for Catalog Archetype Segmentation
2. Reorder Point (ROP) & Safety Stock Optimization Model
3. Price Elasticity & Margin Leakage Recovery Simulator
"""

import os
import duckdb
import pandas as pd
import numpy as np
import logging
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ZeptoMLOptimizer")

class ZeptoMLOptimizer:
    def __init__(self, db_path: str = "database/zepto_warehouse.duckdb"):
        self.db_path = db_path
        self.con = duckdb.connect(self.db_path)
        self.df = self.con.execute("SELECT * FROM zepto_inventory_master").df()

    def cluster_product_archetypes(self, n_clusters: int = 4) -> pd.DataFrame:
        """
        Segments SKUs into 4 retail archetypes using K-Means Clustering on:
        - discounted_price_inr
        - discount_percent
        - weight_in_gms
        - available_quantity
        """
        logger.info(f"Running K-Means Clustering with k={n_clusters}...")
        features = ["discounted_price_inr", "discount_percent", "weight_in_gms", "available_quantity"]
        data = self.df[features].copy()
        data = data.fillna(0)

        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(data)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.df["cluster_id"] = kmeans.fit_predict(scaled_features)

        # Profile the clusters
        cluster_profiles = self.df.groupby("cluster_id").agg(
            sku_count=("sku_id", "count"),
            avg_price=("discounted_price_inr", "mean"),
            avg_discount=("discount_percent", "mean"),
            avg_weight_gms=("weight_in_gms", "mean"),
            avg_stock_units=("available_quantity", "mean"),
            stockout_rate=("out_of_stock", lambda x: round(100 * x.mean(), 2))
        ).reset_index()

        # Archetype labeling based on cluster centers
        def label_archetype(row):
            if row["avg_weight_gms"] > 1000:
                return "Heavy Bulk Staples (Logistical Drag)"
            elif row["avg_price"] > 350:
                return "Premium High-Margin Anchors"
            elif row["avg_discount"] > 15:
                return "Promotional / Discount-Driven Items"
            else:
                return "High-Velocity Impulse & Essentials"

        cluster_profiles["archetype_name"] = cluster_profiles.apply(label_archetype, axis=1)
        archetype_map = dict(zip(cluster_profiles["cluster_id"], cluster_profiles["archetype_name"]))
        self.df["product_archetype"] = self.df["cluster_id"].map(archetype_map)

        logger.info(f"Clustering complete. Archetypes identified:\n{cluster_profiles[['cluster_id', 'archetype_name', 'sku_count', 'avg_price', 'avg_discount', 'avg_weight_gms']]}")
        return self.df, cluster_profiles

    def simulate_margin_recovery(self, discount_cut_pct: float = 3.0) -> dict:
        """
        Simulates margin recovery if over-discounted inelastic SKUs have discounts trimmed by discount_cut_pct.
        Focuses on items with discount > 15% and price > ₹200.
        """
        eligible = self.df[(self.df["discount_percent"] > 15.0) & (self.df["mrp_inr"] >= 200.0)].copy()
        
        # Additional revenue earned per item if discount is lowered
        additional_revenue_per_unit = eligible["mrp_inr"] * (discount_cut_pct / 100.0)
        total_margin_gain = (additional_revenue_per_unit * eligible["available_quantity"]).sum()

        result = {
            "eligible_skus_count": len(eligible),
            "current_holding_value_inr": round(eligible["inventory_holding_value_inr"].sum(), 2),
            "simulated_discount_cut_pct": discount_cut_pct,
            "projected_gross_margin_recovery_inr": round(total_margin_gain, 2),
            "margin_expansion_pct": round(100.0 * total_margin_gain / eligible["inventory_holding_value_inr"].sum(), 2)
        }
        logger.info(f"Margin recovery simulation: {result}")
        return result

    def simulate_safety_stock_rop(self) -> pd.DataFrame:
        """
        Calculates optimized Reorder Points (ROP) and recommended restock units
        for every active SKU in the dark store.
        """
        df_active = self.df[~self.df["out_of_stock"]].copy()

        # Categorical demand velocity multiplier
        def get_velocity_multiplier(cat):
            if cat in ["Dairy, Bread & Batter", "Fruits & Vegetables", "Meats, Fish & Eggs"]:
                return 2.5  # High daily churn
            elif cat in ["Munchies", "Beverages", "Ice Cream & Desserts"]:
                return 1.8  # Steady daily churn
            else:
                return 1.0  # Ambient/shelf-stable

        df_active["velocity_multiplier"] = df_active["category"].apply(get_velocity_multiplier)

        # Baseline estimated daily demand: available_quantity scaled by velocity
        df_active["est_daily_demand"] = np.maximum(1.0, np.round(df_active["available_quantity"] * 0.4 * df_active["velocity_multiplier"], 1))
        
        # Lead time in days (hyperlocal dark store = 0.5 days, i.e. 12 hours)
        lead_time_days = 0.5
        
        # Safety stock buffer
        df_active["safety_stock_units"] = np.ceil(df_active["est_daily_demand"] * 0.5).astype(int)
        
        # Reorder Point (ROP) = (Demand * Lead Time) + Safety Stock
        df_active["reorder_point_units"] = np.ceil((df_active["est_daily_demand"] * lead_time_days) + df_active["safety_stock_units"]).astype(int)
        
        # Need reorder flag
        df_active["trigger_reorder"] = df_active["available_quantity"] <= df_active["reorder_point_units"]
        
        # Recommended replenishment quantity to bring shelf up to capacity (max capacity = 6 units)
        df_active["recommended_reorder_qty"] = np.where(
            df_active["trigger_reorder"],
            np.maximum(0, 6 - df_active["available_quantity"]),
            0
        )

        return df_active

    def export_ml_results(self, output_dir: str = "reports"):
        """Saves enriched dataset with ML clusters and reorder triggers."""
        os.makedirs(output_dir, exist_ok=True)
        df_clustered, profiles = self.cluster_product_archetypes()
        df_clustered.to_csv(os.path.join(output_dir, "skus_with_ml_archetypes.csv"), index=False)
        profiles.to_csv(os.path.join(output_dir, "cluster_archetype_profiles.csv"), index=False)

        df_rop = self.simulate_safety_stock_rop()
        df_rop.to_csv(os.path.join(output_dir, "reorder_point_recommendations.csv"), index=False)
        logger.info(f"ML and Optimization results exported to {output_dir}")

    def close(self):
        self.con.close()

if __name__ == "__main__":
    optimizer = ZeptoMLOptimizer()
    optimizer.cluster_product_archetypes()
    optimizer.simulate_margin_recovery()
    optimizer.export_ml_results()
    optimizer.close()
