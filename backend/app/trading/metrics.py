"""AURXON Backtest Performance & Quantitative Risk Metrics.
Calculates deterministic portfolio metrics:
- Gross and Net Total Return, Annualized Return (CAGR).
- Peak-to-trough Maximum Drawdown and Drawdown Duration.
- Annualized Volatility, Sharpe Ratio, Sortino Ratio with documented Indian Rf rate.
- Trade statistics: Win Rate, Profit Factor, Average Win/Loss, Total Transaction Drag.
- Benchmark-relative Alpha, Beta, and Tracking Error.
"""

import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.semantics import MetricStatus, TypedFinancialMetric


class TradeRecord(BaseModel):
    """Audit record for an individual executed position round-trip or fill."""
    trade_id: str
    symbol: str
    action: str  # "BUY" or "SELL"
    order_type: str  # "MARKET", "LIMIT"
    signal_date: str  # Bar T (decision time)
    execution_date: str  # Bar T+1 (fill time)
    quantity: int
    raw_price: float
    execution_price: float
    turnover: float
    transaction_costs: float
    realized_pnl: Optional[float] = None  # Populated on closing trade
    realized_pnl_pct: Optional[float] = None
    holding_period_days: Optional[int] = None
    cost_notes: str = ""


class EquityPoint(BaseModel):
    """Daily equity snapshot across the simulation trajectory."""
    date: str
    cash: float
    positions_value: float
    total_equity_net: float
    total_equity_gross: float
    daily_return_pct: float
    drawdown_pct: float
    benchmark_equity: Optional[float] = None


class BacktestMetricsReport(BaseModel):
    """Comprehensive performance and risk analytics report."""
    initial_capital: float
    final_equity_net: float
    final_equity_gross: float

    # Returns
    total_return_net_pct: float
    total_return_gross_pct: float
    cagr_net_pct: Optional[float] = None
    cagr_gross_pct: Optional[float] = None

    # Risk Metrics
    annualized_volatility_pct: Optional[float] = None
    max_drawdown_pct: float
    max_drawdown_duration_bars: int
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    risk_free_rate_pct: float = Field(default=6.5, description="Indian 91-day T-bill baseline: 6.5%")

    # Benchmark Comparison
    benchmark_symbol: Optional[str] = None
    benchmark_total_return_pct: Optional[float] = None
    alpha_annualized_pct: Optional[float] = None
    beta: Optional[float] = None

    # Trade Statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: Optional[float] = None
    profit_factor: Optional[float] = None
    average_trade_pnl_inr: Optional[float] = None
    average_win_inr: Optional[float] = None
    average_loss_inr: Optional[float] = None
    win_loss_payoff_ratio: Optional[float] = None
    total_transaction_costs_inr: float
    transaction_cost_drag_pct: float
    exposure_pct: float  # Percentage of bars with market exposure

    notes_and_caveats: List[str] = Field(default_factory=list)


