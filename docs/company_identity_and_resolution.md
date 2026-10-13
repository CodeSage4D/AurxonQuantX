# AURXONQuant — Company Identity & Resolution Engine

**Phase:** 4 — Live Data & Company Research Intelligence Engine  
**Module:** `backend/app/research/company_resolver.py`  
**API Endpoint:** `GET /api/v1/company/resolve?q={query}`  
**Status:** VALIDATED & DEPLOYED

---

## 1. Objectives & Resolution Philosophy

Financial queries frequently contain informal abbreviations ("RIL", "TaMo", "Infy"), historical corporate names ("TELCO", "TISCO"), ISIN codes, or ambiguous conglomerate umbrellas ("Tata", "Bajaj", "HDFC").

**Core Design Rule:**  
AURXON never guesses or silently selects an arbitrary company when a query is ambiguous. When ambiguity is detected, the resolver returns `is_resolved: False`, `is_ambiguous: True`, provides the candidate security list, and generates an operator clarification prompt.

---

## 2. Canonical Security Master Schema

Every resolved corporate security is modeled as a strongly typed `CompanyIdentity`:
- `cin`: Corporate Identification Number (MCA)
- `isin`: International Securities Identification Number (e.g. `INE002A01018`)
- `legal_name`: Statutory registered name (e.g. "Reliance Industries Limited")
- `trade_name`: Recognised brand name (e.g. "Reliance Industries")
- `nse_symbol`: Primary NSE ticker (e.g. `RELIANCE`)
- `bse_code`: BSE Scrip Code (e.g. `500325`)
- `primary_exchange`: Primary trading venue (`NSE` or `BSE`)
- `listing_status`: `ACTIVE_LISTED`, `SUSPENDED`, `DELISTED`, `UNLISTED`
- `security_type`: `EQUITY_SHARES`, `ETF`, `MUTUAL_FUND`, `DEBENTURE`, `REIT_INVIT`
- `sector` / `industry`: Industrial classification
- `aliases`: Recognized aliases and acronyms
- `historical_names`: Verified historical corporate names and former tickers
- `website_ir`: Official investor relations web address

---

## 3. Resolution Priority Order

```
[ Incoming Query ]
       │
       ▼
1. Normalize query (strip "NSE:", "BSE:", ".NS", ".BO", trim whitespace)
       │
       ▼
2. Exact ISIN Match (e.g. INE002A01018 -> RELIANCE)
       │ (No match)
       ▼
3. Exact NSE Ticker Match (e.g. TCS -> Tata Consultancy Services)
       │ (No match)
       ▼
4. Exact BSE Scrip Code Match (e.g. 500325 -> Reliance Industries)
       │ (No match)
       ▼
5. Exact Trade Name or Legal Name Match
       │ (No match)
       ▼
6. Known Alias Match (e.g. "RIL" -> RELIANCE, "SBI" -> SBIN)
       │ (No match)
       ▼
7. Historical Corporate Name Match (e.g. "TELCO" -> TATAMOTORS, "TISCO" -> TATASTEEL)
       │ (No match)
       ▼
8. Multi-Candidate Substring & Umbrella Detection
       ├── Exactly 1 match found -> Resolved
       ├── > 1 match found -> AMBIGUOUS: Return candidate list & clarification prompt
       └── 0 matches found -> UNRESOLVED: Explicit error, zero hallucination
```

---

## 4. Ambiguity Detection Case Studies

| Input Query | Resolution Result | Resolution State | Disambiguation Prompt / Action |
| :--- | :--- | :--- | :--- |
| `RELIANCE` | Reliance Industries Limited | `is_resolved=True` | Immediate resolution |
| `INE467B01029` | Tata Consultancy Services Limited | `is_resolved=True` | Immediate resolution via ISIN |
| `TELCO` | Tata Motors Limited | `is_resolved=True` | Resolved via historical name master |
| `Tata` | Multiple Candidates | `is_ambiguous=True` | *"Found 3 matching securities: TCS (TCS), Tata Motors (TATAMOTORS), Tata Steel (TATASTEEL). Please specify the exact entity or ticker."* |
| `Bajaj` | Multiple Candidates | `is_ambiguous=True` | *"Found 3 matching securities: Bajaj Finance (BAJFINANCE), Bajaj Finserv (BAJAJFINSV), Bajaj Auto (BAJAJ-AUTO)."* |
| `XYZ_UNKNOWN` | None | `is_resolved=False` | *"No matching listed Indian security found for 'XYZ_UNKNOWN'."* |

---

## 5. Verification Evidence

Verified in automated test suite `test_phase_4_company_research.py`:
- `test_company_resolution_exact_symbols`: PASS
- `test_company_resolution_isin_and_historical_names`: PASS
- `test_company_resolution_ambiguity_detection`: PASS
- `test_company_resolution_unresolved`: PASS
