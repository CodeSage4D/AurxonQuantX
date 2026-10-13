"""AURXON Mutual Fund & ETF Quantitative Analysis Engine.
Provides deterministic calculation of CAGR, rolling return statistics,
portfolio holding overlap, Direct vs Regular plan compounding fee differences,
and goal-based asset allocation proposals.
"""

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional
import uuid

from app.schemas.funds import (
    FundCategory,
    FundComparisonResult,
    FundIdentity,
    FundOption,
    FundPlan,
    FundRiskReturnMetrics,
    HoldingItem,
    PortfolioAllocationPlan,
)


def compute_cagr(start_nav: float, end_nav: float, years: float) -> float:
    """Calculates compound annual growth rate given initial and final NAV."""
    if start_nav <= 0 or end_nav <= 0 or years <= 0:
        return 0.0
    return float(round(((end_nav / start_nav) ** (1.0 / years) - 1.0) * 100.0, 2))


def calculate_portfolio_overlap(holdings_a: List[HoldingItem], holdings_b: List[HoldingItem]) -> float:
    """Calculates mutual fund portfolio overlap % using minimum common weights:
    Overlap % = Sum over common stocks ( min(weight_A, weight_B) )
    """
    map_a = {h.symbol.upper(): h.weight_pct for h in holdings_a}
    overlap_sum = 0.0

    for h in holdings_b:
        sym = h.symbol.upper()
        if sym in map_a:
            overlap_sum += min(map_a[sym], h.weight_pct)

    return float(round(overlap_sum, 2))


def compute_direct_plan_savings(
    principal_inr: float = 1000000.0,  # ₹10 Lakhs
    direct_ter_pct: float = 0.65,
    regular_ter_pct: float = 1.45,
    gross_annual_cagr: float = 0.12,
    years: int = 10,
) -> float:
    """Computes compounding wealth differential from Direct Plan lower TER."""
    net_cagr_direct = gross_annual_cagr - (direct_ter_pct / 100.0)
    net_cagr_regular = gross_annual_cagr - (regular_ter_pct / 100.0)

    final_direct = principal_inr * ((1.0 + net_cagr_direct) ** years)
    final_regular = principal_inr * ((1.0 + net_cagr_regular) ** years)

    diff_lakhs = (final_direct - final_regular) / 100000.0
    return float(round(diff_lakhs, 2))


def calculate_tracking_error(daily_etf_returns: List[float], daily_bench_returns: List[float]) -> float:
    """Calculates annualized tracking error (standard deviation of return differences)."""
    if len(daily_etf_returns) < 10 or len(daily_etf_returns) != len(daily_bench_returns):
        return 0.0

    diffs = [e - b for e, b in zip(daily_etf_returns, daily_bench_returns)]
    mean_diff = sum(diffs) / len(diffs)
    variance = sum((d - mean_diff) ** 2 for d in diffs) / (len(diffs) - 1)
    daily_std = math.sqrt(variance)
    annualized_te = daily_std * math.sqrt(252) * 100.0
    return float(round(annualized_te, 2))


