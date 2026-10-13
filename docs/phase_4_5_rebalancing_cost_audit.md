# Aurxon QuantX — Phase 4.5 Rebalancing & Transaction Cost Audit

## 1. Executive Summary & Verification Context
- **Product Name:** Aurxon QuantX
- **Brand:** AURXON
- **Milestone:** Phase 4.5 — Integrated Portfolio Validation & Release Readiness
- **Module:** `backend/app/trading/rebalancing.py`, `backend/app/trading/costs.py`

This document details the independent audit of trade sizing, integer share lot rounding, statutory friction, execution sequencing, cash solvency conservation, and boundary handling in the paper-only rebalancing engine.

---

## 2. Integer Share Rounding & Discrete Lot Sizing

In Indian equity cash delivery, fractional share transactions are prohibited.
$$\Delta Q_i = \text{int}\left( \text{round}\left( \frac{\text{Target Value}_i - \text{Current Value}_i}{P_i} \right) \right)$$
- If $\Delta Q_i > 0$: `BUY` order generated.
- If $\Delta Q_i < 0$: `SELL` order generated.
- If $|\Delta Q_i| \times P_i < \text{min\_trade\_size\_inr}$ (default: ₹1,000): Omitted to eliminate micro-churn drag.

---

## 3. Statutory Cost Schedule Schedule `2024.2-STATUTORY`

Every simulated rebalancing order evaluates statutory transaction costs:
1. **Securities Transaction Tax (STT):**
   - Delivery Buy: 0.10% of turnover.
   - Delivery Sell: 0.10% of turnover.
2. **Stamp Duty:** 0.015% of turnover (Buy only).
3. **NSE Exchange Transaction Charges:** 0.00297% on both sides.
4. **SEBI Turnover Charges:** ₹10 per ₹1 Crore (0.0001%).
5. **Goods and Services Tax (GST):** 18.0% applied on transaction charges and SEBI turnover fees.
6. **Execution Slippage:** 5.0 basis points (0.05%) added to Buy execution price and subtracted from Sell execution price.

### Verified Numerical Cost Example:
- **Order:** Buy 30 shares of `RELIANCE` @ ₹2,980.50.
  - Fill price with +5.0 bps slippage: $₹2,980.50 \times 1.0005 = ₹2,981.99$.
  - Turnover gross: $30 \times ₹2,981.99 = ₹89,459.70$.
  - STT (0.1%): ₹89.46.
  - Stamp duty (0.015%): ₹13.42.
  - NSE Exchange charges (0.00297%): ₹2.66.
  - SEBI turnover fee: ₹0.09.
  - GST (18% on ₹2.75): ₹0.495.
  - Total statutory cost: $₹89.46 + ₹13.42 + ₹2.66 + ₹0.09 + ₹0.50 = ₹106.13$.

---

## 4. Execution Sequencing & Liquidity Conservation

To avoid spurious rejections due to temporary cash deficits:
1. **Sells First:** The engine sorts all proposed trades so that `SELL` orders execute first, generating virtual cash.
2. **Buys Second:** `BUY` orders execute sequentially with liberated funds.
3. **Solvency Verification:** Projected post-rebalance cash incorporates total statutory drag and slippage. If projected cash falls below target cash reserve, warnings are flagged.

---

## 5. Unpriced Holdings & Non-Actionable Boundary Handling

In Phase 4.5, an important defect was resolved:
- Unpriced securities are appended to the proposed trade list as non-actionable `HOLD` orders with explicit block reason:
  > *"Unpriced symbol; rebalancing blocked to protect capital."*
- Unpriced holdings are never silently liquidated or purchased at fabricated prices.
- Active emergency kill switch strictly vetoes paper rebalancing execution with rejection status `REJECTED`.
