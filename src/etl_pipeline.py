"""
Zepto Inventory & Sales Analysis - Automated ETL & Dimensional Modeling
=======================================================================
Orchestrates:
1. Data Ingestion & Hygiene via ZeptoDataCleaner
2. Star Schema Dimensional Modeling (dim_category, dim_product, fact_inventory)
3. Dual-Database Materialization:
   - DuckDB (Embedded High-Performance Vectorized OLAP)
   - SQLite (Universal Relational Database for portability)
4. Creation of Analytical Views & Aggregations
"""

import os
import sqlite3
import duckdb
import logging
import pandas as pd
from data_cleaner import ZeptoDataCleaner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ZeptoETLPipeline")

class ZeptoETLPipeline:
    def __init__(
        self,
        raw_csv: str = "data/raw/zepto_data.csv",
        duckdb_path: str = "database/zepto_warehouse.duckdb",
        sqlite_path: str = "database/zepto_analytics.db"
    ):
        self.raw_csv = raw_csv
        self.duckdb_path = duckdb_path
        self.sqlite_path = sqlite_path
        os.makedirs(os.path.dirname(duckdb_path), exist_ok=True)

    def run_cleaner(self) -> pd.DataFrame:
        """Executes data cleaning and feature engineering."""
        cleaner = ZeptoDataCleaner(self.raw_csv)
        cleaner.audit_raw_data()
        df = cleaner.clean_and_transform()
        cleaner.export_processed_data()
        return df

    def build_dimensional_models(self, df: pd.DataFrame):
        """Constructs dimensional entities (Categories, Products, Inventory Fact)."""
        logger.info("Constructing Dimensional Data Models (Star Schema)...")

        # 1. Dim Category
        categories = sorted(df["category"].unique())
        dim_category = pd.DataFrame({
            "category_id": range(1, len(categories) + 1),
            "category_name": categories
        })

        cat_map = dict(zip(dim_category["category_name"], dim_category["category_id"]))
        df["category_id"] = df["category"].map(cat_map)

        # 2. Dim Product (Unique by name + category)
        unique_products = df.drop_duplicates(subset=["product_name", "category_id"]).copy()
        unique_products = unique_products.reset_index(drop=True)
        unique_products["product_id"] = range(1, len(unique_products) + 1)

        dim_product = unique_products[[
            "product_id", "product_name", "category_id", "weight_in_gms", "weight_tier", "price_tier"
        ]].copy()

        prod_map = dict(zip(
            zip(unique_products["product_name"], unique_products["category_id"]),
            unique_products["product_id"]
        ))

        df["product_id"] = [prod_map.get((p, c)) for p, c in zip(df["product_name"], df["category_id"])]

        # 3. Fact Inventory
        fact_inventory = df[[
            "sku_id", "product_id", "category_id", "mrp_inr", "discount_percent",
            "discounted_price_inr", "discount_amount_inr", "available_quantity",
            "out_of_stock", "inventory_holding_value_inr", "estimated_stockout_loss_inr",
            "weight_in_gms", "inventory_weight_kg", "price_per_gram_inr", "revenue_density_per_kg"
        ]].copy()

        logger.info(f"Dim Category created: {len(dim_category)} records")
        logger.info(f"Dim Product created: {len(dim_product)} records")
        logger.info(f"Fact Inventory created: {len(fact_inventory)} records")

        return dim_category, dim_product, fact_inventory, df

    def load_duckdb(self, dim_category, dim_product, fact_inventory, df_master):
        """Loads data into DuckDB warehouse and creates OLAP views."""
        logger.info(f"Connecting to DuckDB at: {self.duckdb_path}")
        con = duckdb.connect(self.duckdb_path)

        # Register and persist tables
        con.execute("CREATE OR REPLACE TABLE dim_category AS SELECT * FROM dim_category")
        con.execute("CREATE OR REPLACE TABLE dim_product AS SELECT * FROM dim_product")
        con.execute("CREATE OR REPLACE TABLE fact_inventory AS SELECT * FROM fact_inventory")
        con.execute("CREATE OR REPLACE TABLE zepto_inventory_master AS SELECT * FROM df_master")

        # Materialize Analytical View: Category Performance
        con.execute("""
        CREATE OR REPLACE VIEW v_category_performance AS
        SELECT 
            c.category_name,
            COUNT(f.sku_id) AS total_skus,
            COUNT(DISTINCT f.product_id) AS unique_products,
            SUM(CASE WHEN f.out_of_stock THEN 1 ELSE 0 END) AS out_of_stock_skus,
            ROUND(100.0 * SUM(CASE WHEN f.out_of_stock THEN 1 ELSE 0 END) / COUNT(f.sku_id), 2) AS stockout_rate_pct,
            ROUND(AVG(f.discount_percent), 2) AS avg_discount_pct,
            ROUND(AVG(f.mrp_inr), 2) AS avg_mrp_inr,
            ROUND(SUM(f.inventory_holding_value_inr), 2) AS total_holding_value_inr,
            ROUND(SUM(f.estimated_stockout_loss_inr), 2) AS estimated_lost_revenue_inr,
            ROUND(SUM(f.inventory_weight_kg), 2) AS total_weight_kg,
            ROUND(AVG(f.revenue_density_per_kg), 2) AS avg_revenue_density_per_kg
        FROM fact_inventory f
        JOIN dim_category c ON f.category_id = c.category_id
        GROUP BY c.category_name
        ORDER BY total_holding_value_inr DESC;
        """)

        # Materialize Analytical View: ABC Inventory Segmentation (Pareto 80/20)
        con.execute("""
        CREATE OR REPLACE VIEW v_abc_inventory_classification AS
        WITH sku_rev AS (
            SELECT 
                sku_id,
                product_name,
                category,
                mrp_inr,
                discounted_price_inr,
                available_quantity,
                inventory_holding_value_inr,
                SUM(inventory_holding_value_inr) OVER () AS total_portfolio_value,
                SUM(inventory_holding_value_inr) OVER (
                    ORDER BY inventory_holding_value_inr DESC, sku_id
                ) AS running_inventory_value
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
            ROUND(100.0 * running_inventory_value / total_portfolio_value, 2) AS cumulative_value_pct,
            CASE 
                WHEN (100.0 * running_inventory_value / total_portfolio_value) <= 70.0 THEN 'Class A (Critical Value)'
                WHEN (100.0 * running_inventory_value / total_portfolio_value) <= 90.0 THEN 'Class B (Moderate Value)'
                ELSE 'Class C (Long Tail / Low Value)'
            END AS abc_classification
        FROM sku_rev;
        """)

        # Materialize Analytical View: High-Priority Out of Stock Alert
        con.execute("""
        CREATE OR REPLACE VIEW v_stockout_critical_alerts AS
        SELECT 
            sku_id,
            product_name,
            category,
            mrp_inr,
            discount_percent,
            discounted_price_inr,
            estimated_stockout_loss_inr,
            DENSE_RANK() OVER(PARTITION BY category ORDER BY mrp_inr DESC) AS category_mrp_rank
        FROM zepto_inventory_master
        WHERE out_of_stock = TRUE
        ORDER BY estimated_stockout_loss_inr DESC;
        """)

        row_count = con.execute("SELECT COUNT(*) FROM fact_inventory").fetchone()[0]
        logger.info(f"DuckDB tables & views successfully materialized. Fact rows: {row_count}")
        con.close()

    def load_sqlite(self, dim_category, dim_product, fact_inventory, df_master):
        """Loads data into portable SQLite database."""
        logger.info(f"Connecting to SQLite at: {self.sqlite_path}")
        con = sqlite3.connect(self.sqlite_path)

        dim_category.to_sql("dim_category", con, if_exists="replace", index=False)
        dim_product.to_sql("dim_product", con, if_exists="replace", index=False)
        fact_inventory.to_sql("fact_inventory", con, if_exists="replace", index=False)
        df_master.to_sql("zepto_inventory_master", con, if_exists="replace", index=False)

        cursor = con.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_prod ON fact_inventory(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_cat ON fact_inventory(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_stock ON fact_inventory(out_of_stock)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_master_cat ON zepto_inventory_master(category)")
        con.commit()

        count = cursor.execute("SELECT COUNT(*) FROM zepto_inventory_master").fetchone()[0]
        logger.info(f"SQLite database successfully indexed and populated. Master rows: {count}")
        con.close()

    def run(self):
        """Full pipeline execution."""
        logger.info("=== STARTING FULL ZEPTO ETL PIPELINE ===")
        df_clean = self.run_cleaner()
        dim_cat, dim_prod, fact_inv, df_master = self.build_dimensional_models(df_clean)
        self.load_duckdb(dim_cat, dim_prod, fact_inv, df_master)
        self.load_sqlite(dim_cat, dim_prod, fact_inv, df_master)
        logger.info("=== ZEPTO ETL PIPELINE COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    pipeline = ZeptoETLPipeline()
    pipeline.run()
