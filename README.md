#  Zepto Quick-Commerce Inventory & Sales Intelligence Platform
### Advanced End-to-End Data Engineering, OLAP Analytics, Machine Learning & Interactive BI Web Application

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg?logo=python&logoColor=white)](https://python.org)
[![DuckDB](https://img.shields.io/badge/Engine-DuckDB%20OLAP-yellow.svg?logo=duckdb&logoColor=white)](https://duckdb.org)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg?logo=sqlite&logoColor=white)](https://sqlite.org)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-000000.svg)](https://github.com/psf/black)
[![Tests](https://img.shields.io/badge/Tests-Passing%20(6%2F6)-brightgreen.svg)]()

---

##  Project Overview

This project elevates a traditional SQL analysis repository into an **enterprise-grade, production-ready Quick-Commerce Data Intelligence Platform** modeled on **Zepto**, India’s leading 10-minute grocery delivery startup.

Operating in quick-commerce requires extreme operational discipline: dark stores (micro-warehouses) maintain limited shelf space (typically 1–6 units per SKU), tight delivery partner payload limits (~10–12 kg per bike), and ruthless service level requirements where stockouts directly cause immediate customer churn to competitors.

This platform bridges the entire modern data lifecycle:
1. **Automated ETL & Data Hygiene Pipeline**: Validates raw scraped inventory records, converts legacy currencies (paise to INR ₹), scrubs data anomalies, and builds production Star Schema models.
2. **High-Performance Dual-Database Architecture**: Powered by **DuckDB** (columnar vectorized OLAP warehouse) and **SQLite** (portable indexed relational database).
3. **Advanced SQL OLAP Suite**: 25+ real-world production queries utilizing Window Functions (`ROW_NUMBER`, `DENSE_RANK`, `NTILE`, `PERCENT_RANK`), CTEs, and cumulative Pareto running totals.
4. **Machine Learning & Inventory Optimization**: Unsupervised K-Means clustering of catalog archetypes, dynamic Reorder Point (ROP) & Safety Stock models, and price elasticity margin recovery simulations.
5. **Interactive Executive BI Web Application**: Full-featured **Streamlit** dashboard with real-time scenario modeling, Plotly visualizations, and an in-browser live SQL execution workbench.

---

##  Executive Business Scorecard (Dark Store Snapshot)

| Metric | Measured Value | Business Interpretation |
| :--- | :--- | :--- |
| **Total Catalog SKUs** | **3,731 SKUs** | 1,673 unique products across 14 categories |
| **Total Active Inventory Capital** | **₹22,43,080.60** | ₹22.43 Lakhs held in shelf inventory |
| **Out-of-Stock (OOS) Rate** | **12.14% (453 SKUs)** | Significant stockout risk in high-velocity categories |
| **Estimated Stockout Revenue Loss** | **₹1,78,058.90** | Unfulfilled demand lost due to empty dark store shelves |
| **Class A SKUs (Pareto)** | **1,129 SKUs (34.4%)** | Drives **70.0% of total inventory value** (₹15.7 Lakhs) |
| **Total Stored Weight** | **6,005.85 kg (6.0 tonnes)** | Constrains shelf capacity and 2-wheeler courier payloads |
| **Projected Margin Expansion** | **+₹10,183.98 / cycle** | Achieved by trimming discounts by 3% on 180 luxury items |

---

##  System Architecture

```
                      +-----------------------------+
                      |      Raw Source Layer       |
                      |  zepto_data.csv (Kaggle)    |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Data Cleaning & Feature Eng |
                      |    (src/data_cleaner.py)    |
                      |  - Paise to INR conversion  |
                      |  - Anomaly & Zero-MRP audit |
                      |  - Revenue density & tiers  |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   Automated ETL Pipeline    |
                      |   (src/etl_pipeline.py)     |
                      |   - Star Schema Generation  |
                      +--------------+--------------+
                                     |
             +-----------------------+-----------------------+
             |                                               |
             v                                               v
+---------------------------+                   +---------------------------+
|    DuckDB Vector Engine   |                   |    SQLite Relational DB   |
| (zepto_warehouse.duckdb)  |                   |   (zepto_analytics.db)    |
| - Ultra-fast columnar OLAP|                   | - Portable standard SQL   |
| - Analytical views & CTEs |                   | - B-Tree indexed queries  |
+-------------+-------------+                   +-------------+-------------+
              |                                               |
              +-----------------------+-----------------------+
                                      |
                                      v
                      +-----------------------------+
                      | Advanced Analytics & ML     |
                      | (src/advanced_analytics.py) |
                      | (ml_inventory_optimizer.py) |
                      | - ABC Pareto Classification |
                      | - K-Means Archetypes (k=4)  |
                      | - Reorder Point Simulator   |
                      +--------------+--------------+
                                     |
             +-----------------------+-----------------------+
             |                                               |
             v                                               v
+---------------------------+                   +---------------------------+
|  Interactive Streamlit BI |                   |  Automated Visualizations |
|    (dashboard/app.py)     |                   | (reports/figures/)        |
| - Executive Scorecards    |                   | - 6 Publication PNGs      |
| - Live SQL Workbench      |                   | - CSV Analytical Exports  |
| - Real-time scenario Sims |                   |                           |
+---------------------------+                   +---------------------------+
```

---

##  Repository Structure

```
Zepto-Inventory-And-Sales-Analysis/
│
├── data/
│   ├── raw/
│   │   └── zepto_data.csv                    # Raw scraped catalog dataset
│   └── processed/
│       ├── zepto_cleaned.csv                 # Cleaned dataset (INR, validated)
│       └── zepto_analytics.parquet           # Columnar analytics dataset
│
├── database/
│   ├── zepto_warehouse.duckdb                # DuckDB embedded analytical warehouse
│   └── zepto_analytics.db                    # Indexed SQLite database
│
├── sql/
│   ├── 01_ddl_schema.sql                     # Production Star Schema DDL & indexes
│   ├── 02_data_cleaning_audit.sql            # SQL data hygiene, anomalies & IQR outliers
│   ├── 03_intermediate_staging.sql           # Materialized views & staging transformations
│   ├── 04_advanced_analytics.sql             # 12+ real-world queries (Window functions, CTEs)
│   ├── 05_business_kpis.sql                  # Executive scorecards, GMV & margin bleed
│   └── 06_inventory_optimization.sql         # ABC Classification, ROP & Safety Stock
│
├── src/
│   ├── data_cleaner.py                       # Data hygiene, validation & feature engineering
│   ├── etl_pipeline.py                       # Automated Star Schema builder & loader
│   ├── advanced_analytics.py                 # Quantitative metrics & automated reporting
│   └── ml_inventory_optimizer.py             # K-Means clustering & safety stock simulator
│
├── dashboard/
│   └── app.py                                # Interactive Streamlit BI Web Application
│
├── notebooks/
│   └── zepto_advanced_eda.py                 # Automated chart generation script
│
├── reports/
│   ├── figures/                              # High-resolution generated charts (PNG)
│   ├── category_performance_report.csv       # Category financial breakdown
│   ├── abc_inventory_summary.csv             # ABC classification distribution
│   └── stockout_loss_ranking.csv             # Prioritized restock table
│
├── tests/
│   └── test_pipeline.py                      # Automated data quality & schema unit tests
│
├── docs/
│   ├── DATA_DICTIONARY.md                    # Column descriptions & metric formulas
│   ├── BUSINESS_INSIGHTS.md                  # Executive findings & strategic action plan
│   └── ARCHITECTURE.md                       # Technical stack & architecture details
│
├── requirements.txt                          # Pinned project dependencies
├── run_project.py                            # Master CLI orchestrator
└── README.md                                 # Portfolio documentation
```

---

##  Sample Advanced SQL OLAP Highlights

### 1. Cumulative Pareto Revenue Contribution (Window Function)
```sql
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
    ROUND(100.0 * cumulative_holding_value / total_portfolio_value, 2) AS cumulative_pct,
    CASE 
        WHEN (100.0 * cumulative_holding_value / total_portfolio_value) <= 70.0 THEN 'Class A (High Value)'
        WHEN (100.0 * cumulative_holding_value / total_portfolio_value) <= 90.0 THEN 'Class B (Medium Value)'
        ELSE 'Class C (Long Tail / Low Value)'
    END AS pareto_class
FROM ranked_skus;
```

### 2. Relative Price Index (RPI) vs Category Benchmark
```sql
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
FROM zepto_inventory_master;
```

---

##  Machine Learning Archetype Clustering

Using normalized K-Means clustering ($k=4$), products are automatically grouped into strategic retail archetypes:
1. **Everyday Fast-Movers & Staples**: High stock depth, everyday price point, steady churn (e.g. Milk, Onions, Bread).
2. **Promotional / Discount-Driven Items**: Moderate price, deep discounts (>20%), high promo elasticity (e.g. Snacks, Soda).
3. **Premium High-Margin Anchors**: Low weight, high price point, high revenue density (>₹1,500/kg) (e.g. Saffron, Skin Serums, Dark Chocolate).
4. **Heavy Bulk Goods (Logistical Drag)**: High unit weight (>2kg), low revenue density (<₹150/kg) (e.g. 5kg Atta, 5L Oil, Melons).

---

##  Quickstart Guide

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-username/Zepto-Inventory-And-Sales-Analysis.git
cd Zepto-Inventory-And-Sales-Analysis

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Master Orchestrator (Single-Command Execution)
```bash
# Execute end-to-end pipeline, analytics, figures, and tests in one shot:
python run_project.py --all
```

### 3. Launch the Interactive BI Web Dashboard
```bash
streamlit run dashboard/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser to interact with the live analytics platform.

### 4. Run Automated Unit Tests
```bash
python -m unittest tests/test_pipeline.py
```

---

##  Strategic Business Takeaways

1. **Protect Class A Revenue**: 1,129 SKUs drive 70% of inventory valuation. Never allow stockouts on these critical anchors.
2. **Eliminate Class C Bloat**: 1,263 SKUs generate only 10% of value while consuming shelf capacity and labor time. Rationalize the bottom 10%.
3. **Solve Perishable Out-of-Stock**: Dairy, Bread, and Fresh Produce account for urgent daily customer missions. Stockouts here directly drive customers to Blinkit or Instamart.
4. **Delivery Payload Optimization**: Implement basket-level weight balancing to prevent courier fatigue and vehicle overload from bulk items.

---

##  License & Acknowledgments
- Dataset originally sourced from Kaggle (Zepto public scraped catalog).
- Developed for professional Data Engineering, Analytics Engineering, and Quick-Commerce Strategy portfolios.
