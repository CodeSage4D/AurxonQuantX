# AURXONQuant — Company Research Workflow & Specialist Review

**Phase:** 4 — Live Data & Company Research Intelligence Engine  
**Module:** `backend/app/research/company_researcher.py`  
**Frontend View:** `frontend/src/components/CompanyResearchView.tsx`  
**Status:** VALIDATED & DEPLOYED

---

## 1. Research Lifecycle Flow

The company research workflow follows a disciplined 9-stage sequence:

```
[ User Query: Company / Ticker / ISIN ]
                   │
                   ▼
       1. Entity Resolution & Security Master
       (Disambiguation & clarification if needed)
                   │
                   ▼
       2. Market Quote & Fundamentals Ingestion
       (From Store or Verified Connectors)
                   │
                   ▼
       3. Historical OHLCV & Benchmark Alignment
       (Retrieval of 1Y candles & NIFTY50 index)
                   │
                   ▼
       4. Deterministic Quantitative Calculations
       (Returns, Volatility, Max Drawdown, Trend, Valuation)
                   │
                   ▼
       5. Primary Evidence & Regulatory Disclosure Mining
       (BSE/NSE circulars, official filings, verified news)
                   │
                   ▼
       6. Specialist Multi-Role Examination
       (6 independent research perspectives)
                   │
                   ▼
       7. Probabilistic Scenario Synthesis
       (Bull, Base, Bear cases with fair value estimates)
                   │
                   ▼
       8. Paper-Trading Safety & Eligibility Gating
       (Evaluates listing, price freshness, drawdown limits)
                   │
                   ▼
       9. Cryptographic Audit Ledger Chaining
       (Tamper-evident record appended to audit_chain)
```

---

## 2. Six Specialist Roles

| Role | Analyst Persona | Domain Focus | Sample Invalidation Trigger |
| :--- | :--- | :--- | :--- |
| **Fundamentals** | Dr. Raghavan K. | Revenue growth, EBITDA margins, balance sheet debt, cash flows | Operating margin contraction > 300 bps across 2 consecutive quarters |
| **Technicals & Trend** | Arjun Mehta, CMT | Moving average structure (SMA 20/50/200), trend regimes, volume | Breakdown below 52-week low with high institutional volume |
| **Valuation & Quality** | Priya Sengupta, CFA | Trailing P/E, P/B, Graham threshold, DCF fair value, Piotroski F-Score | Multiple derating driven by broad macro equity headwinds |
| **Corporate Events** | Sunil Natarajan | LODR corporate disclosures, dividends, bonus issues, board meetings | Regulatory investigations or adverse tribunal sanctions |
| **Downside & Liquidity Risk**| Vikram Sethi, CRO | Maximum drawdown, secondary market liquidity, transaction costs | Portfolio drawdown circuit breaker triggered (> 15% drop) |
| **Adversarial Counter-Thesis**| Devika Rao | Competitive threats, margin pressures, alternative risk-free assets | Sustained organic revenue acceleration above 20% YoY |

---

## 3. Paper-Trading Consideration Ticket Gating

Before any research dossier can be considered for simulated execution in the paper portfolio, it must be issued a valid `PaperTradingEligibilityTicket`.

### Mandatory Verification Gates:
1. `VALID_ACTIVE_LISTING`: Security must have `listing_status == "ACTIVE_LISTED"`. Delisted or suspended stocks are vetoed immediately.
2. `VALID_MARKET_PRICE`: Non-null, non-zero observed price.
3. `FRESH_MARKET_DATA`: Observation must not be flagged as `STALE_WARNING`.
4. `DRAWDOWN_WITHIN_RISK_CAP`: 1-Year maximum drawdown cannot exceed 50.0%.
5. `ALLOCATION_CAP`: Position sizing is hard-capped at $\le 15.0\%$ of portfolio equity.
