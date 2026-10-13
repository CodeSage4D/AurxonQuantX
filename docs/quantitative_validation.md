# AURXONQuant — Deterministic Quantitative Validation

**Phase:** 4 — Live Data & Company Research Intelligence Engine  
**Module:** `backend/app/analytics/company_quant.py`  
**Status:** VALIDATED & VERIFIED

---

## 1. Mathematical Definitions & Formulas

All quantitative metrics are implemented deterministically in pure Python without non-deterministic approximations:

### 1.1 Period Returns
$$\text{Return}_{\text{period}} = \left( \frac{\text{Close}_{\text{latest}}}{\text{Close}_{T - k}} - 1 \right) \times 100\%$$
- 1-Month ($k = 21$ trading days)
- 6-Month ($k = 126$ trading days)
- 1-Year ($k = 252$ trading days)

### 1.2 Annualized Volatility
$$\sigma_{\text{ann}} = \sqrt{\frac{1}{N-1} \sum_{i=1}^N (R_i - \bar{R})^2} \times \sqrt{252} \times 100\%$$
- Evaluated over a rolling 252-day window. Returns `None` if fewer than 10 valid daily return observations exist.

### 1.3 Maximum Drawdown (1-Year Window)
$$\text{MDD} = \min_{t} \left( \frac{\text{Close}_t - \max_{\tau \le t} \text{Close}_\tau}{\max_{\tau \le t} \text{Close}_\tau} \right)$$
- Measures the single largest peak-to-trough decline over the period.

### 1.4 Trend Regime Classification
- `STRONG_BULLISH`: $\text{Price} > \text{SMA}_{20} > \text{SMA}_{50}$
- `MILD_BULLISH`: $\text{Price} > \text{SMA}_{50}$
- `STRONG_BEARISH`: $\text{Price} < \text{SMA}_{20} < \text{SMA}_{50}$
- `CONSOLIDATION_NEUTRAL`: Otherwise.

### 1.5 Relative Strength vs NIFTY50
$$\text{Excess Return} = \text{Return}_{1\text{M}}(\text{Security}) - \text{Return}_{1\text{M}}(\text{NIFTY50})$$
- $> +3.0\% \implies \text{OUTPERFORMING}$
- $< -3.0\% \implies \text{UNDERPERFORMING}$
- $[-3.0\%, +3.0\%] \implies \text{MARKET\_PERFORM}$

### 1.6 Financial Statement Margins & Ratios
$$\text{EBITDA Margin} = \frac{\text{EBITDA}}{\text{Revenue}} \times 100\%$$
$$\text{PAT Margin} = \frac{\text{PAT}}{\text{Revenue}} \times 100\%$$
$$\text{Debt-to-Equity} = \frac{\text{Total Debt}}{\text{Net Worth}}$$
$$\text{ROE} = \frac{\text{PAT}}{\text{Net Worth}} \times 100\%$$
$$\text{RoCE} = \frac{\text{EBITDA}}{\text{Total Debt} + \text{Net Worth}} \times 100\%$$

---

## 2. Prevention of Methodological Biases

1. **Look-Ahead Bias Elimination**: Moving averages, volatility, and period returns calculate exclusively using historical bars indexed strictly on or before observation time $T$. Future bars are inaccessible to the calculation loop.
2. **Double Adjustment Prevention**: When bars carry `RAW_UNADJUSTED` status, corporate actions are factored via historical lot tracking. When bars are pre-adjusted, corporate action dividends credit cash without rescaling share quantities.
3. **Survivor Bias Control**: Security master supports active, suspended, and delisted securities. Delisted assets remain discoverable with `listing_status = "DELISTED"`.
