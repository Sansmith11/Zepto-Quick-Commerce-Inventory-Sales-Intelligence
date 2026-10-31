"""
Zepto Quick-Commerce Inventory & Sales Intelligence Dashboard
=============================================================
Interactive Enterprise BI Web Application built with Streamlit, DuckDB & Plotly.
Run with: streamlit run dashboard/app.py
"""

import os
import duckdb
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Zepto Quick-Commerce Analytics Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #7c3aed, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1.2rem;
        border-left: 5px solid #7c3aed;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #f1f5f9;
        border-radius: 8px 8px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #7c3aed !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Database Connection Helper
DB_PATH = "database/zepto_warehouse.duckdb"

@st.cache_data
def load_master_data():
    if not os.path.exists(DB_PATH):
        st.error(f"Database not found at {DB_PATH}. Please run python run_project.py --pipeline first.")
        st.stop()
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("SELECT * FROM zepto_inventory_master").df()
    con.close()
    return df

df_master = load_master_data()

# -----------------------------------------------------------------------------
# SIDEBAR FILTERS
# -----------------------------------------------------------------------------
st.sidebar.image("https://images.seeklogo.com/logo-png/43/1/zepto-logo-png_seeklogo-437500.png", width=120) if False else None
st.sidebar.title(" Control Center")
st.sidebar.markdown("Filter dark store inventory data in real-time.")

# Category Multi-Select
all_categories = sorted(df_master["category"].unique())
select_all_cats = st.sidebar.checkbox("Select All Categories", value=True)
if select_all_cats:
    selected_categories = st.sidebar.multiselect("Category Filter", all_categories, default=all_categories)
else:
    selected_categories = st.sidebar.multiselect("Category Filter", all_categories, default=["Cooking Essentials", "Munchies", "Fruits & Vegetables"])

# Stock Status Filter
stock_status = st.sidebar.radio("Stock Status", ["All Items", "In-Stock Only", "Out-of-Stock Only"])

# Price Tier Filter
all_price_tiers = list(df_master["price_tier"].unique())
selected_price_tiers = st.sidebar.multiselect("Price Tier", all_price_tiers, default=all_price_tiers)

# Weight Tier Filter
all_weight_tiers = list(df_master["weight_tier"].unique())
selected_weight_tiers = st.sidebar.multiselect("Weight Tier", all_weight_tiers, default=all_weight_tiers)

# Discount Slider
min_disc, max_disc = int(df_master["discount_percent"].min()), int(df_master["discount_percent"].max())
discount_range = st.sidebar.slider("Discount % Range", min_disc, max_disc, (min_disc, max_disc))

# Apply Filters
filtered_df = df_master[
    (df_master["category"].isin(selected_categories)) &
    (df_master["price_tier"].isin(selected_price_tiers)) &
    (df_master["weight_tier"].isin(selected_weight_tiers)) &
    (df_master["discount_percent"] >= discount_range[0]) &
    (df_master["discount_percent"] <= discount_range[1])
]

if stock_status == "In-Stock Only":
    filtered_df = filtered_df[~filtered_df["out_of_stock"]]
elif stock_status == "Out-of-Stock Only":
    filtered_df = filtered_df[filtered_df["out_of_stock"]]

# Header
st.markdown('<div class="main-header">Zepto Quick-Commerce Inventory & Sales Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Executive Decision Support System • Hyperlocal Dark Store Inventory Optimization • Pricing & Margin Analytics</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TOP EXECUTIVE SCORECARD
# -----------------------------------------------------------------------------
col1, col2, col3, col4, col5, col6 = st.columns(6)

tot_holding_val = filtered_df["inventory_holding_value_inr"].sum()
tot_loss_val = filtered_df["estimated_stockout_loss_inr"].sum()
tot_skus = len(filtered_df)
oos_count = filtered_df["out_of_stock"].sum()
oos_rate = (100.0 * oos_count / tot_skus) if tot_skus > 0 else 0.0
avg_discount = filtered_df["discount_percent"].mean() if tot_skus > 0 else 0.0
tot_weight_kg = filtered_df["inventory_weight_kg"].sum()

col1.metric("Inventory Value", f"₹{tot_holding_val:,.0f}", help="Total INR capital locked in dark store shelf inventory")
col2.metric("Lost Revenue (OOS)", f"₹{tot_loss_val:,.0f}", delta=f"-{tot_loss_val:,.0f}", delta_color="inverse", help="Unfulfilled demand loss from out-of-stock items")
col3.metric("Total Active SKUs", f"{tot_skus:,}", f"{filtered_df['product_name'].nunique()} unique")
col4.metric("Stockout Rate", f"{oos_rate:.1f}%", delta=f"{oos_count} OOS SKUs", delta_color="inverse")
col5.metric("Avg Discount", f"{avg_discount:.1f}%")
col6.metric("Total Stored Weight", f"{tot_weight_kg:,.1f} kg", help="Total physical payload stored in dark store micro-warehouse")

st.markdown("---")

# -----------------------------------------------------------------------------
# MAIN DASHBOARD TABS
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    " Executive Overview",
    " ABC & Pareto Optimization",
    " Stockout Risk & Restock Matrix",
    " Dark Store Logistics & Payload",
    " Live SQL Workbench & Data Explorer"
])

