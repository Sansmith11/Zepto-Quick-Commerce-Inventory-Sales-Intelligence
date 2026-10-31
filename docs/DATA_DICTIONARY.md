# 📖 Data Dictionary - Zepto Quick-Commerce Analytics Platform

## Overview
This document outlines the data schema, entity relationships, type specifications, currency units, and derived business metric definitions used across the Zepto Analytics Platform.

---

## 1. Raw vs Processed Schema Mapping

| Raw CSV Field (`zepto_data.csv`) | Raw Type | Cleaned / Warehouse Field | Standard Type | Description |
| :--- | :--- | :--- | :--- | :--- |
| `Category` | VARCHAR | `category` / `category_name` | VARCHAR(120) | High-level department/aisle |
| `name` | VARCHAR | `product_name` | VARCHAR(255) | Product name as displayed on customer app |
| `mrp` | INT (Paise) | `mrp_inr` | NUMERIC(10,2) | Maximum Retail Price in Indian Rupees (₹) |
| `discountPercent` | INT | `discount_percent` | NUMERIC(5,2) | Advertised discount percentage |
| `discountedSellingPrice` | INT (Paise) | `discounted_price_inr` | NUMERIC(10,2) | Final customer purchase price in INR (₹) |
| `availableQuantity` | INT | `available_quantity` | INTEGER | Active shelf stock count in dark store (0 to 6) |
| `weightInGms` | INT | `weight_in_gms` | INTEGER | Net product weight in grams |
| `outOfStock` | BOOLEAN | `out_of_stock` | BOOLEAN | TRUE if item is unfulfillable, FALSE if in stock |
| `quantity` | INT | `pack_quantity` | INTEGER | Units per multipack or weight equivalent |

---

## 2. Derived Analytical & Financial Metrics

| Metric Name | Formula / Logic | Business Purpose |
| :--- | :--- | :--- |
| **`discount_amount_inr`** | `mrp_inr - discounted_price_inr` | Gross discount subsidy given per unit sold |
| **`effective_discount_percent`** | `ROUND(((mrp_inr - discounted_price_inr) / mrp_inr) * 100, 1)` | Audited mathematical discount percentage |
| **`inventory_holding_value_inr`** | `discounted_price_inr * available_quantity` | Realizable revenue currently locked in dark store shelf inventory |
| **`mrp_inventory_value_inr`** | `mrp_inr * available_quantity` | Gross catalog inventory valuation at full retail price |
| **`estimated_stockout_loss_inr`** | `IF(out_of_stock, discounted_price_inr * 4.56, 0)` | Estimated unfulfilled gross revenue lost due to stockouts |
| **`price_per_gram_inr`** | `discounted_price_inr / weight_in_gms` | Unit-level value index for value-conscious shoppers |
| **`revenue_density_per_kg`** | `(discounted_price_inr / weight_in_gms) * 1000` | Revenue generated per kilogram of shelf/delivery space |
| **`inventory_weight_kg`** | `(weight_in_gms * available_quantity) / 1000` | Total physical load stored in warehouse |

---

## 3. Dimensional Model (Star Schema)

### Entity: `dim_category`
- `category_id` (PK, INT): Primary identifier
- `category_name` (VARCHAR): Standardized category name

### Entity: `dim_product`
- `product_id` (PK, INT): Unique product identifier
- `product_name` (VARCHAR): Normalized product title
- `category_id` (FK, INT): References `dim_category`
- `weight_in_gms` (INT): Product net weight
- `weight_tier` (VARCHAR): Ultra-Light (<=100g), Light (100-500g), Medium (500g-2kg), Bulk (>2kg)
- `price_tier` (VARCHAR): Budget (<₹50), Everyday (₹50-200), Premium (₹200-500), Luxury (>₹500)

### Entity: `fact_inventory`
- `sku_id` (PK, INT): Unique SKU snapshot identifier
- `product_id` (FK, INT): References `dim_product`
- `category_id` (FK, INT): References `dim_category`
- `mrp_inr`, `discounted_price_inr`, `discount_percent`
- `available_quantity`, `out_of_stock`
- `inventory_holding_value_inr`, `estimated_stockout_loss_inr`
- `inventory_weight_kg`, `revenue_density_per_kg`
