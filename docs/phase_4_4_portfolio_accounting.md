# Aurxon QuantX — Phase 4.4 Portfolio Accounting Methodology & Verification

## 1. Overview & System Identity
- **Product Name:** Aurxon QuantX
- **Brand:** AURXON
- **Milestone:** Phase 4.4 — Workstream A: Portfolio Inventory and Accounting
- **Repository:** `AURXONQuant`
- **Module:** `backend/app/trading/paper_manager.py`, `backend/app/trading/portfolio_analytics.py`, `backend/app/schemas/portfolio_intelligence.py`

This document defines the mathematical, transactional, and architectural specifications governing multi-portfolio accounting, holdings tracking, cost-basis computation, corporate-action adjustments, and concentration measurement in **Aurxon QuantX**.

---

## 2. Multi-Portfolio Inventory Architecture

### 2.1 Ledger Isolation
The system provides multi-portfolio simulation capability anchored to SQLite WAL persistence (`data/aurxon_paper_portfolio.sqlite`). Each portfolio is strictly isolated via `portfolio_id`:
- **Default Portfolio:** `DEFAULT` (initialized with standard ₹10,00,000 cash balance).
- **Secondary / User Portfolios:** Arbitrary alphanumeric identifiers (`QUANT_ALPHA`, `BALANCED_GROWTH`, etc.) initialized with user-defined virtual cash.
- **Table Isolation:** All records in `paper_portfolios`, `paper_orders`, `paper_positions`, and `paper_portfolio_snapshots` include `portfolio_id` as part of their composite primary keys or indexes.

### 2.2 Mathematical Accounting Invariants
Every portfolio satisfies strict mathematical conservation laws:
$$\text{Total Equity}_t = \text{Cash Balance}_t + \sum_{i=1}^N \left( \text{Quantity}_{i,t} \times \text{Current Price}_{i,t} \right)$$
Where:
- $\text{Cost Basis}_{i,t} = \text{Quantity}_{i,t} \times \text{Average Cost}_{i,t}$
- $\text{Unrealized P&L}_{i,t} = \left( \text{Current Price}_{i,t} - \text{Average Cost}_{i,t} \right) \times \text{Quantity}_{i,t}$
- $\text{Unrealized P&L \%}_{i,t} = \frac{\text{Current Price}_{i,t} - \text{Average Cost}_{i,t}}{\text{Average Cost}_{i,t}} \times 100$
- $\text{Realized P&L}_{i,t} = \sum_{k} \left( \text{Fill Price}_k - \text{FIFO Cost}_k \right) \times \text{Quantity}_k$
- $\text{Portfolio Weight \%}_i = \frac{\text{Market Value}_i}{\text{Total Equity}} \times 100$

### 2.3 Double-Entry Cash Conservation
During buy orders:
$$\text{Cash}_{t+1} = \text{Cash}_t - (\text{Quantity} \times \text{Execution Price} + \text{Statutory Transaction Costs})$$
During sell orders:
$$\text{Cash}_{t+1} = \text{Cash}_t + (\text{Quantity} \times \text{Execution Price} - \text{Statutory Transaction Costs})$$
Statutory transaction costs adhere strictly to the Indian `2024.2-STATUTORY` schedule (STT, Stamp Duty, NSE transaction charges, SEBI turnover fees, GST).

---

## 3. Handling Missing, Stale & Unpriced Holdings

### 3.1 Anti-Silent-Substitution Invariant
Under no circumstances does Aurxon QuantX replace a missing price with zero, a previous arbitrary price, or a fabricated figure. 

1. **Pricing Status Classifications:**
   - `PRICED_CURRENT`: Verified price quote received with timestamp $\le 24\text{ hours}$ old.
   - `PRICED_STALE`: Price quote older than 24 hours. Market value is computed for display with explicit warning, but marked stale.
   - `UNPRICED`: No price quote available in market data store or broker feed.
2. **Behavior on Unpriced Securities:**
   - Market value and unrealized P&L are set to `None` (`null` in JSON).
   - Valuation reflects `cost_basis_total` as conservative floor with explicit qualification `PRICING_UNAVAILABLE`.
   - Rebalancing algorithms block buy/sell actions on unpriced holdings to prevent erroneous trade sizing.

---

## 4. Concentration & Exposure Analytics

### 4.1 Herfindahl-Hirschman Index (HHI)
Portfolio concentration is mathematically measured using normalized weights:
$$\text{HHI} = \sum_{i=1}^N \left( \frac{\text{Market Value}_i}{\text{Total Invested Value}} \right)^2$$
- $\text{HHI} < 0.15$: Diversified allocation.
- $0.15 \le \text{HHI} \le 0.25$: Moderately concentrated.
- $\text{HHI} > 0.25$: Highly concentrated.

### 4.2 Concentration Breaches
The engine continuously inspects:
- **Top Position Limit:** Configurable threshold (default 30.0%). Breaches trigger `has_concentration_breach = True` with explicit diagnostic alerts.
- **Top-3 Positions Concentration:** Aggregate exposure of the 3 largest holdings.
- **Sector Concentration:** Sector aggregation based on canonical NSE classification (Technology, Energy, Financial Services, etc.).

---

## 5. Durable Snapshot Architecture

Portfolio states can be frozen into reproducible audit snapshots via `record_portfolio_snapshot()` into the SQLite WAL table `paper_portfolio_snapshots`:
- `snapshot_id`: Unique timestamped identifier (`SNAP_{portfolio_id}_{YYYYMMDD_HHMMSS}_{uuid}`).
- `equity`, `cash`, `holdings_count`, `unrealized_pnl`, `realized_pnl`.
- `holdings_json`: Complete JSON serialization of all holdings, quantities, cost bases, and prices.
- Queryable via `get_portfolio_snapshots(portfolio_id)` for historical performance reconstruction and compliance audits.

---

## 6. Corporate Action Treatment

When official corporate actions occur on Indian securities:
1. **Cash Dividends:** Credited directly to the virtual cash ledger without altering share quantity or cost basis.
2. **Stock Splits / Bonus Issues:** 
   $$\text{Quantity}_{new} = \text{Quantity}_{old} \times \text{Multiplier}$$
   $$\text{Average Cost}_{new} = \frac{\text{Average Cost}_{old}}{\text{Multiplier}}$$
   FIFO lot inventory is proportionally adjusted, preserving total invested capital.