# -----------------------------------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW
# -----------------------------------------------------------------------------
with tab1:
    c1, c2 = st.columns([7, 5])
    
    with c1:
        st.subheader("Category Valuation & Stockout Impact")
        cat_agg = filtered_df.groupby("category").agg(
            holding_value=("inventory_holding_value_inr", "sum"),
            stockout_loss=("estimated_stockout_loss_inr", "sum"),
            sku_count=("sku_id", "count")
        ).reset_index().sort_values("holding_value", ascending=True)

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            y=cat_agg["category"],
            x=cat_agg["holding_value"],
            name="Inventory Holding Value (₹)",
            orientation="h",
            marker=dict(color="#7c3aed")
        ))
        fig_bar.add_trace(go.Bar(
            y=cat_agg["category"],
            x=cat_agg["stockout_loss"],
            name="Estimated Stockout Loss (₹)",
            orientation="h",
            marker=dict(color="#ef4444")
        ))
        fig_bar.update_layout(
            barmode="group",
            height=460,
            margin=dict(l=0, r=20, t=30, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        st.subheader("Category Capital Share")
        fig_pie = px.pie(
            cat_agg,
            values="holding_value",
            names="category",
            hole=0.45,
            color_discrete_sequence=px.colors.sequential.Purp
        )
        fig_pie.update_layout(height=460, margin=dict(l=20, r=20, t=30, b=30))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("#### Top 10 High-Value In-Stock Anchors")
    top_anchors = filtered_df[~filtered_df["out_of_stock"]].sort_values("inventory_holding_value_inr", ascending=False)[[
        "sku_id", "product_name", "category", "mrp_inr", "discount_percent", "discounted_price_inr",
        "available_quantity", "inventory_holding_value_inr", "weight_in_gms"
    ]].head(10)
    st.dataframe(top_anchors, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# TAB 2: ABC & PARETO INVENTORY OPTIMIZATION
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("Pareto ABC Inventory Classification (80/20 Rule)")
    st.markdown("""
    **Class A Items (Top 70% Value)**: Critical revenue drivers. Must have zero stockout tolerance with daily replenishment.  
    **Class B Items (Next 20% Value)**: Medium volume staples. Maintain moderate safety stock.  
    **Class C Items (Bottom 10% Value)**: Long tail assortment. Guard against over-stocking and holding cost decay.
    """)

    active_items = filtered_df[~filtered_df["out_of_stock"]].sort_values("inventory_holding_value_inr", ascending=False).reset_index(drop=True)
    if len(active_items) > 0:
        active_items["cum_val"] = active_items["inventory_holding_value_inr"].cumsum()
        total_active_val = active_items["inventory_holding_value_inr"].sum()
        active_items["cum_pct"] = (active_items["cum_val"] / total_active_val) * 100.0
        active_items["sku_pct"] = ((active_items.index + 1) / len(active_items)) * 100.0

        def assign_abc(pct):
            if pct <= 70.0:
                return "Class A"
            elif pct <= 90.0:
                return "Class B"
            else:
                return "Class C"

        active_items["abc_class"] = active_items["cum_pct"].apply(assign_abc)

        # Plotly Pareto
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Scatter(
            x=active_items["sku_pct"],
            y=active_items["cum_pct"],
            mode="lines",
            name="Cumulative Value %",
            line=dict(color="#7c3aed", width=3)
        ))
        fig_pareto.add_hline(y=70, line_dash="dash", line_color="#ec4899", annotation_text="Class A Cutoff (70%)")
        fig_pareto.add_hline(y=90, line_dash="dash", line_color="#f59e0b", annotation_text="Class B Cutoff (90%)")
        fig_pareto.update_layout(
            xaxis_title="% of Total Active SKUs",
            yaxis_title="Cumulative % of Inventory Holding Value",
            height=420,
            margin=dict(l=40, r=20, t=30, b=40)
        )
        st.plotly_chart(fig_pareto, use_container_width=True)

        # ABC Metrics Summary Cards
        abc_summary = active_items.groupby("abc_class").agg(
            sku_count=("sku_id", "count"),
            total_value=("inventory_holding_value_inr", "sum"),
            avg_price=("discounted_price_inr", "mean"),
            avg_stock=("available_quantity", "mean")
        ).reset_index()
        abc_summary["pct_of_skus"] = (100.0 * abc_summary["sku_count"] / len(active_items)).round(1)
        abc_summary["pct_of_value"] = (100.0 * abc_summary["total_value"] / total_active_val).round(1)

        cols = st.columns(3)
        for i, row in abc_summary.iterrows():
            with cols[i]:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{row['abc_class']}</h4>
                    <p><b>{row['sku_count']} SKUs</b> ({row['pct_of_skus']}% of catalog)</p>
                    <p><b>₹{row['total_value']:,.0f}</b> ({row['pct_of_value']}% of capital)</p>
                    <p>Avg Unit Price: ₹{row['avg_price']:.1f}</p>
                    <p>Avg Stock on Shelf: {row['avg_stock']:.1f} units</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No active in-stock items in the selected filter range.")

# -----------------------------------------------------------------------------
# TAB 3: STOCKOUT RISK & RESTOCK MATRIX
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("Critical Stockout Alerts & Immediate Restock Ranking")
    st.markdown("Identifies revenue leakage from unfulfilled demand. Prioritizes SKUs based on estimated lost revenue.")

    oos_df = filtered_df[filtered_df["out_of_stock"]].sort_values("estimated_stockout_loss_inr", ascending=False)
    
    col_a, col_b = st.columns([5, 7])
    with col_a:
        st.write(f"Total Out-of-Stock SKUs: **{len(oos_df)}** | Lost Revenue Impact: **₹{oos_df['estimated_stockout_loss_inr'].sum():,.0f}**")
        cat_oos = oos_df.groupby("category")["estimated_stockout_loss_inr"].sum().reset_index().sort_values("estimated_stockout_loss_inr", ascending=False)
        fig_oos = px.bar(
            cat_oos,
            x="estimated_stockout_loss_inr",
            y="category",
            orientation="h",
            color="estimated_stockout_loss_inr",
            color_continuous_scale="Reds",
            title="Lost Revenue Impact by Category"
        )
        fig_oos.update_layout(height=420, margin=dict(l=20, r=20, t=40, b=30))
        st.plotly_chart(fig_oos, use_container_width=True)

    with col_b:
        st.markdown("#### High-Priority Restock Worklist")
        restock_table = oos_df[[
            "sku_id", "product_name", "category", "mrp_inr", "discount_percent",
            "discounted_price_inr", "estimated_stockout_loss_inr"
        ]].head(15)
        st.dataframe(restock_table, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# TAB 4: DARK STORE LOGISTICS & PAYLOAD ANALYTICS
# -----------------------------------------------------------------------------
with tab4:
    st.subheader("Delivery Payload & Dark Store Shelf Space Efficiency")
    st.markdown("Quick-commerce delivery partners operate on 2-wheelers with a strict 10–12 kg payload cap. Optimize shelf space by maximizing revenue density (₹ / kg).")

    logistics_df = filtered_df[filtered_df["weight_in_gms"] > 0].copy()
    
    fig_scatter = px.scatter(
        logistics_df,
        x="weight_in_gms",
        y="revenue_density_per_kg",
        color="category",
        size="inventory_holding_value_inr",
        hover_data=["product_name", "discounted_price_inr", "available_quantity"],
        title="Product Weight vs Revenue Density (Bubble size = Inventory Holding Value)",
        labels={"weight_in_gms": "Product Unit Weight (Grams)", "revenue_density_per_kg": "Revenue Density (₹ / Kilogram)"}
    )
    fig_scatter.add_vline(x=1000, line_dash="dash", line_color="gray", annotation_text="1 kg Bulk Threshold")
    fig_scatter.add_hline(y=500, line_dash="dash", line_color="red", annotation_text="Minimum Revenue Density (₹500/kg)")
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)

    c_p1, c_p2 = st.columns(2)
    with c_p1:
        st.markdown("####  Highest Revenue Density SKUs (Space Champions)")
        high_dense = logistics_df.sort_values("revenue_density_per_kg", ascending=False)[[
            "product_name", "category", "weight_in_gms", "discounted_price_inr", "revenue_density_per_kg"
        ]].head(8)
        st.dataframe(high_dense, use_container_width=True, hide_index=True)

    with c_p2:
        st.markdown("####  Heavy Bulk SKUs (Delivery Drag)")
        heavy_skus = logistics_df[logistics_df["weight_in_gms"] >= 1000].sort_values("revenue_density_per_kg", ascending=True)[[
            "product_name", "category", "weight_in_gms", "discounted_price_inr", "revenue_density_per_kg"
        ]].head(8)
        st.dataframe(heavy_skus, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# TAB 5: LIVE SQL QUERY WORKBENCH & DATA EXPLORER
# -----------------------------------------------------------------------------
with tab5:
    st.subheader("⚡ Live DuckDB SQL Query Workbench")
    st.markdown("Execute high-performance vectorized SQL queries directly against the Zepto analytical warehouse.")

    prebuilt_queries = {
        "1. Category Financial Scorecard": """
SELECT 
    category,
    COUNT(sku_id) AS total_skus,
    ROUND(SUM(inventory_holding_value_inr), 2) AS holding_value_inr,
    ROUND(AVG(discount_percent), 2) AS avg_discount_pct,
    ROUND(AVG(discounted_price_inr), 2) AS avg_price_inr,
    ROUND(100.0 * SUM(CASE WHEN out_of_stock THEN 1 ELSE 0 END) / COUNT(sku_id), 2) AS stockout_pct
FROM zepto_inventory_master
GROUP BY category
ORDER BY holding_value_inr DESC;
        """,
        "2. Top 10 Best Value Items by Price per Gram": """
SELECT 
    product_name,
    category,
    weight_in_gms,
    discounted_price_inr,
    price_per_gram_inr
FROM zepto_inventory_master
WHERE weight_in_gms >= 100 AND price_per_gram_inr > 0
ORDER BY price_per_gram_inr ASC
LIMIT 10;
        """,
        "3. Critical High-MRP Out-of-Stock SKUs": """
SELECT 
    product_name,
    category,
    mrp_inr,
    discount_percent,
    estimated_stockout_loss_inr
FROM zepto_inventory_master
WHERE out_of_stock = TRUE AND mrp_inr >= 300
ORDER BY estimated_stockout_loss_inr DESC
LIMIT 15;
        """,
        "4. Margin Bleeders (MRP > ₹400 & Discount > 20%)": """
SELECT 
    product_name,
    category,
    mrp_inr,
    discount_percent,
    discounted_price_inr,
    ROUND(mrp_inr - discounted_price_inr, 2) AS margin_giveaway_per_unit
FROM zepto_inventory_master
WHERE mrp_inr >= 400 AND discount_percent >= 20
ORDER BY margin_giveaway_per_unit DESC
LIMIT 15;
        """
    }

    selected_query_key = st.selectbox("Select a Pre-Built Analytical Query or Write Custom SQL:", list(prebuilt_queries.keys()))
    sql_input = st.text_area("SQL Editor", value=prebuilt_queries[selected_query_key].strip(), height=160)

    if st.button(" Execute SQL Query"):
        try:
            con = duckdb.connect(DB_PATH, read_only=True)
            res_df = con.execute(sql_input).df()
            con.close()
            st.success(f"Query executed successfully ({len(res_df)} rows returned).")
            st.dataframe(res_df, use_container_width=True)
        except Exception as e:
            st.error(f"SQL Execution Error: {str(e)}")

    st.markdown("---")
    st.subheader("Filtered Catalog Raw Data Explorer")
    st.write(f"Showing **{len(filtered_df)}** records matching the sidebar filters.")
    st.dataframe(filtered_df, use_container_width=True, height=350)
    
    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=" Download Filtered Data as CSV",
        data=csv_bytes,
        file_name="zepto_filtered_inventory.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.85rem;'>Zepto Quick-Commerce Analytics Platform • Upgraded to Advanced Production Grade • Powered by DuckDB & Streamlit</p>", unsafe_allow_html=True)
