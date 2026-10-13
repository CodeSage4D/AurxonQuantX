"""AURXON Paper-Only Rebalancing Simulator.
Workstream D: Evaluates current vs target portfolio allocation, enforces risk constraints,
models Indian statutory transaction costs and slippage, and generates actionable simulated trades.
"""

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.portfolio_intelligence import (
    PricingStatus,
    ProposedTrade,
    RebalanceConstraints,
    RebalancingSimulationResult,
)
from app.schemas.paper_trading import (
    PaperOrderRequest,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
    PaperPortfolioState,
)
from app.trading.costs import IndianTransactionCostModel, InstrumentType, TradeAction
from app.trading.paper_manager import PaperPortfolioManager
from app.market_data.nse_connector import NSEDataConnector
from app.trading.portfolio_analytics import INDIAN_SECTOR_MAP


class PaperRebalancingEngine:
    """Simulates multi-asset portfolio rebalancing strictly within the paper trading sandbox."""

    def __init__(
        self,
        cost_model: Optional[IndianTransactionCostModel] = None,
        connector: Optional[NSEDataConnector] = None,
        paper_manager: Optional[PaperPortfolioManager] = None,
    ):
        self.cost_model = cost_model or IndianTransactionCostModel(slippage_bps=5.0)
        self.connector = connector or NSEDataConnector()
        self.paper_manager = paper_manager

    def simulate_rebalance(
        self,
        current_state: PaperPortfolioState,
        target_weights: Dict[str, float],
        constraints: Optional[RebalanceConstraints] = None,
    ) -> RebalancingSimulationResult:
        """Simulates allocation adjustments, constraints checks, and integer trade rounding.
        
        Args:
            current_state: Mark-to-market snapshot of the paper portfolio.
            target_weights: Dictionary mapping clean symbol (e.g. 'RELIANCE') to target weight (0.0 to 1.0).
            constraints: Rebalancing boundaries and cost parameters.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        limits = constraints or RebalanceConstraints()
        total_equity = current_state.total_equity
        curr_cash = current_state.current_cash

        warnings_and_qualifications: List[str] = []

        # 1. Validation of inputs
        if total_equity <= 0:
            return RebalancingSimulationResult(
                portfolio_id=current_state.portfolio_id,
                simulation_timestamp=now_iso,
                status="BLOCKED",
                current_cash=curr_cash,
                projected_post_rebalance_cash=curr_cash,
                projected_cash_reserve_pct=100.0,
                constraints_applied=limits,
                qualifications_and_warnings=["Total portfolio equity is zero or negative. Rebalancing impossible."],
            )

        # Check target weights sum
        sum_targets = sum(target_weights.values())
        cash_reserve_target = limits.target_cash_reserve_pct / 100.0
        max_equity_allocation = 1.0 - cash_reserve_target

        if sum_targets > max_equity_allocation + 1e-4:
            scale_factor = max_equity_allocation / sum_targets
            warnings_and_qualifications.append(
                f"Target weights sum ({sum_targets * 100.0:.1f}%) exceeds allowable equity ceiling "
                f"({max_equity_allocation * 100.0:.1f}%) after reserving {limits.target_cash_reserve_pct:.1f}% cash. "
                f"Weights were proportionally scaled by factor {scale_factor:.4f}."
            )
            target_weights = {s: w * scale_factor for s, w in target_weights.items()}

        # 2. Map current holdings and prices
        all_symbols = set(current_state.positions.keys()).union(set(target_weights.keys()))
        prices: Dict[str, float] = {}
        pricing_statuses: Dict[str, PricingStatus] = {}
        unpriced_symbols: List[str] = []

        for sym in all_symbols:
            clean = sym.strip().upper().replace(".NS", "").replace(".BO", "")
            quote = self.connector.get_market_quote(clean)
            if quote.current_price is not None and quote.current_price > 0:
                prices[clean] = quote.current_price
                if "Benchmark" in quote.data_provider:
                    pricing_statuses[clean] = PricingStatus.BENCHMARK_FIXTURE
                elif "Cached" in quote.data_provider or quote.classification.value == "CACHED_LOCAL":
                    pricing_statuses[clean] = PricingStatus.CACHED
                else:
                    pricing_statuses[clean] = PricingStatus.DELAYED_VERIFIED
            else:
                # Check if position has stored price
                pos = current_state.positions.get(sym)
                if pos and pos.current_price > 0:
                    prices[clean] = pos.current_price
                    pricing_statuses[clean] = PricingStatus.CACHED
                else:
                    unpriced_symbols.append(clean)
                    pricing_statuses[clean] = PricingStatus.UNPRICED

        # If any symbol cannot be priced, qualify or block
        if unpriced_symbols:
            warnings_and_qualifications.append(
                f"Symbols {unpriced_symbols} lack verified market prices. "
                "Simulated rebalancing is qualified: trades for unpriced symbols are blocked to prevent fabricated fills."
            )

        # 3. Calculate current weights and target values
        current_quantities: Dict[str, int] = {
            s.strip().upper().replace(".NS", ""): pos.quantity
            for s, pos in current_state.positions.items()
        }
        current_values: Dict[str, float] = {
            s: current_quantities.get(s, 0) * prices.get(s, 0.0)
            for s in all_symbols
        }
        pre_weights = {
            s: round((current_values[s] / total_equity) * 100.0, 2)
            for s in all_symbols
        }

        # Check concentration constraints on targets
        for s, tw in target_weights.items():
            tw_pct = tw * 100.0
            if tw_pct > limits.max_position_weight_pct:
                warnings_and_qualifications.append(
                    f"Target weight for '{s}' ({tw_pct:.1f}%) exceeds position ceiling ({limits.max_position_weight_pct:.1f}%). "
                    f"Capped at {limits.max_position_weight_pct:.1f}%."
                )
                target_weights[s] = limits.max_position_weight_pct / 100.0

        # Sector concentration check on targets
        target_sector_totals: Dict[str, float] = {}
        for s, tw in target_weights.items():
            sec = INDIAN_SECTOR_MAP.get(s, "Diversified Indian Equities")
            target_sector_totals[sec] = target_sector_totals.get(sec, 0.0) + (tw * 100.0)
        
        for sec, sw in target_sector_totals.items():
            if sw > limits.max_sector_weight_pct:
                warnings_and_qualifications.append(
                    f"Target sector exposure for '{sec}' ({sw:.1f}%) exceeds sector ceiling ({limits.max_sector_weight_pct:.1f}%)."
                )

        # 4. Compute proposed trades
        proposed_trades: List[ProposedTrade] = []
        sells: List[ProposedTrade] = []
        buys: List[ProposedTrade] = []

        total_buy_turnover = 0.0
        total_sell_turnover = 0.0
        total_costs = 0.0

        for s in all_symbols:
            p = prices.get(s)
            curr_qty = current_quantities.get(s, 0)
            target_w = target_weights.get(s, 0.0)
            target_val = total_equity * target_w

            if p is None or p <= 0:
                if curr_qty > 0 or target_w > 0:
                    proposed_trades.append(
                        ProposedTrade(
                            symbol=s,
                            action="HOLD",
                            current_quantity=curr_qty,
                            target_quantity=curr_qty,
                            share_delta=0,
                            estimated_price=0.0,
                            estimated_turnover=0.0,
                            estimated_transaction_costs=0.0,
                            pre_trade_weight_pct=pre_weights.get(s, 0.0),
                            post_trade_weight_pct=pre_weights.get(s, 0.0),
                            reason="Unpriced symbol; rebalancing blocked to protect capital.",
                            pricing_status=PricingStatus.UNPRICED,
                            is_actionable=False,
                            block_reason="Verified market price unavailable.",
                        )
                    )
                continue

            curr_val = curr_qty * p
            val_diff = target_val - curr_val
            
            # Integer share delta (no fractional shares for Indian equity delivery)
            share_delta = int(round(val_diff / p))
            target_qty = curr_qty + share_delta

            if target_qty < 0:
                # Long only constraint
                target_qty = 0
                share_delta = -curr_qty

            trade_turnover = round(abs(share_delta) * p, 2)

            # Minimum trade size filter
            if trade_turnover < limits.min_trade_size_inr:
                continue

            # Calculate statutory Indian transaction costs & slippage
            action_type = "BUY" if share_delta > 0 else "SELL"
            trade_action = TradeAction.BUY if share_delta > 0 else TradeAction.SELL
            
            costs = self.cost_model.calculate_trade_costs(
                action=trade_action,
                raw_price=p,
                quantity=abs(share_delta),
                instrument_type=InstrumentType.EQUITY_DELIVERY,
            )
            est_cost = round(costs.total_costs, 2)
            post_val = target_qty * p
            post_w = round((post_val / total_equity) * 100.0, 2)

            reason_str = (
                f"Underweight by {(target_w * 100.0) - pre_weights[s]:.1f}%; allocate +{abs(share_delta)} shares to meet target {target_w * 100.0:.1f}%."
                if share_delta > 0
                else f"Trim position by {pre_weights[s] - (target_w * 100.0):.1f}%; liquidate {abs(share_delta)} shares to target {target_w * 100.0:.1f}%."
            )

            trade = ProposedTrade(
                symbol=s,
                action=action_type,
                current_quantity=curr_qty,
                target_quantity=target_qty,
                share_delta=abs(share_delta),
                estimated_price=p,
                estimated_turnover=trade_turnover,
                estimated_transaction_costs=est_cost,
                pre_trade_weight_pct=pre_weights.get(s, 0.0),
                post_trade_weight_pct=post_w,
                reason=reason_str,
                pricing_status=pricing_statuses.get(s, PricingStatus.DELAYED_VERIFIED),
                is_actionable=True,
            )

            if action_type == "SELL":
                sells.append(trade)
                total_sell_turnover += trade_turnover
            else:
                buys.append(trade)
                total_buy_turnover += trade_turnover

            total_costs += est_cost

        # Order trades: Sells first to generate liquidity, then Buys, followed by unpriced/blocked holds
        ordered_trades = sells + buys + proposed_trades

        # Cash balance simulation
        # Cash after sells:
        liquidity_from_sells = total_sell_turnover - sum(t.estimated_transaction_costs for t in sells)
        cash_available = curr_cash + liquidity_from_sells
        
        # Cash required for buys:
        capital_needed_for_buys = total_buy_turnover + sum(t.estimated_transaction_costs for t in buys)

        projected_cash = round(cash_available - capital_needed_for_buys, 2)
        target_cash_inr = total_equity * cash_reserve_target

        if projected_cash < target_cash_inr:
            warnings_and_qualifications.append(
                f"Projected post-rebalance cash (₹{projected_cash:,.2f}) falls below target cash reserve "
                f"(₹{target_cash_inr:,.2f}, {limits.target_cash_reserve_pct}%). "
                "Buy allocations may need downscaling if executed."
            )

        projected_cash_pct = round((projected_cash / total_equity) * 100.0, 2) if total_equity > 0 else 0.0
        total_turnover = round(total_buy_turnover + total_sell_turnover, 2)
        portfolio_turnover_pct = round((total_turnover / (2.0 * total_equity)) * 100.0, 2) if total_equity > 0 else 0.0

        # Post-rebalance sector and position weights
        post_weights: Dict[str, float] = {}
        post_sector_weights: Dict[str, float] = {}
        for s in all_symbols:
            # If trade occurred, use target_qty; else current_qty
            traded = next((t for t in ordered_trades if t.symbol == s), None)
            final_q = traded.target_quantity if traded else current_quantities.get(s, 0)
            final_v = final_q * prices.get(s, 0.0)
            final_w = round((final_v / total_equity) * 100.0, 2)
            post_weights[s] = final_w
            sec = INDIAN_SECTOR_MAP.get(s, "Diversified Indian Equities")
            post_sector_weights[sec] = post_sector_weights.get(sec, 0.0) + final_w

        pre_sector_weights: Dict[str, float] = {}
        for s, w in pre_weights.items():
            sec = INDIAN_SECTOR_MAP.get(s, "Diversified Indian Equities")
            pre_sector_weights[sec] = pre_sector_weights.get(sec, 0.0) + w

        status = "QUALIFIED" if warnings_and_qualifications else "FEASIBLE"

        return RebalancingSimulationResult(
            portfolio_id=current_state.portfolio_id,
            simulation_timestamp=now_iso,
            status=status,
            proposed_trades=ordered_trades,
            total_buy_turnover=round(total_buy_turnover, 2),
            total_sell_turnover=round(total_sell_turnover, 2),
            total_estimated_turnover=total_turnover,
            total_estimated_transaction_costs=round(total_costs, 2),
            current_cash=curr_cash,
            projected_post_rebalance_cash=projected_cash,
            projected_cash_reserve_pct=projected_cash_pct,
            portfolio_turnover_pct=portfolio_turnover_pct,
            pre_rebalance_weights=pre_weights,
            post_rebalance_weights=post_weights,
            pre_sector_weights={k: round(v, 2) for k, v in pre_sector_weights.items()},
            post_sector_weights={k: round(v, 2) for k, v in post_sector_weights.items()},
            constraints_applied=limits,
            qualifications_and_warnings=warnings_and_qualifications,
        )

    def execute_paper_rebalancing(
        self,
        simulation: RebalancingSimulationResult,
    ) -> List[Dict[str, Any]]:
        """Executes the proposed rebalancing trades sequentially in the virtual paper ledger.
        Enforces:
        - Sells executed first to generate liquidity.
        - Full statutory transaction cost accounting.
        - Compliance with kill switch and paper risk vetoes.
        """
        if not self.paper_manager:
            raise ValueError("PaperPortfolioManager not configured for execution.")

        if simulation.status == "BLOCKED":
            raise ValueError("Cannot execute a BLOCKED rebalancing simulation.")

        results = []
        # 1. Execute SELLS first
        sells = [t for t in simulation.proposed_trades if t.action == "SELL" and t.is_actionable]
        for t in sells:
            order_req = PaperOrderRequest(
                portfolio_id=simulation.portfolio_id,
                symbol=t.symbol,
                side=PaperOrderSide.SELL,
                quantity=t.share_delta,
                order_type=PaperOrderType.MARKET,
            )
            order_record = self.paper_manager.submit_order(order_req)
            results.append({
                "symbol": t.symbol,
                "action": "SELL",
                "quantity": t.share_delta,
                "order_id": order_record.order_id,
                "status": order_record.status.value,
                "fill_price": order_record.fill_price,
                "transaction_costs": order_record.transaction_costs,
                "rejection_reason": order_record.rejection_reason,
            })

        # 2. Execute BUYS second
        buys = [t for t in simulation.proposed_trades if t.action == "BUY" and t.is_actionable]
        for t in buys:
            order_req = PaperOrderRequest(
                portfolio_id=simulation.portfolio_id,
                symbol=t.symbol,
                side=PaperOrderSide.BUY,
                quantity=t.share_delta,
                order_type=PaperOrderType.MARKET,
            )
            order_record = self.paper_manager.submit_order(order_req)
            results.append({
                "symbol": t.symbol,
                "action": "BUY",
                "quantity": t.share_delta,
                "order_id": order_record.order_id,
                "status": order_record.status.value,
                "fill_price": order_record.fill_price,
                "transaction_costs": order_record.transaction_costs,
                "rejection_reason": order_record.rejection_reason,
            })

        # Record a snapshot post-rebalance
        self.paper_manager.record_portfolio_snapshot(simulation.portfolio_id)
        return results


paper_rebalancing_engine = PaperRebalancingEngine()