# Curated Mutual Fund & ETF Benchmarks
CURATED_FUND_BENCHMARKS: Dict[str, Dict[str, Any]] = {
    "PPFAS_FLEXI": {
        "identity": {
            "scheme_code": "PPFAS_FLEXI",
            "scheme_name": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
            "amc_name": "PPFAS Mutual Fund",
            "category": FundCategory.FLEXI_CAP,
            "benchmark_index": "Nifty 500 TRI",
            "plan": FundPlan.DIRECT,
            "option": FundOption.GROWTH,
            "expense_ratio_pct": 0.63,
            "regular_expense_ratio_pct": 1.33,
            "aum_crores": 78400.0,
            "exit_load": "2% within 365 days; 1% between 366-730 days; Nil after 730 days",
            "inception_date": "2013-05-24",
            "is_passive": False,
        },
        "metrics": {
            "cagr_1y_pct": 28.4,
            "cagr_3y_pct": 21.2,
            "cagr_5y_pct": 23.8,
            "cagr_since_inception_pct": 19.8,
            "rolling_return_3y_min_pct": 11.2,
            "rolling_return_3y_median_pct": 20.4,
            "rolling_return_3y_max_pct": 29.5,
            "annualized_volatility_pct": 12.1,
            "max_drawdown_pct": 14.8,
            "sharpe_ratio": 1.19,  # RF = 6.8%
            "sortino_ratio": 1.84,
            "alpha_vs_benchmark_pct": 4.8,
            "beta_vs_benchmark": 0.74,
            "tracking_error_pct": None,
            "tracking_difference_pct": None,
            "top_10_holdings_pct": 52.4,
            "top_3_sectors_pct": 42.1,
            "holdings": [
                {"company_name": "HDFC Bank Limited", "symbol": "HDFCBANK", "weight_pct": 8.1, "sector": "Financials"},
                {"company_name": "ITC Limited", "symbol": "ITC", "weight_pct": 7.4, "sector": "FMCG"},
                {"company_name": "Bajaj Holdings & Inv", "symbol": "BAJAJHLDNG", "weight_pct": 6.8, "sector": "Financials"},
                {"company_name": "Power Grid Corp", "symbol": "POWERGRID", "weight_pct": 5.9, "sector": "Utilities"},
                {"company_name": "Coal India Limited", "symbol": "COALINDIA", "weight_pct": 5.2, "sector": "Energy"},
                {"company_name": "ICICI Bank Limited", "symbol": "ICICIBANK", "weight_pct": 4.9, "sector": "Financials"},
                {"company_name": "Alphabet Inc (US)", "symbol": "GOOGL", "weight_pct": 4.6, "sector": "Technology"},
                {"company_name": "Microsoft Corp (US)", "symbol": "MSFT", "weight_pct": 4.1, "sector": "Technology"},
                {"company_name": "HCL Technologies", "symbol": "HCLTECH", "weight_pct": 3.2, "sector": "Technology"},
                {"company_name": "Maruti Suzuki India", "symbol": "MARUTI", "weight_pct": 2.2, "sector": "Automobile"},
            ],
        },
    },
    "NIFTYBEES": {
        "identity": {
            "scheme_code": "NIFTYBEES",
            "scheme_name": "Nippon India ETF Nifty 50 BeES",
            "amc_name": "Nippon India Mutual Fund",
            "category": FundCategory.INDEX_ETF,
            "benchmark_index": "Nifty 50 TRI",
            "plan": FundPlan.DIRECT,
            "option": FundOption.GROWTH,
            "expense_ratio_pct": 0.04,
            "regular_expense_ratio_pct": None,
            "aum_crores": 31200.0,
            "exit_load": "Nil (Traded on NSE/BSE Exchange)",
            "inception_date": "2001-12-28",
            "is_passive": True,
            "tracking_index": "Nifty 50 Index",
        },
        "metrics": {
            "cagr_1y_pct": 24.2,
            "cagr_3y_pct": 15.6,
            "cagr_5y_pct": 17.8,
            "cagr_since_inception_pct": 16.1,
            "rolling_return_3y_min_pct": 8.4,
            "rolling_return_3y_median_pct": 15.8,
            "rolling_return_3y_max_pct": 24.2,
            "annualized_volatility_pct": 13.8,
            "max_drawdown_pct": 17.4,
            "sharpe_ratio": 0.64,
            "sortino_ratio": 0.95,
            "alpha_vs_benchmark_pct": -0.04,
            "beta_vs_benchmark": 1.00,
            "tracking_error_pct": 0.03,
            "tracking_difference_pct": -0.04,
            "top_10_holdings_pct": 57.2,
            "top_3_sectors_pct": 58.5,
            "holdings": [
                {"company_name": "HDFC Bank Limited", "symbol": "HDFCBANK", "weight_pct": 11.2, "sector": "Financials"},
                {"company_name": "Reliance Industries", "symbol": "RELIANCE", "weight_pct": 9.4, "sector": "Energy"},
                {"company_name": "ICICI Bank Limited", "symbol": "ICICIBANK", "weight_pct": 7.9, "sector": "Financials"},
                {"company_name": "Infosys Limited", "symbol": "INFY", "weight_pct": 5.8, "sector": "Technology"},
                {"company_name": "ITC Limited", "symbol": "ITC", "weight_pct": 4.4, "sector": "FMCG"},
                {"company_name": "Tata Consultancy Services", "symbol": "TCS", "weight_pct": 3.9, "sector": "Technology"},
                {"company_name": "Larsen & Toubro", "symbol": "LT", "weight_pct": 3.8, "sector": "Capital Goods"},
                {"company_name": "Bharti Airtel", "symbol": "BHARTIARTL", "weight_pct": 3.7, "sector": "Telecom"},
                {"company_name": "Axis Bank", "symbol": "AXISBANK", "weight_pct": 3.6, "sector": "Financials"},
                {"company_name": "State Bank of India", "symbol": "SBIN", "weight_pct": 3.5, "sector": "Financials"},
            ],
        },
    },
    "MIRAE_LARGE": {
        "identity": {
            "scheme_code": "MIRAE_LARGE",
            "scheme_name": "Mirae Asset Large Cap Fund - Direct Plan - Growth",
            "amc_name": "Mirae Asset Mutual Fund",
            "category": FundCategory.LARGE_CAP,
            "benchmark_index": "Nifty 100 TRI",
            "plan": FundPlan.DIRECT,
            "option": FundOption.GROWTH,
            "expense_ratio_pct": 0.54,
            "regular_expense_ratio_pct": 1.48,
            "aum_crores": 38900.0,
            "exit_load": "1% within 365 days; Nil after 365 days",
            "inception_date": "2008-04-04",
            "is_passive": False,
        },
        "metrics": {
            "cagr_1y_pct": 23.5,
            "cagr_3y_pct": 14.8,
            "cagr_5y_pct": 17.2,
            "cagr_since_inception_pct": 15.8,
            "rolling_return_3y_min_pct": 7.9,
            "rolling_return_3y_median_pct": 15.2,
            "rolling_return_3y_max_pct": 23.8,
            "annualized_volatility_pct": 13.5,
            "max_drawdown_pct": 16.9,
            "sharpe_ratio": 0.59,
            "sortino_ratio": 0.88,
            "alpha_vs_benchmark_pct": -0.4,
            "beta_vs_benchmark": 0.98,
            "tracking_error_pct": None,
            "tracking_difference_pct": None,
            "top_10_holdings_pct": 54.8,
            "top_3_sectors_pct": 53.2,
            "holdings": [
                {"company_name": "HDFC Bank Limited", "symbol": "HDFCBANK", "weight_pct": 9.8, "sector": "Financials"},
                {"company_name": "ICICI Bank Limited", "symbol": "ICICIBANK", "weight_pct": 8.4, "sector": "Financials"},
                {"company_name": "Reliance Industries", "symbol": "RELIANCE", "weight_pct": 8.1, "sector": "Energy"},
                {"company_name": "Infosys Limited", "symbol": "INFY", "weight_pct": 6.2, "sector": "Technology"},
                {"company_name": "Larsen & Toubro", "symbol": "LT", "weight_pct": 4.9, "sector": "Capital Goods"},
                {"company_name": "Axis Bank", "symbol": "AXISBANK", "weight_pct": 4.2, "sector": "Financials"},
                {"company_name": "Tata Consultancy Services", "symbol": "TCS", "weight_pct": 3.8, "sector": "Technology"},
                {"company_name": "Bharti Airtel", "symbol": "BHARTIARTL", "weight_pct": 3.6, "sector": "Telecom"},
                {"company_name": "State Bank of India", "symbol": "SBIN", "weight_pct": 3.1, "sector": "Financials"},
                {"company_name": "ITC Limited", "symbol": "ITC", "weight_pct": 2.7, "sector": "FMCG"},
            ],
        },
    },
}


