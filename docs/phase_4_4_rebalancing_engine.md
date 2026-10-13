# Aurxon QuantX — Phase 4.4 Paper-Only Rebalancing Simulator

## 1. Overview & System Identity
- **Product Name:** Aurxon QuantX
- **Brand:** AURXON
- **Milestone:** Phase 4.4 — Workstream D: Rebalancing Engine
- **Module:** `backend/app/trading/rebalancing.py`, `backend/app/schemas/portfolio_intelligence.py`

This document outlines the optimization heuristics, constraint satisfaction rules, integer-lot rounding, transaction drag modeling, and strict safety boundaries of the **Aurxon QuantX** paper-only rebalancing simulator.

---

## 2. Rebalancing Objectives & Sizing Logic

The goal of the rebalancing simulator is to compute the minimal transaction set required to transition an active portfolio from its current weights $w_{current}$ to target weights $w_{target}$, subject to user constraints and market realities.

### 2.1 Target Value Calculation
For each security $i \in \{1 \dots N\}$:
$$\text{Target Value}_i = \text{Total Portfolio Equity} \times w_{target, i}$$
$$\text{Value Delta}_i = \text{Target Value}_i - \text{Current Value}_i$$

### 2.2 Discrete Share Lot Sizing
Real equity markets do not permit fractional share orders. Aurxon QuantX enforces integer share discretization:
$$\Delta Q_i = \text{round}\left( \frac{\text{Value Delta}_i}{P_i} \right)$$
$$\text{Target Shares}_i = \max\left( 0, Q_{current, i} + \Delta Q_i \right)$$

### 2.3 Order Categorization
- If $\Delta Q_i > 0$: `BUY` order generated.
- If $\Delta Q_i < 0$: `SELL` order generated with quantity $|\Delta Q_i|$.
- If $\Delta Q_i = 0$: `HOLD` (no transaction required).

---

## 3. Risk & Portfolio Constraints

The engine evaluates and enforces four layers of risk constraints:

1. **Maximum Position Limit:**
   $$w_{target, i} \le \text{max\_position\_weight\_pct}$$
   Default: 30.0%. If any target weight violates this limit, the rebalance simulation is flagged with a warning, or clamped.
2. **Minimum Trade Threshold:**
   $$|\Delta Q_i| \times P_i \ge \text{min\_trade\_size\_inr}$$
   Default: ₹1,000. De minimis adjustments below this threshold are omitted to prevent transaction friction from destroying capital.
3. **Target Cash Reserve:**
   $$\text{Cash Target} = \text{Total Equity} \times \left( \frac{\text{target\_cash\_reserve\_pct}}{100} \right)$$
   Allocated equity across holdings is constrained to $1.0 - \frac{\text{target\_cash\_reserve\_pct}}{100}$.
4. **Execution Cash Conservation:**
   $$\text{Post-Rebalance Cash} = \text{Current Cash} + \text{Sell Turnover} - \text{Buy Turnover} - \text{Total Costs}$$
   If projected post-rebalance cash is negative, buy order quantities are dynamically scaled back to maintain cash solvency.

---

## 4. Transaction Cost & Slippage Modeling

Aurxon QuantX applies the verified Indian statutory cost schedule (`2024.2-STATUTORY`):
1. **Securities Transaction Tax (STT):**
   - Delivery Buy: 0.1% of trade value.
   - Delivery Sell: 0.1% of trade value.
2. **Stamp Duty:** 0.015% on Delivery Buy.
3. **NSE Exchange Transaction Charges:** 0.00297% on both sides.
4. **SEBI Turnover Fee:** ₹10 per ₹1 Crore (0.0001%).
5. **Goods and Services Tax (GST):** 18% applied on brokerage and transaction fees.
6. **Execution Slippage:** Configurable parameter (default: 5.0 bps / 0.05%) added to buy execution prices and subtracted from sell execution prices.

$$\text{Total Friction} = \sum_{\text{trades}} \left( \text{Statutory Costs} + \text{Slippage Drag} \right)$$

---

## 5. Execution Sequencing & Virtual Paper Ledger

When the user initiates simulated rebalancing (`execute-paper`):
1. **Sells First:** Sell orders are executed first to release locked capital into the virtual cash balance.
2. **Buys Second:** Buy orders are executed sequentially using liberated cash.
3. **Idempotency Protection:** Each generated rebalance transaction carries a cryptographically unique `idempotency_key` (`REBAL_{portfolio_id}_{timestamp}_{symbol}_{action}`).
4. **Paper Trading Isolation:** Fills are recorded exclusively in `data/aurxon_paper_portfolio.sqlite`.

---

## 6. Real-Money Trading Boundary

```
ENABLE_REAL_TRADING = false
```
The rebalancing engine contains **ZERO** network connectivity to broker APIs (Zerodha Kite, Upstox, Angel One, Interactive Brokers). Real-money trading is disabled at the core architecture layer.
