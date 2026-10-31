# 📊 Zepto Quick-Commerce Business Insights & Strategic Recommendations

## Executive Summary
This analysis evaluates **3,731 SKUs** across **14 categories** stored in a hyperlocal Zepto dark store (micro-fulfillment center). The store holds **₹22.43 Lakhs** in active inventory holding value, while suffering **₹1.78 Lakhs in estimated lost revenue** due to a **12.14% stockout rate**.

---

## 1. Key Findings & Quantitative Breakdown

### A. Working Capital & Assortment Concentration (Pareto Principle)
- **Class A SKUs (34.4% of catalog, 1,129 items)** drive **70.0% of total inventory valuation** (₹15.7 Lakhs).
- **Class B SKUs (27.0% of catalog, 886 items)** contribute **20.0% of valuation**.
- **Class C SKUs (38.5% of catalog, 1,263 items)** tie up only **10.0% of capital**.
- **Takeaway**: Dark store capacity is constrained. Over-indexing on low-velocity Class C SKUs increases picking friction and holding costs without driving meaningful gross merchandise value.

### B. Stockout Opportunity Cost & Lost Demand
- **453 out of 3,732 SKUs are out of stock (12.14% overall stockout rate)**.
- **Top Stockout Impact Categories**:
  1. *Cooking Essentials*: High stockout volume in staple oils, ghee, and pulses.
  2. *Personal Care & Hygiene*: High-ticket items with steep margin contributions.
  3. *Dairy, Bread & Batter*: Daily perishable staples where a stockout forces immediate customer churn to competitors (Blinkit / Instamart).
- Estimated direct revenue leakage from out-of-stock items stands at **₹1,78,058.90**.

### C. Dark Store Shelf Space & Delivery Payload Efficiency
- Total dark store physical storage payload: **6,005.85 kg (6.0 metric tonnes)**.
- Two-wheeler delivery riders face strict **10–12 kg payload limits**.
- **High Revenue Density Stars (Space Champions)**:
  - *Personal Care & Paan Corner*: **~₹1,850/kg** revenue density. High margin, compact footprint, minimal courier fatigue.
- **Logistical Drag (Heavy Bulk Items)**:
  - *Atta, Rice, Oil, Melons*: Large footprint, **< ₹150/kg** revenue density, high picking and courier delivery burden.

### D. Margin Bleed & Over-Discounting Analysis
- 180 high-ticket SKUs (>₹200) carry discounts exceeding 15%–25%.
- Simulation demonstrates that trimming discount by just **3.0%** on these price-inelastic items recovers **₹10,183.98 in gross margin** per replenishment cycle with near-zero drop in conversion.

---

## 2. Actionable Strategic Playbook

```
+---------------------------------------------------------------------------------------+
|                               ZEPTO ACTION MATRIX                                     |
+------------------------------------+--------------------------------------------------+
| Immediate (Next 48 Hours)          | Medium Term (Quarterly Strategy)                 |
+------------------------------------+--------------------------------------------------+
| 1. Trigger automated P0 reorders   | 1. Rationalize Class C catalog (delist bottom    |
|    for top 25 high-MRP OOS SKUs.   |    10% low-velocity SKUs).                       |
| 2. Implement twice-daily restock   | 2. Implement Dynamic Delivery Surcharge for bulk |
|    for Dairy and Produce.          |    orders exceeding 8 kg.                        |
| 3. Trim 3% promotional discount    | 3. Establish Dedicated Dark Store Micro-Zones    |
|    on price-inelastic luxury SKUs. |    for ultra-high revenue density categories.    |
+------------------------------------+--------------------------------------------------+
```

### Strategic Recommendations:
1. **Perishable Category SLA (Service Level Agreement)**:
   - Institute a 99.5% in-stock threshold for Dairy, Bread, and Fresh Produce. High churn items should trigger automated mother-warehouse dispatch whenever dark-store on-hand stock falls below 3 units.
2. **Dynamic Weight-Based Delivery Surcharge**:
   - Heavy bulk goods (>3kg per unit) consume disproportionate delivery bag volume. Introduce basket-level weight balancing algorithms to pair light high-margin items with heavy groceries.
3. **Automated Reorder Point (ROP) Alerts**:
   - Replace manual stock checks with the ROP calculation model (`est_daily_demand * lead_time + safety_stock`) integrated into the dark store dispatch terminal.
