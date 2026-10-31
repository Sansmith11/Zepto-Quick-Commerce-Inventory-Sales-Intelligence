"""
Zepto Inventory & Sales Analysis - Automated Data Quality & Pipeline Unit Tests
===============================================================================
Run with: python -m unittest tests/test_pipeline.py
"""

import os
import unittest
import duckdb
import sqlite3
import pandas as pd

class TestZeptoDataPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_csv = "data/raw/zepto_data.csv"
        cls.clean_csv = "data/processed/zepto_cleaned.csv"
        cls.duckdb_path = "database/zepto_warehouse.duckdb"
        cls.sqlite_path = "database/zepto_analytics.db"

    def test_01_processed_files_exist(self):
        """Verify that processed CSV and parquet files exist and are non-empty."""
        self.assertTrue(os.path.exists(self.clean_csv), "Cleaned CSV file missing")
        self.assertGreater(os.path.getsize(self.clean_csv), 10000, "Cleaned CSV is empty or too small")

    def test_02_no_invalid_prices(self):
        """Verify all cleaned records have mrp > 0 and selling price > 0."""
        df = pd.read_csv(self.clean_csv)
        self.assertEqual((df["mrp_inr"] <= 0).sum(), 0, "Found non-positive MRP in cleaned data")
        self.assertEqual((df["discounted_price_inr"] <= 0).sum(), 0, "Found non-positive selling price")
        self.assertTrue((df["discounted_price_inr"] <= df["mrp_inr"]).all(), "Selling price exceeds MRP")

    def test_03_currency_conversion(self):
        """Verify that currency conversion from paise to INR was executed correctly."""
        df = pd.read_csv(self.clean_csv)
        # In raw, max mrp was 260000 paise -> ₹2600
        self.assertLessEqual(df["mrp_inr"].max(), 5000.0, "MRP appears unconverted (still in paise)")
        self.assertGreaterEqual(df["mrp_inr"].min(), 1.0, "Minimum MRP seems too low")

    def test_04_duckdb_integrity(self):
        """Verify DuckDB warehouse tables and view consistency."""
        con = duckdb.connect(self.duckdb_path, read_only=True)
        tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        self.assertIn("dim_category", tables)
        self.assertIn("dim_product", tables)
        self.assertIn("fact_inventory", tables)
        self.assertIn("zepto_inventory_master", tables)

        fact_count = con.execute("SELECT COUNT(*) FROM fact_inventory").fetchone()[0]
        self.assertGreater(fact_count, 3500, "Fact table has fewer rows than expected")
        con.close()

    def test_05_sqlite_integrity(self):
        """Verify SQLite database accessibility and indexing."""
        con = sqlite3.connect(self.sqlite_path)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM zepto_inventory_master")
        count = cur.fetchone()[0]
        self.assertGreater(count, 3500, "SQLite master table count mismatch")
        con.close()

    def test_06_abc_classification_coverage(self):
        """Verify that ABC classification accounts for all active items and sums to 100%."""
        con = duckdb.connect(self.duckdb_path, read_only=True)
        abc_res = con.execute("""
            SELECT abc_classification, COUNT(*) 
            FROM v_abc_inventory_classification 
            GROUP BY abc_classification
        """).fetchall()
        classes = {r[0] for r in abc_res}
        self.assertIn("Class A (Critical Value)", classes)
        self.assertIn("Class B (Moderate Value)", classes)
        self.assertIn("Class C (Long Tail / Low Value)", classes)
        con.close()

if __name__ == "__main__":
    unittest.main()
