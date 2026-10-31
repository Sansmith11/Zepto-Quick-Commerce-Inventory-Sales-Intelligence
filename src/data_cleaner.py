"""
Zepto Inventory & Sales Analysis - Data Cleaning & Hygiene Module
==================================================================
Handles raw CSV validation, anomaly detection, currency conversion (paise -> INR),
type coercion, and analytical feature engineering.
"""

import os
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ZeptoDataCleaner")

class ZeptoDataCleaner:
    def __init__(self, raw_filepath: str):
        self.raw_filepath = raw_filepath
        self.df_raw = None
        self.df_clean = None
        self.anomalies_report = {}

    def load_data(self) -> pd.DataFrame:
        """Loads raw CSV data."""
        if not os.path.exists(self.raw_filepath):
            raise FileNotFoundError(f"Raw data file not found at: {self.raw_filepath}")
        logger.info(f"Loading raw data from: {self.raw_filepath}")
        self.df_raw = pd.read_csv(self.raw_filepath)
        logger.info(f"Loaded {len(self.df_raw)} records with columns: {list(self.df_raw.columns)}")
        return self.df_raw

    def audit_raw_data(self) -> dict:
        """Audits anomalies before cleaning."""
        if self.df_raw is None:
            self.load_data()

        df = self.df_raw
        audit = {
            "total_rows": len(df),
            "missing_values": df.isnull().sum().to_dict(),
            "zero_mrp_count": int((df["mrp"] <= 0).sum()),
            "zero_selling_price_count": int((df["discountedSellingPrice"] <= 0).sum()),
            "zero_weight_count": int((df["weightInGms"] <= 0).sum()),
            "out_of_stock_count": int((df["outOfStock"] == True).sum()),
            "in_stock_count": int((df["outOfStock"] == False).sum()),
            "unique_categories": int(df["Category"].nunique()),
            "unique_skus": int(df["name"].nunique()),
        }
        self.anomalies_report = audit
        logger.info(f"Raw audit completed: {audit}")
        return audit

    def clean_and_transform(self) -> pd.DataFrame:
        """
        Cleans data and engineers analytical features:
        - Drops invalid records (mrp <= 0)
        - Converts paise to INR (mrp, discountedSellingPrice)
        - Generates synthetic SKU ID
        - Calculates discount amount and discount percentage accuracy
        - Categorizes weights and discount bands
        - Computes price per gram and stock values
        """
        if self.df_raw is None:
            self.load_data()

        df = self.df_raw.copy()

        # 1. Standardize column names
        df.columns = [c.strip() for c in df.columns]
        rename_map = {
            "Category": "category",
            "name": "product_name",
            "mrp": "mrp_paise",
            "discountPercent": "discount_percent",
            "availableQuantity": "available_quantity",
            "discountedSellingPrice": "discounted_price_paise",
            "weightInGms": "weight_in_gms",
            "outOfStock": "out_of_stock",
            "quantity": "pack_quantity"
        }
        df = df.rename(columns=rename_map)

        # 2. Filter out invalid rows (mrp <= 0 or corrupt price)
        initial_count = len(df)
        df = df[df["mrp_paise"] > 0].copy()
        dropped_count = initial_count - len(df)
        if dropped_count > 0:
            logger.warning(f"Dropped {dropped_count} rows with invalid MRP (<= 0).")

        # 3. Currency Conversion: Paise to INR
        df["mrp_inr"] = (df["mrp_paise"] / 100.0).round(2)
        df["discounted_price_inr"] = (df["discounted_price_paise"] / 100.0).round(2)
        df["discount_amount_inr"] = (df["mrp_inr"] - df["discounted_price_inr"]).round(2)

        # 4. Correct slight discount calculation mismatches
        computed_discount_pct = np.where(
            df["mrp_inr"] > 0,
            np.round(((df["mrp_inr"] - df["discounted_price_inr"]) / df["mrp_inr"]) * 100.0, 1),
            0.0
        )
        df["effective_discount_percent"] = computed_discount_pct

        # 5. Inventory Financials
        # Total value of currently held inventory
        df["inventory_holding_value_inr"] = (df["discounted_price_inr"] * df["available_quantity"]).round(2)
        df["mrp_inventory_value_inr"] = (df["mrp_inr"] * df["available_quantity"]).round(2)

        # Potential lost revenue for out-of-stock items (assume baseline demand depth of 4.5 units, store average)
        avg_depth = df[~df["out_of_stock"]]["available_quantity"].mean()
        df["estimated_stockout_loss_inr"] = np.where(
            df["out_of_stock"],
            np.round(df["discounted_price_inr"] * avg_depth, 2),
            0.0
        )

        # 6. Physical Logistics & Shelf Density
        # Safe price per gram (avoid division by 0)
        df["price_per_gram_inr"] = np.where(
            df["weight_in_gms"] > 0,
            np.round(df["discounted_price_inr"] / df["weight_in_gms"], 4),
            np.nan
        )
        
        # Revenue density: INR revenue per Kilogram of shelf space
        df["revenue_density_per_kg"] = np.where(
            df["weight_in_gms"] > 0,
            np.round((df["discounted_price_inr"] / df["weight_in_gms"]) * 1000.0, 2),
            np.nan
        )

        # Total held inventory weight in KG
        df["inventory_weight_kg"] = np.round((df["weight_in_gms"] * df["available_quantity"]) / 1000.0, 3)

        # 7. Tier Segmentations
        # Weight Class
        def categorize_weight(w):
            if w <= 100:
                return "Ultra-Light (<=100g)"
            elif w <= 500:
                return "Light (100g-500g)"
            elif w <= 2000:
                return "Medium (500g-2kg)"
            else:
                return "Bulk (>2kg)"

        df["weight_tier"] = df["weight_in_gms"].apply(categorize_weight)

        # Discount Class
        def categorize_discount(d):
            if d == 0:
                return "No Discount (0%)"
            elif d <= 10:
                return "Low Discount (1-10%)"
            elif d <= 25:
                return "Moderate Discount (11-25%)"
            else:
                return "Deep Discount (>25%)"

        df["discount_tier"] = df["discount_percent"].apply(categorize_discount)

        # Price Tier
        def categorize_price(p):
            if p < 50:
                return "Budget (< ₹50)"
            elif p <= 200:
                return "Everyday (₹50 - ₹200)"
            elif p <= 500:
                return "Premium (₹200 - ₹500)"
            else:
                return "Luxury / High Ticket (> ₹500)"

        df["price_tier"] = df["mrp_inr"].apply(categorize_price)

        # 8. Clean Product Names (strip trailing whitespace)
        df["product_name"] = df["product_name"].astype(str).str.strip()
        df["category"] = df["category"].astype(str).str.strip()

        # 9. Synthetic Primary Key
        df.insert(0, "sku_id", range(1, len(df) + 1))

        self.df_clean = df
        logger.info(f"Cleaning complete. Transformed records: {len(df)}")
        return self.df_clean

    def export_processed_data(self, output_dir: str = "data/processed"):
        """Exports processed data to CSV and Parquet."""
        if self.df_clean is None:
            self.clean_and_transform()

        os.makedirs(output_dir, exist_ok=True)
        csv_path = os.path.join(output_dir, "zepto_cleaned.csv")
        parquet_path = os.path.join(output_dir, "zepto_analytics.parquet")

        self.df_clean.to_csv(csv_path, index=False)
        self.df_clean.to_parquet(parquet_path, index=False)
        logger.info(f"Exported clean CSV: {csv_path} ({os.path.getsize(csv_path)} bytes)")
        logger.info(f"Exported Parquet: {parquet_path} ({os.path.getsize(parquet_path)} bytes)")
        return csv_path, parquet_path

if __name__ == "__main__":
    cleaner = ZeptoDataCleaner("data/raw/zepto_data.csv")
    cleaner.audit_raw_data()
    cleaner.clean_and_transform()
    cleaner.export_processed_data()
