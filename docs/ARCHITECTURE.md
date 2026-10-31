# 🏛️ Technical Architecture - Zepto Analytics Platform

## System Overview
The Zepto Analytics Platform transitions a flat, raw SQL portfolio project into an enterprise-grade Modern Data Stack (MDS) implementation featuring automated ETL, Star Schema dimensional modeling, vectorized OLAP database querying, machine learning categorization, and an interactive BI web application.

---

## Architecture Flow

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
|    (dashboard/app.py)     |                   | (reports/ & figures/)     |
| - Executive Scorecards    |                   | - 6 Publication PNGs      |
| - Live SQL Workbench      |                   | - CSV Analytical Exports  |
| - Real-time scenario Sims |                   |                           |
+---------------------------+                   +---------------------------+
```

---

## Tech Stack & Design Choices

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Language Runtime** | Python 3.12 via Astral `uv` | Modern, blazingly fast dependency management and virtual environment orchestration. |
| **Data Engine** | DuckDB (v2.0) | Columnar, vectorized in-process OLAP engine capable of executing complex window functions and analytical aggregations in sub-milliseconds without database server overhead. |
| **Relational Storage** | SQLite 3 | Embedded zero-dependency SQL engine ensuring universal compatibility across any OS or local machine. |
| **Machine Learning** | Scikit-Learn | K-Means clustering for unsupervised catalog archetype discovery and standard scaling. |
| **Visualization** | Plotly & Matplotlib / Seaborn | Interactive web dashboards (Plotly) paired with publication-grade static reporting exports (Matplotlib). |
| **UI Framework** | Streamlit | Fast, intuitive Python web application framework with reactive widgets, custom CSS styling, and live SQL execution capabilities. |
| **Testing** | Python `unittest` | Automated data quality, currency validation, schema integrity, and boundary testing. |