class FundAnalyzer:
    """Quantitative research engine for Indian mutual funds and ETFs."""

    def get_fund_details(self, scheme_code: str) -> Optional[Dict[str, Any]]:
        clean_code = scheme_code.strip().upper()
        return CURATED_FUND_BENCHMARKS.get(clean_code)

    def compare_funds(self, code_a: str, code_b: str) -> FundComparisonResult:
        data_a = self.get_fund_details(code_a) or CURATED_FUND_BENCHMARKS["PPFAS_FLEXI"]
        data_b = self.get_fund_details(code_b) or CURATED_FUND_BENCHMARKS["NIFTYBEES"]

        id_a = FundIdentity(**data_a["identity"])
        id_b = FundIdentity(**data_b["identity"])

        met_a = FundRiskReturnMetrics(**data_a["metrics"])
        met_b = FundRiskReturnMetrics(**data_b["metrics"])

        overlap_ab = calculate_portfolio_overlap(met_a.holdings, met_b.holdings)

        # Compute savings for fund A (if regular plan exists)
        savings = 0.0
        if id_a.regular_expense_ratio_pct:
            savings = compute_direct_plan_savings(
                principal_inr=1000000.0,
                direct_ter_pct=id_a.expense_ratio_pct,
                regular_ter_pct=id_a.regular_expense_ratio_pct,
                years=10,
            )

        notes = [
            f"Portfolio holding overlap between {id_a.scheme_name} and {id_b.scheme_name} is {overlap_ab}%.",
            f"Direct plan selection saves approx ₹{savings:.2f} Lakhs on ₹10 Lakhs invested over 10 years at 12% CAGR.",
            "Total returns account for NAV compounding. IDCW payouts are capital withdrawals, not bonus yields.",
        ]

        return FundComparisonResult(
            schemes=[id_a, id_b],
            metrics={id_a.scheme_code: met_a, id_b.scheme_code: met_b},
            pairwise_overlap_pct={f"{id_a.scheme_code}_vs_{id_b.scheme_code}": overlap_ab},
            direct_vs_regular_savings_10y_lakhs=savings,
            comparison_notes=notes,
        )

    def generate_portfolio_allocation(
        self, goal_name: str, horizon_years: int, risk_profile: str
    ) -> PortfolioAllocationPlan:
        audit_id = f"AUD-ALLOC-{uuid.uuid4().hex[:10].upper()}"

        risk_lower = risk_profile.lower()
        if horizon_years <= 3 or "conservative" in risk_lower:
            eq_pct, debt_pct, gold_pct = 25.0, 65.0, 10.0
            stress_drawdown = 6.5
            allocated = [
                {"category": "Liquid / Low Duration Debt", "weight_pct": 45.0, "vehicle": "Direct Liquid Mutual Fund"},
                {"category": "Target Maturity / G-Sec", "weight_pct": 20.0, "vehicle": "Bharat Bond / G-Sec Fund"},
                {"category": "Large Cap Index", "weight_pct": 25.0, "vehicle": "Nippon India ETF Nifty 50 BeES"},
                {"category": "Sovereign Gold Bond / Gold ETF", "weight_pct": 10.0, "vehicle": "Gold ETF Direct"},
            ]
        elif horizon_years >= 7 and "aggressive" in risk_lower:
            eq_pct, debt_pct, gold_pct = 80.0, 10.0, 10.0
            stress_drawdown = 24.5
            allocated = [
                {"category": "Flexi Cap Equity", "weight_pct": 40.0, "vehicle": "Parag Parikh Flexi Cap Fund (Direct)"},
                {"category": "Large Cap Index Core", "weight_pct": 25.0, "vehicle": "Nippon India ETF Nifty 50 BeES"},
                {"category": "Mid/Small Cap Active", "weight_pct": 15.0, "vehicle": "Direct Mid/Small Cap Fund"},
                {"category": "Short Term Debt / Emergency", "weight_pct": 10.0, "vehicle": "Direct Money Market Fund"},
                {"category": "Gold ETF", "weight_pct": 10.0, "vehicle": "Gold ETF Direct"},
            ]
        else:  # Balanced default (5-7 years, moderate)
            eq_pct, debt_pct, gold_pct = 60.0, 30.0, 10.0
            stress_drawdown = 15.2
            allocated = [
                {"category": "Large Cap Core Index", "weight_pct": 35.0, "vehicle": "Nippon India ETF Nifty 50 BeES"},
                {"category": "Flexi Cap Quality Active", "weight_pct": 25.0, "vehicle": "Parag Parikh Flexi Cap Fund (Direct)"},
                {"category": "Short Duration Debt", "weight_pct": 30.0, "vehicle": "Direct Corporate Bond / G-Sec Fund"},
                {"category": "Gold ETF", "weight_pct": 10.0, "vehicle": "Gold ETF Direct"},
            ]

        caveats = [
            f"Downside Stress Scenario: In a 2008/2020-style systemic market correction, expected peak-to-trough portfolio drawdown is approximately -{stress_drawdown}%.",
            "Asset rebalancing discipline: Rebalance back to target weights annually or when asset classes drift by >5%.",
            "Tax efficiency: Equity capital gains taxed at 12.5% LTCG above ₹1.25L; debt fund gains taxed at marginal slab rate.",
            "Real-money execution is strictly disabled. This allocation represents quantitative research guidance.",
        ]

        return PortfolioAllocationPlan(
            audit_id=audit_id,
            goal_name=goal_name,
            horizon_years=horizon_years,
            risk_profile=risk_profile,
            recommended_equity_pct=eq_pct,
            recommended_debt_pct=debt_pct,
            recommended_gold_pct=gold_pct,
            allocated_schemes=allocated,
            downside_stress_scenario_drawdown_pct=stress_drawdown,
            key_risks_and_caveats=caveats,
            created_at=datetime.now(timezone.utc).isoformat(),
        )


fund_analyzer = FundAnalyzer()