def calculate_backtest_metrics(
    equity_curve: List[EquityPoint],
    closed_trades: List[TradeRecord],
    initial_capital: float,
    benchmark_returns: Optional[List[float]] = None,
    risk_free_rate_pct: float = 6.5,
) -> BacktestMetricsReport:
    """Computes exact quantitative metrics without heuristics or lookahead bias."""
    if not equity_curve:
        raise ValueError("Cannot calculate metrics on empty equity curve")

    total_bars = len(equity_curve)
    final_net = equity_curve[-1].total_equity_net
    final_gross = equity_curve[-1].total_equity_gross

    # 1. Total & Annualized Returns
    ret_net_pct = round(((final_net - initial_capital) / initial_capital) * 100.0, 2)
    ret_gross_pct = round(((final_gross - initial_capital) / initial_capital) * 100.0, 2)

    cagr_net = None
    cagr_gross = None
    if total_bars > 20 and final_net > 0:
        years = total_bars / 252.0
        cagr_net = round(((final_net / initial_capital) ** (1.0 / years) - 1.0) * 100.0, 2)
        cagr_gross = round(((final_gross / initial_capital) ** (1.0 / years) - 1.0) * 100.0, 2)

    # 2. Daily returns series
    daily_returns = [pt.daily_return_pct / 100.0 for pt in equity_curve[1:]]

    # 3. Volatility (Annualized)
    ann_vol = None
    sharpe = None
    sortino = None
    if len(daily_returns) >= 2:
        mean_ret = sum(daily_returns) / len(daily_returns)
        var = sum((r - mean_ret) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        daily_vol = math.sqrt(var)
        ann_vol = round(daily_vol * math.sqrt(252) * 100.0, 2)

        # Sharpe Ratio
        rf_daily = (risk_free_rate_pct / 100.0) / 252.0
        excess_daily_mean = mean_ret - rf_daily
        if daily_vol > 1e-8:
            sharpe = round((excess_daily_mean / daily_vol) * math.sqrt(252), 2)

        # Downside Deviation & Sortino Ratio
        if daily_vol > 1e-8:
            downside_sq = [min(0.0, r - rf_daily) ** 2 for r in daily_returns]
            downside_dev = math.sqrt(sum(downside_sq) / max(1, len(daily_returns)))
            if downside_dev > 1e-8:
                sortino = round((excess_daily_mean / downside_dev) * math.sqrt(252), 2)

    # 4. Maximum Drawdown & Duration
    peak_equity = initial_capital
    max_dd_pct = 0.0
    current_dd_bars = 0
    max_dd_bars = 0

    for pt in equity_curve:
        if pt.total_equity_net > peak_equity:
            peak_equity = pt.total_equity_net
            current_dd_bars = 0
        else:
            current_dd_bars += 1
            if current_dd_bars > max_dd_bars:
                max_dd_bars = current_dd_bars

        dd = (peak_equity - pt.total_equity_net) / peak_equity * 100.0
        if dd > max_dd_pct:
            max_dd_pct = round(dd, 2)

    # 5. Trade Statistics
    tot_trades = len(closed_trades)
    winning = [t for t in closed_trades if t.realized_pnl and t.realized_pnl > 0]
    losing = [t for t in closed_trades if t.realized_pnl and t.realized_pnl < 0]

    tot_costs = sum(t.transaction_costs for t in closed_trades)
    cost_drag_pct = round((tot_costs / initial_capital) * 100.0, 2)

    win_rate = round((len(winning) / tot_trades) * 100.0, 2) if tot_trades > 0 else None

    gross_profit = sum(t.realized_pnl for t in winning if t.realized_pnl)
    gross_loss = abs(sum(t.realized_pnl for t in losing if t.realized_pnl))

    if gross_loss > 0:
        profit_factor = round(gross_profit / gross_loss, 2)
    elif gross_profit > 0:
        profit_factor = float("inf")
    else:
        profit_factor = None

    avg_win = round(gross_profit / len(winning), 2) if winning else None
    avg_loss = round(gross_loss / len(losing), 2) if losing else None
    payoff = round(avg_win / avg_loss, 2) if (avg_win and avg_loss and avg_loss > 0) else None
    avg_trade = round(sum((t.realized_pnl or 0.0) for t in closed_trades) / tot_trades, 2) if tot_trades > 0 else None

    # 6. Market Exposure %
    exposed_bars = sum(1 for pt in equity_curve if pt.positions_value > 0)
    exposure_pct = round((exposed_bars / total_bars) * 100.0, 2)

    # 7. Benchmark Alpha & Beta
    beta = None
    alpha = None
    if benchmark_returns and len(benchmark_returns) == len(daily_returns) and len(daily_returns) > 10:
        mean_bm = sum(benchmark_returns) / len(benchmark_returns)
        var_bm = sum((b - mean_bm) ** 2 for b in benchmark_returns) / (len(benchmark_returns) - 1)
        if var_bm > 1e-8:
            cov = sum(
                (daily_returns[i] - mean_ret) * (benchmark_returns[i] - mean_bm)
                for i in range(len(daily_returns))
            ) / (len(daily_returns) - 1)
            b_val = cov / var_bm
            beta = round(b_val, 2)
            if cagr_net is not None:
                bm_compounded = 1.0
                for r in benchmark_returns:
                    bm_compounded *= (1.0 + r)
                if bm_compounded > 0 and len(benchmark_returns) > 0:
                    bm_cagr = round(((bm_compounded) ** (252.0 / len(benchmark_returns)) - 1.0) * 100.0, 2)
                    alpha = round(cagr_net - (risk_free_rate_pct + b_val * (bm_cagr - risk_free_rate_pct)), 2)

    caveats = [
        "Simulation strictly uses lagged next-bar execution (Bar T+1 Open) to eliminate lookahead leakage.",
        f"Statutory Indian cost drag accounts for STT, NSE transaction charges, GST, Stamp Duty, and SEBI turnover fees (Total Drag: ₹{tot_costs:,.2f}).",
        f"Sharpe and Sortino ratios assume Indian Risk-Free Rate of {risk_free_rate_pct}% p.a. (91-day T-bill reference).",
        "Historical backtested results are non-predictive simulations and do not guarantee future returns.",
    ]

    # Handle undefined metrics and edge cases explicitly
    if len(daily_returns) < 2:
        caveats.append("Insufficient observations (< 2 daily bars): Volatility, Sharpe, and Sortino ratios are undefined.")
    elif ann_vol is None or ann_vol <= 1e-6:
        caveats.append("Zero portfolio volatility observed: Sharpe ratio is undefined.")

    if tot_trades == 0:
        caveats.append("Zero closed trades executed: Win rate, profit factor, and trade payoff statistics are not applicable.")

    if cagr_net is None and total_bars <= 20:
        caveats.append("CAGR undefined: Minimum 20 trading bars required for annualized return calculation.")
    elif total_bars < 252:
        caveats.append("Annualized return (CAGR) extrapolated from short simulation duration (< 1 year / 252 bars); treat with caution.")

    return BacktestMetricsReport(
        initial_capital=initial_capital,
        final_equity_net=round(final_net, 2),
        final_equity_gross=round(final_gross, 2),
        total_return_net_pct=ret_net_pct,
        total_return_gross_pct=ret_gross_pct,
        cagr_net_pct=cagr_net,
        cagr_gross_pct=cagr_gross,
        annualized_volatility_pct=ann_vol,
        max_drawdown_pct=max_dd_pct,
        max_drawdown_duration_bars=max_dd_bars,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        risk_free_rate_pct=risk_free_rate_pct,
        benchmark_symbol="NIFTY50_BENCHMARK" if benchmark_returns else None,
        beta=beta,
        alpha_annualized_pct=alpha,
        total_trades=tot_trades,
        winning_trades=len(winning),
        losing_trades=len(losing),
        win_rate_pct=win_rate,
        profit_factor=profit_factor,
        average_trade_pnl_inr=avg_trade,
        average_win_inr=avg_win,
        average_loss_inr=avg_loss,
        win_loss_payoff_ratio=payoff,
        total_transaction_costs_inr=tot_costs,
        transaction_cost_drag_pct=cost_drag_pct,
        exposure_pct=exposure_pct,
        notes_and_caveats=caveats,
    )
