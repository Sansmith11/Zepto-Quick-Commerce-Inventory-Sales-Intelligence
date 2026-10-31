"""
Zepto Inventory & Sales Analysis - Automated Publication-Quality Visualizations
================================================================================
Generates 6 high-resolution charts for business intelligence, presentations,
and executive reports into reports/figures/.
"""

import os
import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Styling configuration
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 11
plt.rcParams["axes.titlesize"] = 14
plt.rcParams["axes.labelsize"] = 12

PRIMARY_COLOR = "#6b21a8"   # Zepto Deep Purple
ACCENT_COLOR = "#ec4899"    # Zepto Magenta / Pink
SECONDARY_COLOR = "#3b82f6" # Quick Commerce Blue
WARN_COLOR = "#f59e0b"      # Warning Amber
DANGER_COLOR = "#ef4444"    # Critical Red

def generate_all_visualizations(
    db_path: str = "database/zepto_warehouse.duckdb",
    output_dir: str = "reports/figures"
):
    os.makedirs(output_dir, exist_ok=True)
    con = duckdb.connect(db_path)
    df = con.execute("SELECT * FROM zepto_inventory_master").df()

    # -------------------------------------------------------------------------
    # 1. Category Inventory Holding Value vs Potential Lost Revenue
    # -------------------------------------------------------------------------
    cat_summary = df.groupby("category").agg(
        holding_value=("inventory_holding_value_inr", "sum"),
        lost_revenue=("estimated_stockout_loss_inr", "sum")
    ).sort_values("holding_value", ascending=True)

    fig, ax = plt.subplots(figsize=(12, 8))
    y_pos = np.arange(len(cat_summary))
    height = 0.4

    ax.barh(y_pos - height/2, cat_summary["holding_value"] / 1000.0, height, label="Active Holding Value (₹ '000s)", color=PRIMARY_COLOR, alpha=0.9)
    ax.barh(y_pos + height/2, cat_summary["lost_revenue"] / 1000.0, height, label="Stockout Lost Revenue (₹ '000s)", color=DANGER_COLOR, alpha=0.85)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(cat_summary.index)
    ax.set_xlabel("Value in INR (Thousands ₹)", fontweight="bold")
    ax.set_title("Zepto Dark Store: Inventory Valuation vs Unfulfilled Stockout Loss by Category", fontweight="bold", pad=15)
    ax.legend(loc="lower right", frameon=True)

    for i in y_pos:
        val = cat_summary["holding_value"].iloc[i] / 1000.0
        ax.text(val + 5, i - height/2, f"₹{val:.1f}k", va="center", fontsize=9, color="#1e293b", fontweight="bold")

    plt.tight_layout()
    chart1_path = os.path.join(output_dir, "01_category_revenue_valuation.png")
    fig.savefig(chart1_path, dpi=300)
    plt.close()

    # -------------------------------------------------------------------------
    # 2. ABC Inventory Pareto Curve (80/20 Rule)
    # -------------------------------------------------------------------------
    active_df = df[~df["out_of_stock"]].sort_values("inventory_holding_value_inr", ascending=False).reset_index(drop=True)
    active_df["cumulative_val"] = active_df["inventory_holding_value_inr"].cumsum()
    total_val = active_df["inventory_holding_value_inr"].sum()
    active_df["cum_pct"] = (active_df["cumulative_val"] / total_val) * 100.0
    active_df["sku_rank_pct"] = ((active_df.index + 1) / len(active_df)) * 100.0

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(active_df["sku_rank_pct"], active_df["cum_pct"], color=PRIMARY_COLOR, lw=3, label="Cumulative Value %")
    ax.axhline(70, color=ACCENT_COLOR, linestyle="--", lw=1.5, label="Class A Cutoff (70% Value)")
    ax.axhline(90, color=WARN_COLOR, linestyle="--", lw=1.5, label="Class B Cutoff (90% Value)")

    # Find intersection points
    class_a_sku_pct = active_df[active_df["cum_pct"] <= 70]["sku_rank_pct"].max()
    ax.axvline(class_a_sku_pct, color=ACCENT_COLOR, linestyle=":", lw=1.5)
    ax.text(class_a_sku_pct + 2, 35, f"Class A: Top {class_a_sku_pct:.1f}% SKUs\n= 70% Inventory Capital", 
            bbox=dict(boxstyle="round,pad=0.4", fc="#fdf2f8", ec=ACCENT_COLOR, lw=1.5), fontsize=10, fontweight="bold")

    ax.set_xlabel("% of Total Active SKUs", fontweight="bold")
    ax.set_ylabel("Cumulative % of Inventory Holding Value", fontweight="bold")
    ax.set_title("Pareto ABC Inventory Curve: Capital Concentration across Zepto SKUs", fontweight="bold", pad=15)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 105)
    ax.legend(loc="lower right")

    plt.tight_layout()
    chart2_path = os.path.join(output_dir, "02_abc_inventory_pareto_curve.png")
    fig.savefig(chart2_path, dpi=300)
    plt.close()

    # -------------------------------------------------------------------------
    # 3. Stockout Rate vs Assortment Depth by Category
    # -------------------------------------------------------------------------
    stockout_stats = df.groupby("category").agg(
        total_skus=("sku_id", "count"),
        oos_rate=("out_of_stock", lambda x: np.round(100.0 * x.mean(), 1))
    ).sort_values("oos_rate", ascending=False)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(stockout_stats.index, stockout_stats["oos_rate"], color=DANGER_COLOR, alpha=0.85, edgecolor="#991b1b")
    ax.axhline(df["out_of_stock"].mean() * 100.0, color="#1e293b", linestyle="--", lw=1.5, label=f"Average Store Stockout ({df['out_of_stock'].mean()*100:.1f}%)")

    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.5, f"{h:.1f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_ylabel("Out-of-Stock Rate (%)", fontweight="bold")
    ax.set_title("Stockout Vulnerability by Category: Stockout Rates across Dark Store Assortment", fontweight="bold", pad=15)
    plt.xticks(rotation=45, ha="right", fontweight="bold")
    ax.set_ylim(0, max(stockout_stats["oos_rate"]) + 5)
    ax.legend()

    plt.tight_layout()
    chart3_path = os.path.join(output_dir, "03_stockout_rate_by_category.png")
    fig.savefig(chart3_path, dpi=300)
    plt.close()

    # -------------------------------------------------------------------------
    # 4. Logistics: Revenue Density (₹/kg) vs Unit Weight (gms)
    # -------------------------------------------------------------------------
    plot_df = df[(df["weight_in_gms"] > 0) & (df["weight_in_gms"] <= 5000) & (df["discounted_price_inr"] <= 1500)].copy()

    fig, ax = plt.subplots(figsize=(11, 7))
    scatter = ax.scatter(
        plot_df["weight_in_gms"],
        plot_df["revenue_density_per_kg"],
        c=plot_df["discount_percent"],
        cmap="viridis",
        alpha=0.6,
        s=35,
        edgecolors="none"
    )
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Discount %", fontweight="bold")

    ax.set_xlabel("Product Weight (Grams)", fontweight="bold")
    ax.set_ylabel("Revenue Density (₹ / Kilogram)", fontweight="bold")
    ax.set_title("Dark Store Logistics Optimization: Weight vs Revenue Density per SKU", fontweight="bold", pad=15)
    ax.axhline(500, color="gray", linestyle=":", label="Low Revenue Density (< ₹500/kg)")
    ax.axvline(1000, color="gray", linestyle="--", label="1kg Delivery Threshold")
    ax.legend(loc="upper right")

    plt.tight_layout()
    chart4_path = os.path.join(output_dir, "04_revenue_density_vs_weight.png")
    fig.savefig(chart4_path, dpi=300)
    plt.close()

    # -------------------------------------------------------------------------
    # 5. Discount Depth Distribution Across Categories (Boxplot)
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(13, 7))
    order = df.groupby("category")["discount_percent"].median().sort_values(ascending=False).index
    sns.boxplot(
        data=df,
        x="category",
        y="discount_percent",
        order=order,
        palette="crest",
        ax=ax,
        showmeans=True,
        meanprops={"marker":"o", "markerfacecolor":"red", "markeredgecolor":"red"}
    )
    ax.set_ylabel("Discount Percentage (%)", fontweight="bold")
    ax.set_xlabel("Product Category", fontweight="bold")
    ax.set_title("Discount Depth & Variance Across Categories (Red dot = Mean)", fontweight="bold", pad=15)
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    chart5_path = os.path.join(output_dir, "05_discount_distribution_by_category.png")
    fig.savefig(chart5_path, dpi=300)
    plt.close()

    # -------------------------------------------------------------------------
    # 6. K-Means Product Archetype Clusters
    # -------------------------------------------------------------------------
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    features = ["discounted_price_inr", "discount_percent", "weight_in_gms", "available_quantity"]
    X = StandardScaler().fit_transform(df[features].fillna(0))
    km = KMeans(n_clusters=4, random_state=42, n_init=10)
    df["cluster"] = km.fit_predict(X)

    cluster_labels = {
        0: "Everyday Core Staples",
        1: "Discount & Promotional Drivers",
        2: "Premium High-Ticket Anchors",
        3: "Heavy Bulk Goods"
    }
    df["archetype_label"] = df["cluster"].map(cluster_labels)

    fig, ax = plt.subplots(figsize=(11, 7))
    sns.scatterplot(
        data=df,
        x="discounted_price_inr",
        y="discount_percent",
        hue="archetype_label",
        palette=["#3b82f6", "#ec4899", "#8b5cf6", "#10b981"],
        s=60,
        alpha=0.75,
        ax=ax
    )
    ax.set_xlabel("Discounted Price (₹)", fontweight="bold")
    ax.set_ylabel("Discount Percentage (%)", fontweight="bold")
    ax.set_title("Machine Learning Archetype Segmentation: Price vs Discount Clusters", fontweight="bold", pad=15)
    ax.legend(title="Product Archetype", frameon=True)

    plt.tight_layout()
    chart6_path = os.path.join(output_dir, "06_ml_product_archetypes.png")
    fig.savefig(chart6_path, dpi=300)
    plt.close()

    con.close()
    print(f"[SUCCESS] All 6 publication-grade figures saved to: {output_dir}")

if __name__ == "__main__":
    generate_all_visualizations()
