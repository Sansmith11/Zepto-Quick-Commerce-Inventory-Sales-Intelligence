"""
Zepto Quick-Commerce Analytics Platform - Master Orchestrator CLI
=================================================================
Usage:
    python run_project.py --all           # Execute full end-to-end pipeline & reports
    python run_project.py --pipeline      # Run ETL & Star Schema materialization
    python run_project.py --analytics     # Run ABC Pareto, KPIs & ML Archetypes
    python run_project.py --visualize     # Generate publication-grade figures
    python run_project.py --test          # Run automated data quality unit tests
    python run_project.py --dashboard     # Launch interactive Streamlit BI Web App
"""

import sys
import os
import argparse
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_step(cmd, description):
    print(f"\n========================================================")
    print(f"🚀 {description}...")
    print(f"========================================================")
    ret = subprocess.run(cmd, shell=True)
    if ret.returncode != 0:
        print(f"❌ Error during: {description} (Exit code: {ret.returncode})")
        sys.exit(ret.returncode)
    print(f"✅ Completed: {description}")

def main():
    parser = argparse.ArgumentParser(description="Zepto Quick-Commerce Master CLI")
    parser.add_argument("--pipeline", action="store_true", help="Run ETL and load DuckDB/SQLite")
    parser.add_argument("--analytics", action="store_true", help="Run Advanced Analytics & ML Optimizer")
    parser.add_argument("--visualize", action="store_true", help="Generate publication charts")
    parser.add_argument("--test", action="store_true", help="Execute unit tests")
    parser.add_argument("--dashboard", action="store_true", help="Launch Streamlit dashboard")
    parser.add_argument("--all", action="store_true", help="Run full pipeline, tests, analytics, and charts")

    args = parser.parse_args()

    # Determine python executable
    py_exec = sys.executable

    if len(sys.argv) == 1 or args.all:
        print("\n⚡ [ZEPTO ANALYTICS PLATFORM] Running Full End-to-End Orchestration...")
        run_step(f'"{py_exec}" src/etl_pipeline.py', "1. ETL Pipeline & Star Schema Modeling")
        run_step(f'"{py_exec}" src/advanced_analytics.py', "2. Advanced OLAP Analytics & ABC Classification")
        run_step(f'"{py_exec}" src/ml_inventory_optimizer.py', "3. ML Clustering & Inventory Optimization")
        run_step(f'"{py_exec}" notebooks/zepto_advanced_eda.py', "4. Publication-Grade Visualization Generation")
        run_step(f'"{py_exec}" -m unittest tests/test_pipeline.py', "5. Automated Data Quality & Schema Unit Tests")
        print("\n🎉 ALL PIPELINE STAGES COMPLETED SUCCESSFULLY!")
        print("💡 To launch the interactive BI dashboard, run:")
        print("   streamlit run dashboard/app.py\n")
        return

    if args.pipeline:
        run_step(f'"{py_exec}" src/etl_pipeline.py', "ETL Pipeline & Star Schema Modeling")

    if args.analytics:
        run_step(f'"{py_exec}" src/advanced_analytics.py', "Advanced OLAP Analytics")
        run_step(f'"{py_exec}" src/ml_inventory_optimizer.py', "ML Clustering & Inventory Optimization")

    if args.visualize:
        run_step(f'"{py_exec}" notebooks/zepto_advanced_eda.py', "Publication-Grade Visualization Generation")

    if args.test:
        run_step(f'"{py_exec}" -m unittest tests/test_pipeline.py', "Data Quality Unit Tests")

    if args.dashboard:
        print("\n⚡ Starting Zepto BI Dashboard...")
        subprocess.run(f"streamlit run dashboard/app.py", shell=True)

if __name__ == "__main__":
    main()
