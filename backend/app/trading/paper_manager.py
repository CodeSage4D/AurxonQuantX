"""AURXON Persistent Paper Trading Portfolio Manager.
Implements Stage 2:
- Persistent SQLite virtual cash and portfolio equity ledger with restart recovery.
- Simulated orders, fills, rejections, cancellations, and complete order lifecycle.
- FIFO lot tracking, positions, average cost, realized/unrealized P&L.
- Statutory Indian transaction cost deductions (STT, Stamp Duty, GST, NSE fees, SEBI, slippage).
- Idempotency & duplicate-event protection via idempotency keys.
- Independent risk boundaries and operator kill switch vetoes.
- Strict market data provenance: rejection of unverified/missing feeds without silent substitution.
- Cryptographic chained audit logging for all state-changing events.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.evidence.ledger import audit_ledger
from app.market_data.nse_connector import NSEDataConnector
from app.schemas.market import DataClassification, FreshnessStatus
from app.schemas.paper_trading import (
    CancelOrderRequest,
    KillSwitchRequest,
    PaperCorporateActionRequest,
    PaperEventType,
    PaperOrderRecord,
    PaperOrderRequest,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
    PaperPortfolioState,
    PaperPositionRecord,
    RiskLimits,
)
from app.trading.costs import (
    IndianTransactionCostModel,
    InstrumentType,
    TradeAction,
    default_indian_cost_model,
)
from app.trading.fixtures import (
    NIFTY50_BENCHMARK_SERIES,
    RELIANCE_SERIES,
    TCS_BONUS_SERIES,
)

PAPER_DB_PATH = Path("data/aurxon_paper_portfolio.sqlite")
PAPER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class PaperPortfolioManager:
    """Thread-safe persistent portfolio manager for simulated trading in Indian markets."""

    def __init__(
        self,
        db_path: Path = PAPER_DB_PATH,
        cost_model: Optional[IndianTransactionCostModel] = None,
    ):
        self.db_path = db_path
        self.cost_model = cost_model or default_indian_cost_model
        self.market_connector = NSEDataConnector()
        self._init_db()

    def _init_db(self):
        """Initializes SQLite tables in WAL mode for ACID-compliant persistence."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_portfolios (
                    portfolio_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    initial_cash REAL NOT NULL,
                    current_cash REAL NOT NULL,
                    peak_equity REAL NOT NULL DEFAULT 0.0,
                    kill_switch_active INTEGER NOT NULL DEFAULT 0,
                    risk_limits_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            try:
                conn.execute("ALTER TABLE paper_portfolios ADD COLUMN peak_equity REAL NOT NULL DEFAULT 0.0")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE paper_portfolios ADD COLUMN user_id TEXT DEFAULT 'USR_SYSTEM'")
            except Exception:
                pass
            conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolios_user ON paper_portfolios(user_id)")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_positions (
                    portfolio_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    average_cost REAL NOT NULL,
                    current_price REAL NOT NULL,
                    realized_pnl REAL NOT NULL DEFAULT 0.0,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (portfolio_id, symbol)
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_orders (
                    order_id TEXT PRIMARY KEY,
                    idempotency_key TEXT UNIQUE,
                    portfolio_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    limit_price REAL,
                    status TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    filled_at TEXT,
                    fill_price REAL,
                    executed_quantity INTEGER NOT NULL DEFAULT 0,
                    turnover REAL NOT NULL DEFAULT 0.0,
                    transaction_costs REAL NOT NULL DEFAULT 0.0,
                    realized_pnl REAL NOT NULL DEFAULT 0.0,
                    cost_breakdown_json TEXT,
                    rejection_reason TEXT,
                    data_provenance TEXT NOT NULL,
                    data_classification TEXT NOT NULL,
                    freshness_status TEXT NOT NULL,
                    is_demonstration INTEGER NOT NULL DEFAULT 1,
                    notes TEXT
                )
                """
            )
            try:
                conn.execute("ALTER TABLE paper_orders ADD COLUMN realized_pnl REAL NOT NULL DEFAULT 0.0")
            except Exception:
                pass
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_port ON paper_orders(portfolio_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON paper_orders(status)")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_lots (
                    lot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    buy_order_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    remaining_quantity INTEGER NOT NULL,
                    buy_price REAL NOT NULL,
                    buy_costs REAL NOT NULL,
                    buy_date TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_lots_symbol ON paper_lots(portfolio_id, symbol)")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_audit_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    idempotency_key TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_portfolio_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id TEXT NOT NULL,
                    total_equity REAL NOT NULL,
                    current_cash REAL NOT NULL,
                    positions_value REAL NOT NULL,
                    total_unrealized_pnl REAL NOT NULL,
                    total_realized_pnl REAL NOT NULL,
                    positions_count INTEGER NOT NULL,
                    positions_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_port ON paper_portfolio_snapshots(portfolio_id, created_at)")
            conn.commit()

    def get_or_create_portfolio(
        self,
        portfolio_id: str = "DEFAULT",
        initial_cash: float = 1000000.0,
        name: str = "Primary Paper Portfolio",
        user_id: str = "USR_SYSTEM",
    ) -> PaperPortfolioState:
        """Retrieves an existing portfolio from SQLite or creates a new one with initial virtual cash and user ownership."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT portfolio_id FROM paper_portfolios WHERE portfolio_id = ?", (portfolio_id,))
            row = cursor.fetchone()
            if not row:
                default_limits = RiskLimits()
                cursor.execute(
                    """
                    INSERT INTO paper_portfolios (
                        portfolio_id, user_id, name, initial_cash, current_cash, peak_equity, kill_switch_active,
                        risk_limits_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        portfolio_id,
                        user_id or "USR_SYSTEM",
                        name,
                        initial_cash,
                        initial_cash,
                        initial_cash,
                        0,
                        json.dumps(default_limits.model_dump()),
                        now_iso,
                        now_iso,
                    ),
                )
                conn.commit()
                self._record_audit_event(
                    conn,
                    portfolio_id=portfolio_id,
                    event_type=PaperEventType.PORTFOLIO_CREATED,
                    payload={"initial_cash": initial_cash, "name": name, "user_id": user_id or "USR_SYSTEM"},
                )
        return self.get_portfolio_state(portfolio_id)

    def get_portfolio_state(self, portfolio_id: str = "DEFAULT") -> PaperPortfolioState:
        """Constructs an accurate mark-to-market snapshot of the paper portfolio."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT portfolio_id, name, initial_cash, current_cash, peak_equity, kill_switch_active,
                       risk_limits_json, created_at, updated_at, user_id
                FROM paper_portfolios WHERE portfolio_id = ?
                """,
                (portfolio_id,),
            )
            port_row = cursor.fetchone()
            if not port_row:
                return self.get_or_create_portfolio(portfolio_id)

            p_id, name, init_cash, curr_cash, stored_peak_eq, kill_switch, limits_json, created_at, updated_at, owner_user_id = port_row
            risk_limits = RiskLimits(**json.loads(limits_json))
            risk_limits.kill_switch_active = bool(kill_switch)

            # Positions
            cursor.execute(
                """
                SELECT symbol, quantity, average_cost, current_price, realized_pnl, updated_at
                FROM paper_positions WHERE portfolio_id = ? AND quantity > 0
                """,
                (portfolio_id,),
            )
            pos_rows = cursor.fetchall()

            positions: Dict[str, PaperPositionRecord] = {}
            total_positions_val = 0.0
            total_realized_pnl = 0.0
            total_unrealized_pnl = 0.0

            for sym, qty, avg_cost, stored_price, r_pnl, pos_upd in pos_rows:
                # Refresh market price
                live_price, _, _, _ = self._resolve_market_price(sym)
                current_price = live_price if live_price and live_price > 0 else stored_price
                market_val = round(qty * current_price, 2)
                unrealized = round((current_price - avg_cost) * qty, 2) if avg_cost > 0 else 0.0
                unrealized_pct = round(((current_price - avg_cost) / avg_cost) * 100.0, 2) if avg_cost > 0 else 0.0

                total_positions_val += market_val
                total_realized_pnl += r_pnl
                total_unrealized_pnl += unrealized

                positions[sym] = PaperPositionRecord(
                    symbol=sym,
                    quantity=qty,
                    average_cost=avg_cost,
                    current_price=current_price,
                    market_value=market_val,
                    unrealized_pnl=unrealized,
                    unrealized_pnl_pct=unrealized_pct,
                    realized_pnl=r_pnl,
                    portfolio_weight_pct=0.0,  # Computed below
                    last_updated_at=pos_upd,
                )

            total_equity = round(curr_cash + total_positions_val, 2)
            peak_equity = max(stored_peak_eq or 0.0, total_equity)
            if peak_equity > (stored_peak_eq or 0.0):
                cursor.execute(
                    "UPDATE paper_portfolios SET peak_equity = ? WHERE portfolio_id = ?",
                    (peak_equity, portfolio_id),
                )
                conn.commit()

            current_drawdown_pct = (
                round(((peak_equity - total_equity) / peak_equity) * 100.0, 2)
                if peak_equity > 0
                else 0.0
            )

            # Weight calculations
            if total_equity > 0:
                for sym, pos_rec in positions.items():
                    pos_rec.portfolio_weight_pct = round((pos_rec.market_value / total_equity) * 100.0, 2)

            # Order counts
            cursor.execute("SELECT count(*) FROM paper_orders WHERE portfolio_id = ?", (portfolio_id,))
            total_orders = cursor.fetchone()[0]

            cursor.execute(
                "SELECT count(*) FROM paper_orders WHERE portfolio_id = ? AND status IN (?, ?)",
                (portfolio_id, PaperOrderStatus.PENDING.value, PaperOrderStatus.SUBMITTED.value),
            )
            open_orders = cursor.fetchone()[0]

            # Transaction costs paid
            cursor.execute(
                "SELECT sum(transaction_costs) FROM paper_orders WHERE portfolio_id = ? AND status = ?",
                (portfolio_id, PaperOrderStatus.FILLED.value),
            )
            costs_sum = cursor.fetchone()[0] or 0.0

            return PaperPortfolioState(
                portfolio_id=p_id,
                user_id=owner_user_id or "USR_SYSTEM",
                name=name,
                initial_cash=round(init_cash, 2),
                current_cash=round(curr_cash, 2),
                positions_value=round(total_positions_val, 2),
                total_equity=total_equity,
                peak_equity=round(peak_equity, 2),
                current_drawdown_pct=current_drawdown_pct,
                total_realized_pnl=round(total_realized_pnl, 2),
                total_unrealized_pnl=round(total_unrealized_pnl, 2),
                total_transaction_costs_paid=round(costs_sum, 2),
                kill_switch_active=bool(kill_switch),
                risk_limits=risk_limits,
                positions=positions,
                open_orders_count=open_orders,
                total_orders_count=total_orders,
                created_at=created_at,
                updated_at=updated_at,
            )

    def submit_order(self, req: PaperOrderRequest) -> PaperOrderRecord:
        """Processes a simulated order with duplicate protection, risk vetoes, and statutory cost deduction."""
        now_iso = datetime.now(timezone.utc).isoformat()
        clean_sym = req.symbol.strip().upper()

        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            conn.isolation_level = "EXCLUSIVE"
            cursor = conn.cursor()

            # -------------------------------------------------------------
            # 1. IDEMPOTENCY / DUPLICATE-EVENT CHECK
            # -------------------------------------------------------------
            if req.idempotency_key:
                cursor.execute("SELECT order_id FROM paper_orders WHERE idempotency_key = ?", (req.idempotency_key,))
                existing_row = cursor.fetchone()
                if existing_row:
                    return self._get_order_by_id(conn, existing_row[0])

            order_id = f"ORD-PAP-{uuid.uuid4().hex[:10].upper()}"

            # -------------------------------------------------------------
            # 2. CHECK KILL SWITCH VETO
            # -------------------------------------------------------------
            cursor.execute(
                "SELECT kill_switch_active, current_cash, risk_limits_json FROM paper_portfolios WHERE portfolio_id = ?",
                (req.portfolio_id,),
            )
            port_row = cursor.fetchone()
            if not port_row:
                self.get_or_create_portfolio(req.portfolio_id)
                cursor.execute(
                    "SELECT kill_switch_active, current_cash, risk_limits_json FROM paper_portfolios WHERE portfolio_id = ?",
                    (req.portfolio_id,),
                )
                port_row = cursor.fetchone()

            kill_switch, current_cash, limits_json = port_row
            risk_limits = RiskLimits(**json.loads(limits_json))

            if kill_switch or risk_limits.kill_switch_active:
                return self._create_and_persist_rejected_order(
                    conn=conn,
                    order_id=order_id,
                    req=req,
                    reason="KILL_SWITCH_ENGAGED: Paper trading kill switch is active. All simulated orders are blocked.",
                    now_iso=now_iso,
                )

            # -------------------------------------------------------------
            # 3. RESOLVE MARKET PRICE & STRICT DATA PROVENANCE
            # -------------------------------------------------------------
            market_price, classification, freshness, provenance_src = self._resolve_market_price(clean_sym)
            if market_price is None or market_price <= 0:
                return self._create_and_persist_rejected_order(
                    conn=conn,
                    order_id=order_id,
                    req=req,
                    reason=f"DATA_UNAVAILABLE: Validated market quote for '{clean_sym}' is unavailable. Simulated execution blocked without fabricated prices.",
                    now_iso=now_iso,
                    provenance=provenance_src,
                    classification=classification,
                    freshness=freshness,
                )

            # Stale market data check
            if risk_limits.reject_stale_prices and freshness == FreshnessStatus.STALE_WARNING:
                return self._create_and_persist_rejected_order(
                    conn=conn,
                    order_id=order_id,
                    req=req,
                    reason=f"STALE_MARKET_DATA: Market quote for '{clean_sym}' has freshness '{freshness.value}'. Execution blocked to protect against stale pricing.",
                    now_iso=now_iso,
                    provenance=provenance_src,
                    classification=classification,
                    freshness=freshness,
                )

            # -------------------------------------------------------------
            # 4. INDEPENDENT RISK LIMIT CHECKS
            # -------------------------------------------------------------
            estimated_turnover = round(market_price * req.quantity, 2)
            if estimated_turnover > risk_limits.max_order_value_inr:
                return self._create_and_persist_rejected_order(
                    conn=conn,
                    order_id=order_id,
                    req=req,
                    reason=f"RISK_LIMIT_EXCEEDED: Order turnover ₹{estimated_turnover:,.2f} exceeds max order value limit of ₹{risk_limits.max_order_value_inr:,.2f}.",
                    now_iso=now_iso,
                    provenance=provenance_src,
                    classification=classification,
                    freshness=freshness,
                )

            # Daily stop-loss check (realized loss + optional unrealized loss)
            today_str = now_iso[:10]
            cursor.execute(
                """
                SELECT coalesce(sum(realized_pnl), 0.0)
                FROM paper_orders
                WHERE portfolio_id = ? AND status = 'FILLED' AND filled_at LIKE ? AND side = 'SELL'
                """,
                (req.portfolio_id, f"{today_str}%"),
            )
            today_net_realized_pnl = cursor.fetchone()[0] or 0.0
            today_realized_loss = abs(today_net_realized_pnl) if today_net_realized_pnl < 0 else 0.0

            today_unrealized_loss = 0.0
            if risk_limits.include_unrealized_in_daily_loss:
                cursor.execute(
                    """
                    SELECT quantity, average_cost, current_price
                    FROM paper_positions
                    WHERE portfolio_id = ? AND quantity > 0
                    """,
                    (req.portfolio_id,),
                )
                for pos_q, pos_ac, pos_cp in cursor.fetchall():
                    pos_pnl = (pos_cp - pos_ac) * pos_q
                    if pos_pnl < 0:
                        today_unrealized_loss += abs(pos_pnl)

            total_daily_loss = today_realized_loss + today_unrealized_loss
            if total_daily_loss > risk_limits.max_daily_loss_inr:
                return self._create_and_persist_rejected_order(
                    conn=conn,
                    order_id=order_id,
                    req=req,
                    reason=(
                        f"DAILY_STOP_LOSS_EXCEEDED: Cumulative daily loss ₹{total_daily_loss:,.2f} "
                        f"(realized=₹{today_realized_loss:,.2f}, unrealized=₹{today_unrealized_loss:,.2f}) "
                        f"exceeds daily stop-loss limit of ₹{risk_limits.max_daily_loss_inr:,.2f}."
                    ),
                    now_iso=now_iso,
                    provenance=provenance_src,
                    classification=classification,
                    freshness=freshness,
                )

            # Max drawdown check from peak portfolio equity
            cursor.execute(
                "SELECT peak_equity FROM paper_portfolios WHERE portfolio_id = ?",
                (req.portfolio_id,),
            )
            peak_eq_row = cursor.fetchone()
            peak_eq = peak_eq_row[0] if (peak_eq_row and peak_eq_row[0]) else current_cash

            cursor.execute(
                "SELECT sum(quantity * current_price) FROM paper_positions WHERE portfolio_id = ? AND quantity > 0",
                (req.portfolio_id,),
            )
            total_pos_val = cursor.fetchone()[0] or 0.0
            curr_equity = current_cash + total_pos_val
            if curr_equity > peak_eq:
                peak_eq = curr_equity
                cursor.execute(
                    "UPDATE paper_portfolios SET peak_equity = ? WHERE portfolio_id = ?",
                    (peak_eq, req.portfolio_id),
                )

            current_dd_pct = ((peak_eq - curr_equity) / peak_eq * 100.0) if peak_eq > 0 else 0.0
            if current_dd_pct > risk_limits.max_drawdown_pct and req.side == PaperOrderSide.BUY:
                return self._create_and_persist_rejected_order(
                    conn=conn,
                    order_id=order_id,
                    req=req,
                    reason=(
                        f"MAX_DRAWDOWN_EXCEEDED: Current portfolio drawdown {current_dd_pct:.1f}% "
                        f"exceeds maximum allowed drawdown threshold of {risk_limits.max_drawdown_pct:.1f}%. "
                        f"New buy orders are restricted."
                    ),
                    now_iso=now_iso,
                    provenance=provenance_src,
                    classification=classification,
                    freshness=freshness,
                )

            # -------------------------------------------------------------
            # 5. ORDER TYPE LIMIT THRESHOLD EVALUATION
            # -------------------------------------------------------------
            if req.order_type == PaperOrderType.LIMIT and req.limit_price is not None:
                if req.side == PaperOrderSide.BUY and market_price > req.limit_price:
                    # Limit price not met: order placed into SUBMITTED (pending fill)
                    return self._create_and_persist_submitted_order(
                        conn=conn,
                        order_id=order_id,
                        req=req,
                        market_price=market_price,
                        now_iso=now_iso,
                        provenance=provenance_src,
                        classification=classification,
                        freshness=freshness,
                        note=f"BUY limit condition not met: Market price (₹{market_price:.2f}) > Limit price (₹{req.limit_price:.2f})",
                    )
                elif req.side == PaperOrderSide.SELL and market_price < req.limit_price:
                    # Limit price not met: order placed into SUBMITTED
                    return self._create_and_persist_submitted_order(
                        conn=conn,
                        order_id=order_id,
                        req=req,
                        market_price=market_price,
                        now_iso=now_iso,
                        provenance=provenance_src,
                        classification=classification,
                        freshness=freshness,
                        note=f"SELL limit condition not met: Market price (₹{market_price:.2f}) < Limit price (₹{req.limit_price:.2f})",
                    )

            # -------------------------------------------------------------
            # 6. STATUTORY COST CALCULATION & CASH/SHARE SUFFICIENCY
            # -------------------------------------------------------------
            trade_action = TradeAction.BUY if req.side == PaperOrderSide.BUY else TradeAction.SELL
            cost_breakdown = self.cost_model.calculate_trade_costs(
                action=trade_action,
                raw_price=market_price,
                quantity=req.quantity,
                instrument_type=req.instrument_type,
            )

            if req.side == PaperOrderSide.BUY:
                required_capital = cost_breakdown.turnover_gross + cost_breakdown.total_costs
                if current_cash < required_capital:
                    return self._create_and_persist_rejected_order(
                        conn=conn,
                        order_id=order_id,
                        req=req,
                        reason=f"INSUFFICIENT_CASH: Required virtual cash ₹{required_capital:,.2f} exceeds available balance ₹{current_cash:,.2f}.",
                        now_iso=now_iso,
                        provenance=provenance_src,
                        classification=classification,
                        freshness=freshness,
                    )

                # Max position weight check on BUY
                cursor.execute(
                    "SELECT quantity, average_cost FROM paper_positions WHERE portfolio_id = ? AND symbol = ?",
                    (req.portfolio_id, clean_sym),
                )
                existing_pos = cursor.fetchone()
                existing_val = (existing_pos[0] * market_price) if existing_pos else 0.0
                post_buy_val = existing_val + cost_breakdown.turnover_gross
                total_portfolio_equity = current_cash + existing_val
                if total_portfolio_equity > 0:
                    projected_weight = (post_buy_val / total_portfolio_equity) * 100.0
                    if projected_weight > risk_limits.max_position_weight_pct:
                        return self._create_and_persist_rejected_order(
                            conn=conn,
                            order_id=order_id,
                            req=req,
                            reason=f"RISK_LIMIT_EXCEEDED: Post-trade position weight {projected_weight:.1f}% exceeds max limit of {risk_limits.max_position_weight_pct:.1f}%.",
                            now_iso=now_iso,
                            provenance=provenance_src,
                            classification=classification,
                            freshness=freshness,
                        )

            elif req.side == PaperOrderSide.SELL:
                cursor.execute(
                    "SELECT quantity FROM paper_positions WHERE portfolio_id = ? AND symbol = ?",
                    (req.portfolio_id, clean_sym),
                )
                existing_pos = cursor.fetchone()
                held_qty = existing_pos[0] if existing_pos else 0
                if held_qty < req.quantity:
                    return self._create_and_persist_rejected_order(
                        conn=conn,
                        order_id=order_id,
                        req=req,
                        reason=f"INSUFFICIENT_SHARES: Attempted to sell {req.quantity} shares, but only {held_qty} shares are held.",
                        now_iso=now_iso,
                        provenance=provenance_src,
                        classification=classification,
                        freshness=freshness,
                    )

            # -------------------------------------------------------------
            # 7. EXECUTE SIMULATED FILL & UPDATE LEDGER
            # -------------------------------------------------------------
            exec_price = cost_breakdown.execution_price_with_slippage
            turnover = cost_breakdown.turnover_gross
            total_costs = cost_breakdown.total_costs

            if req.side == PaperOrderSide.BUY:
                # Deduct exact cash
                new_cash = round(current_cash - (turnover + total_costs), 2)
                cursor.execute(
                    "UPDATE paper_portfolios SET current_cash = ?, updated_at = ? WHERE portfolio_id = ?",
                    (new_cash, now_iso, req.portfolio_id),
                )

                # Update Position
                cursor.execute(
                    "SELECT quantity, average_cost FROM paper_positions WHERE portfolio_id = ? AND symbol = ?",
                    (req.portfolio_id, clean_sym),
                )
                p_row = cursor.fetchone()
                if p_row:
                    old_qty, old_avg = p_row
                    new_qty = old_qty + req.quantity
                    new_avg = round(((old_qty * old_avg) + turnover) / new_qty, 4)
                    cursor.execute(
                        """
                        UPDATE paper_positions
                        SET quantity = ?, average_cost = ?, current_price = ?, updated_at = ?
                        WHERE portfolio_id = ? AND symbol = ?
                        """,
                        (new_qty, new_avg, market_price, now_iso, req.portfolio_id, clean_sym),
                    )
                else:
                    new_avg = round(turnover / req.quantity, 4)
                    cursor.execute(
                        """
                        INSERT INTO paper_positions (
                            portfolio_id, symbol, quantity, average_cost, current_price, realized_pnl, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0.0, ?)
                        """,
                        (req.portfolio_id, clean_sym, req.quantity, new_avg, market_price, now_iso),
                    )

                # Record FIFO open lot
                cursor.execute(
                    """
                    INSERT INTO paper_lots (
                        portfolio_id, symbol, buy_order_id, quantity, remaining_quantity,
                        buy_price, buy_costs, buy_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (req.portfolio_id, clean_sym, order_id, req.quantity, req.quantity, exec_price, total_costs, now_iso),
                )

            elif req.side == PaperOrderSide.SELL:
                # Add net cash proceeds
                net_proceeds = round(turnover - total_costs, 2)
                new_cash = round(current_cash + net_proceeds, 2)
                cursor.execute(
                    "UPDATE paper_portfolios SET current_cash = ?, updated_at = ? WHERE portfolio_id = ?",
                    (new_cash, now_iso, req.portfolio_id),
                )

                # FIFO lot matching for realized P&L
                cursor.execute(
                    """
                    SELECT lot_id, remaining_quantity, buy_price FROM paper_lots
                    WHERE portfolio_id = ? AND symbol = ? AND remaining_quantity > 0
                    ORDER BY lot_id ASC
                    """,
                    (req.portfolio_id, clean_sym),
                )
                lots = cursor.fetchall()
                qty_to_fill = req.quantity
                cost_basis_matched = 0.0

                for lot_id, rem_qty, b_price in lots:
                    match_qty = min(qty_to_fill, rem_qty)
                    cost_basis_matched += match_qty * b_price
                    rem_after = rem_qty - match_qty
                    cursor.execute("UPDATE paper_lots SET remaining_quantity = ? WHERE lot_id = ?", (rem_after, lot_id))
                    qty_to_fill -= match_qty
                    if qty_to_fill <= 0:
                        break

                trade_realized_pnl = round(net_proceeds - cost_basis_matched, 2)

                cursor.execute(
                    "SELECT quantity, average_cost, realized_pnl FROM paper_positions WHERE portfolio_id = ? AND symbol = ?",
                    (req.portfolio_id, clean_sym),
                )
                old_qty, old_avg, old_r_pnl = cursor.fetchone()
                new_qty = old_qty - req.quantity
                new_r_pnl = round(old_r_pnl + trade_realized_pnl, 2)
                new_avg = old_avg if new_qty > 0 else 0.0

                cursor.execute(
                    """
                    UPDATE paper_positions
                    SET quantity = ?, average_cost = ?, current_price = ?, realized_pnl = ?, updated_at = ?
                    WHERE portfolio_id = ? AND symbol = ?
                    """,
                    (new_qty, new_avg, market_price, new_r_pnl, now_iso, req.portfolio_id, clean_sym),
                )

            # Save Filled Order
            cost_dict = {
                "brokerage": cost_breakdown.brokerage,
                "stt": cost_breakdown.stt,
                "exchange_txn_charge": cost_breakdown.exchange_txn_charge,
                "sebi_turnover_fee": cost_breakdown.sebi_turnover_fee,
                "stamp_duty": cost_breakdown.stamp_duty,
                "gst": cost_breakdown.gst,
                "slippage_bps": cost_breakdown.slippage_bps,
            }
            order_realized_pnl = trade_realized_pnl if req.side == PaperOrderSide.SELL else 0.0

            cursor.execute(
                """
                INSERT INTO paper_orders (
                    order_id, idempotency_key, portfolio_id, symbol, side, order_type, quantity,
                    limit_price, status, submitted_at, filled_at, fill_price, executed_quantity,
                    turnover, transaction_costs, realized_pnl, cost_breakdown_json, rejection_reason,
                    data_provenance, data_classification, freshness_status, is_demonstration, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    req.idempotency_key,
                    req.portfolio_id,
                    clean_sym,
                    req.side.value,
                    req.order_type.value,
                    req.quantity,
                    req.limit_price,
                    PaperOrderStatus.FILLED.value,
                    now_iso,
                    now_iso,
                    exec_price,
                    req.quantity,
                    turnover,
                    total_costs,
                    order_realized_pnl,
                    json.dumps(cost_dict),
                    None,
                    provenance_src,
                    classification.value,
                    freshness.value,
                    1 if classification == DataClassification.SYNTHETIC_BENCHMARK else 0,
                    f"Statutory friction: ₹{total_costs:,.2f} | Execution: ₹{exec_price:.2f}",
                ),
            )

            conn.commit()

            # Record event in audit log
            self._record_audit_event(
                conn=conn,
                portfolio_id=req.portfolio_id,
                event_type=PaperEventType.ORDER_FILLED,
                idempotency_key=req.idempotency_key,
                payload={
                    "order_id": order_id,
                    "symbol": clean_sym,
                    "side": req.side.value,
                    "quantity": req.quantity,
                    "fill_price": exec_price,
                    "turnover": turnover,
                    "transaction_costs": total_costs,
                },
            )

            return PaperOrderRecord(
                order_id=order_id,
                idempotency_key=req.idempotency_key,
                portfolio_id=req.portfolio_id,
                symbol=clean_sym,
                side=req.side,
                order_type=req.order_type,
                quantity=req.quantity,
                limit_price=req.limit_price,
                status=PaperOrderStatus.FILLED,
                submitted_at=now_iso,
                filled_at=now_iso,
                fill_price=exec_price,
                executed_quantity=req.quantity,
                turnover=turnover,
                transaction_costs=total_costs,
                cost_breakdown=cost_dict,
                rejection_reason=None,
                data_provenance=provenance_src,
                data_classification=classification,
                freshness_status=freshness,
                is_demonstration=classification == DataClassification.SYNTHETIC_BENCHMARK,
                notes=f"Statutory friction: ₹{total_costs:,.2f} | Execution: ₹{exec_price:.2f}",
            )

    def cancel_order(self, req: CancelOrderRequest) -> PaperOrderRecord:
        """Cancels an open or submitted order if it has not yet been filled."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status, symbol, side, quantity FROM paper_orders WHERE order_id = ? AND portfolio_id = ?",
                (req.order_id, req.portfolio_id),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Order '{req.order_id}' not found in portfolio '{req.portfolio_id}'")

            current_status, sym, side, qty = row
            if current_status not in [PaperOrderStatus.PENDING.value, PaperOrderStatus.SUBMITTED.value]:
                raise ValueError(f"Cannot cancel order in status '{current_status}'")

            cursor.execute(
                "UPDATE paper_orders SET status = ?, rejection_reason = ? WHERE order_id = ?",
                (PaperOrderStatus.CANCELLED.value, "Cancelled by user request", req.order_id),
            )
            conn.commit()

            self._record_audit_event(
                conn=conn,
                portfolio_id=req.portfolio_id,
                event_type=PaperEventType.ORDER_CANCELLED,
                payload={"order_id": req.order_id, "symbol": sym, "side": side, "quantity": qty},
            )

            return self._get_order_by_id(conn, req.order_id)

    def toggle_kill_switch(self, req: KillSwitchRequest) -> PaperPortfolioState:
        """Engages or disengages the emergency risk kill switch."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT risk_limits_json FROM paper_portfolios WHERE portfolio_id = ?",
                (req.portfolio_id,),
            )
            row = cursor.fetchone()
            if not row:
                self.get_or_create_portfolio(req.portfolio_id)
                cursor.execute(
                    "SELECT risk_limits_json FROM paper_portfolios WHERE portfolio_id = ?",
                    (req.portfolio_id,),
                )
                row = cursor.fetchone()

            limits = RiskLimits(**json.loads(row[0]))
            limits.kill_switch_active = req.active

            cursor.execute(
                """
                UPDATE paper_portfolios
                SET kill_switch_active = ?, risk_limits_json = ?, updated_at = ?
                WHERE portfolio_id = ?
                """,
                (1 if req.active else 0, json.dumps(limits.model_dump()), now_iso, req.portfolio_id),
            )
            conn.commit()

            self._record_audit_event(
                conn=conn,
                portfolio_id=req.portfolio_id,
                event_type=PaperEventType.KILL_SWITCH_TOGGLED,
                payload={"active": req.active, "reason": req.reason},
            )

        return self.get_portfolio_state(req.portfolio_id)

    def apply_corporate_action(self, req: PaperCorporateActionRequest) -> Dict[str, Any]:
        """Applies a statutory corporate action (cash dividend, stock split, bonus) to virtual holdings."""
        now_iso = datetime.now(timezone.utc).isoformat()
        clean_sym = req.symbol.strip().upper()

        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT quantity, average_cost FROM paper_positions WHERE portfolio_id = ? AND symbol = ?",
                (req.portfolio_id, clean_sym),
            )
            row = cursor.fetchone()
            if not row or row[0] <= 0:
                return {"status": "NO_POSITION", "message": f"No open position held in '{clean_sym}'"}

            qty, avg_cost = row

            if req.action_type == "CASH_DIVIDEND":
                if not req.dividend_amount_inr or req.dividend_amount_inr <= 0:
                    raise ValueError("Dividend amount must be positive")
                dividend_cash = round(qty * req.dividend_amount_inr, 2)
                cursor.execute(
                    "UPDATE paper_portfolios SET current_cash = current_cash + ?, updated_at = ? WHERE portfolio_id = ?",
                    (dividend_cash, now_iso, req.portfolio_id),
                )
                conn.commit()
                self._record_audit_event(
                    conn=conn,
                    portfolio_id=req.portfolio_id,
                    event_type=PaperEventType.CORPORATE_ACTION_APPLIED,
                    payload={"symbol": clean_sym, "type": "DIVIDEND", "credited": dividend_cash},
                )
                return {"status": "SUCCESS", "type": "DIVIDEND", "credited_inr": dividend_cash, "shares": qty}

            elif req.action_type in ["STOCK_SPLIT", "BONUS_ISSUE"]:
                ratio = req.split_ratio or 2.0
                if ratio <= 0:
                    raise ValueError("Split/bonus ratio must be positive")
                new_qty = int(qty * ratio)
                new_avg = round(avg_cost / ratio, 4)
                cursor.execute(
                    """
                    UPDATE paper_positions
                    SET quantity = ?, average_cost = ?, updated_at = ?
                    WHERE portfolio_id = ? AND symbol = ?
                    """,
                    (new_qty, new_avg, now_iso, req.portfolio_id, clean_sym),
                )
                # Adjust open lots
                cursor.execute(
                    "SELECT lot_id, remaining_quantity, buy_price FROM paper_lots WHERE portfolio_id = ? AND symbol = ?",
                    (req.portfolio_id, clean_sym),
                )
                for lot_id, rem, bp in cursor.fetchall():
                    cursor.execute(
                        "UPDATE paper_lots SET remaining_quantity = ?, buy_price = ? WHERE lot_id = ?",
                        (int(rem * ratio), round(bp / ratio, 4), lot_id),
                    )
                conn.commit()
                self._record_audit_event(
                    conn=conn,
                    portfolio_id=req.portfolio_id,
                    event_type=PaperEventType.CORPORATE_ACTION_APPLIED,
                    payload={"symbol": clean_sym, "type": req.action_type, "old_qty": qty, "new_qty": new_qty},
                )
                return {"status": "SUCCESS", "type": req.action_type, "old_shares": qty, "new_shares": new_qty, "ratio": ratio}

            else:
                raise ValueError(f"Unsupported corporate action type '{req.action_type}'")

    def reset_portfolio(self, portfolio_id: str = "DEFAULT", initial_cash: float = 1000000.0) -> PaperPortfolioState:
        """Wipes virtual positions and orders for testing/demo resets."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM paper_positions WHERE portfolio_id = ?", (portfolio_id,))
            cursor.execute("DELETE FROM paper_orders WHERE portfolio_id = ?", (portfolio_id,))
            cursor.execute("DELETE FROM paper_lots WHERE portfolio_id = ?", (portfolio_id,))
            cursor.execute(
                """
                UPDATE paper_portfolios
                SET current_cash = ?, initial_cash = ?, kill_switch_active = 0, updated_at = ?
                WHERE portfolio_id = ?
                """,
                (initial_cash, initial_cash, now_iso, portfolio_id),
            )
            conn.commit()
            self._record_audit_event(
                conn=conn,
                portfolio_id=portfolio_id,
                event_type=PaperEventType.PORTFOLIO_RESET,
                payload={"initial_cash": initial_cash},
            )
        return self.get_portfolio_state(portfolio_id)

    def list_orders(self, portfolio_id: str = "DEFAULT", limit: int = 50) -> List[PaperOrderRecord]:
        """Lists recent paper orders."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT order_id FROM paper_orders
                WHERE portfolio_id = ? ORDER BY submitted_at DESC LIMIT ?
                """,
                (portfolio_id, limit),
            )
            order_ids = [r[0] for r in cursor.fetchall()]
            return [self._get_order_by_id(conn, o_id) for o_id in order_ids]

    def list_portfolios(self, user_id: Optional[str] = None, is_admin: bool = False) -> List[Dict[str, Any]]:
        """Returns configured paper portfolios, filtered by user_id unless is_admin is True."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            if user_id and not is_admin and user_id != "USR_SYSTEM":
                cursor.execute(
                    """
                    SELECT portfolio_id, name, initial_cash, current_cash, peak_equity,
                           kill_switch_active, created_at, updated_at, user_id
                    FROM paper_portfolios WHERE user_id = ? ORDER BY created_at ASC
                    """,
                    (user_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT portfolio_id, name, initial_cash, current_cash, peak_equity,
                           kill_switch_active, created_at, updated_at, user_id
                    FROM paper_portfolios ORDER BY created_at ASC
                    """
                )
            rows = cursor.fetchall()
            result = []
            for r in rows:
                p_id, name, init_cash, curr_cash, peak_eq, kill_sw, cr_at, up_at, p_owner = r
                state = self.get_portfolio_state(p_id)
                result.append({
                    "portfolio_id": p_id,
                    "user_id": p_owner or "USR_SYSTEM",
                    "name": name,
                    "initial_cash": init_cash,
                    "current_cash": curr_cash,
                    "total_equity": state.total_equity,
                    "positions_value": state.positions_value,
                    "positions_count": len(state.positions),
                    "peak_equity": state.peak_equity,
                    "current_drawdown_pct": state.current_drawdown_pct,
                    "kill_switch_active": bool(kill_sw),
                    "created_at": cr_at,
                    "updated_at": up_at,
                })
            return result

    def verify_portfolio_access(
        self,
        portfolio_id: str,
        user_id: str,
        is_admin: bool = False,
    ) -> bool:
        """Verifies if the given user owns the portfolio or has administrative privileges.
        Returns True if access is permitted, False otherwise."""
        if is_admin or user_id == "USR_SYSTEM":
            return True
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM paper_portfolios WHERE portfolio_id = ?", (portfolio_id,))
            row = cursor.fetchone()
            if not row:
                return True
            owner = row[0] or "USR_SYSTEM"
            if owner == "USR_SYSTEM":
                return True
            return owner == user_id

    def get_portfolio_owner(self, portfolio_id: str) -> Optional[str]:
        """Returns the user_id that owns the portfolio, or None if not found."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM paper_portfolios WHERE portfolio_id = ?", (portfolio_id,))
            row = cursor.fetchone()
            return (row[0] or "USR_SYSTEM") if row else None

    def record_portfolio_snapshot(self, portfolio_id: str = "DEFAULT") -> Dict[str, Any]:
        """Durably persists a mark-to-market snapshot of the portfolio."""
        state = self.get_portfolio_state(portfolio_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        positions_summary = {
            sym: {
                "quantity": pos.quantity,
                "average_cost": pos.average_cost,
                "current_price": pos.current_price,
                "market_value": pos.market_value,
                "unrealized_pnl": pos.unrealized_pnl,
            }
            for sym, pos in state.positions.items()
        }
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO paper_portfolio_snapshots
                (portfolio_id, total_equity, current_cash, positions_value,
                 total_unrealized_pnl, total_realized_pnl, positions_count,
                 positions_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    portfolio_id,
                    state.total_equity,
                    state.current_cash,
                    state.positions_value,
                    state.total_unrealized_pnl,
                    state.total_realized_pnl,
                    len(state.positions),
                    json.dumps(positions_summary),
                    now_iso,
                ),
            )
            conn.commit()
            snap_id = cursor.lastrowid
        return {
            "snapshot_id": snap_id,
            "portfolio_id": portfolio_id,
            "total_equity": state.total_equity,
            "current_cash": state.current_cash,
            "positions_value": state.positions_value,
            "positions_count": len(state.positions),
            "created_at": now_iso,
        }

    def get_portfolio_snapshots(self, portfolio_id: str = "DEFAULT", limit: int = 30) -> List[Dict[str, Any]]:
        """Returns chronological history of persisted portfolio snapshots."""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT snapshot_id, portfolio_id, total_equity, current_cash,
                       positions_value, total_unrealized_pnl, total_realized_pnl,
                       positions_count, positions_json, created_at
                FROM paper_portfolio_snapshots
                WHERE portfolio_id = ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (portfolio_id, limit),
            )
            rows = cursor.fetchall()
            return [
                {
                    "snapshot_id": r[0],
                    "portfolio_id": r[1],
                    "total_equity": r[2],
                    "current_cash": r[3],
                    "positions_value": r[4],
                    "total_unrealized_pnl": r[5],
                    "total_realized_pnl": r[6],
                    "positions_count": r[7],
                    "positions": json.loads(r[8]),
                    "created_at": r[9],
                }
                for r in reversed(rows)
            ]

    # ------------------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------------------

    def _resolve_market_price(
        self, symbol: str
    ) -> Tuple[Optional[float], DataClassification, FreshnessStatus, str]:
        """Resolves current market price strictly through validated connectors or fixtures.
        Never fabricates prices or falls back silently to unrelated instruments.
        """
        clean = symbol.strip().upper()

        # 1. Benchmark Fixtures
        if clean in ["RELIANCE", "RIL", "RELIANCE.NS"]:
            latest_bar = RELIANCE_SERIES[-1]
            return (
                latest_bar.close,
                DataClassification.SYNTHETIC_BENCHMARK,
                FreshnessStatus.OFFLINE_FROZEN,
                "RELIANCE_BENCHMARK_FIXTURE",
            )
        elif clean in ["TCS", "TCS.NS"]:
            latest_bar = TCS_BONUS_SERIES[-1]
            return (
                latest_bar.close,
                DataClassification.SYNTHETIC_BENCHMARK,
                FreshnessStatus.OFFLINE_FROZEN,
                "TCS_BONUS_BENCHMARK_FIXTURE",
            )
        elif clean in ["NIFTY", "NIFTY50", "NIFTY_50", "NIFTY50_INDEX"]:
            latest_bar = NIFTY50_BENCHMARK_SERIES[-1]
            return (
                latest_bar.close,
                DataClassification.SYNTHETIC_BENCHMARK,
                FreshnessStatus.OFFLINE_FROZEN,
                "NIFTY50_INDEX_BENCHMARK_FIXTURE",
            )

        # 2. Existing NSE Connector
        try:
            quote = self.market_connector.get_quote(clean)
            if quote.current_price and quote.current_price > 0:
                if quote.classification in [
                    DataClassification.LIVE_VERIFIED,
                    DataClassification.DELAYED_VERIFIED,
                    DataClassification.CACHED,
                    DataClassification.HISTORICAL_VERIFIED,
                ]:
                    return (
                        quote.current_price,
                        quote.classification,
                        quote.freshness,
                        f"NSE_CONNECTOR:{quote.data_provider}",
                    )
        except Exception:
            pass

        # 3. Unavailable / Missing
        return (None, DataClassification.UNAVAILABLE, FreshnessStatus.UNKNOWN, "PRICE_FEED_UNAVAILABLE")

    def _create_and_persist_rejected_order(
        self,
        conn: sqlite3.Connection,
        order_id: str,
        req: PaperOrderRequest,
        reason: str,
        now_iso: str,
        provenance: str = "PRICE_FEED_UNAVAILABLE",
        classification: DataClassification = DataClassification.UNVERIFIED,
        freshness: FreshnessStatus = FreshnessStatus.UNKNOWN,
    ) -> PaperOrderRecord:
        """Stores a rejected order record and writes an audit event."""
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO paper_orders (
                order_id, idempotency_key, portfolio_id, symbol, side, order_type, quantity,
                limit_price, status, submitted_at, filled_at, fill_price, executed_quantity,
                turnover, transaction_costs, cost_breakdown_json, rejection_reason,
                data_provenance, data_classification, freshness_status, is_demonstration, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                req.idempotency_key,
                req.portfolio_id,
                req.symbol.upper(),
                req.side.value,
                req.order_type.value,
                req.quantity,
                req.limit_price,
                PaperOrderStatus.REJECTED.value,
                now_iso,
                None,
                None,
                0,
                0.0,
                0.0,
                None,
                reason,
                provenance,
                classification.value,
                freshness.value,
                1,
                reason,
            ),
        )
        conn.commit()

        self._record_audit_event(
            conn=conn,
            portfolio_id=req.portfolio_id,
            event_type=PaperEventType.ORDER_REJECTED,
            idempotency_key=req.idempotency_key,
            payload={"order_id": order_id, "symbol": req.symbol.upper(), "reason": reason},
        )

        return PaperOrderRecord(
            order_id=order_id,
            idempotency_key=req.idempotency_key,
            portfolio_id=req.portfolio_id,
            symbol=req.symbol.upper(),
            side=req.side,
            order_type=req.order_type,
            quantity=req.quantity,
            limit_price=req.limit_price,
            status=PaperOrderStatus.REJECTED,
            submitted_at=now_iso,
            rejection_reason=reason,
            data_provenance=provenance,
            data_classification=classification,
            freshness_status=freshness,
            is_demonstration=True,
            notes=reason,
        )

    def _create_and_persist_submitted_order(
        self,
        conn: sqlite3.Connection,
        order_id: str,
        req: PaperOrderRequest,
        market_price: float,
        now_iso: str,
        provenance: str,
        classification: DataClassification,
        freshness: FreshnessStatus,
        note: str,
    ) -> PaperOrderRecord:
        """Stores a limit order in SUBMITTED state awaiting condition fulfillment."""
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO paper_orders (
                order_id, idempotency_key, portfolio_id, symbol, side, order_type, quantity,
                limit_price, status, submitted_at, filled_at, fill_price, executed_quantity,
                turnover, transaction_costs, cost_breakdown_json, rejection_reason,
                data_provenance, data_classification, freshness_status, is_demonstration, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                req.idempotency_key,
                req.portfolio_id,
                req.symbol.upper(),
                req.side.value,
                req.order_type.value,
                req.quantity,
                req.limit_price,
                PaperOrderStatus.SUBMITTED.value,
                now_iso,
                None,
                None,
                0,
                0.0,
                0.0,
                None,
                None,
                provenance,
                classification.value,
                freshness.value,
                1 if classification == DataClassification.SYNTHETIC_BENCHMARK else 0,
                note,
            ),
        )
        conn.commit()

        self._record_audit_event(
            conn=conn,
            portfolio_id=req.portfolio_id,
            event_type=PaperEventType.ORDER_SUBMITTED,
            idempotency_key=req.idempotency_key,
            payload={"order_id": order_id, "symbol": req.symbol.upper(), "limit_price": req.limit_price},
        )

        return PaperOrderRecord(
            order_id=order_id,
            idempotency_key=req.idempotency_key,
            portfolio_id=req.portfolio_id,
            symbol=req.symbol.upper(),
            side=req.side,
            order_type=req.order_type,
            quantity=req.quantity,
            limit_price=req.limit_price,
            status=PaperOrderStatus.SUBMITTED,
            submitted_at=now_iso,
            data_provenance=provenance,
            data_classification=classification,
            freshness_status=freshness,
            is_demonstration=classification == DataClassification.SYNTHETIC_BENCHMARK,
            notes=note,
        )

    def _get_order_by_id(self, conn: sqlite3.Connection, order_id: str) -> PaperOrderRecord:
        """Reconstructs PaperOrderRecord from SQLite."""
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT order_id, idempotency_key, portfolio_id, symbol, side, order_type, quantity,
                   limit_price, status, submitted_at, filled_at, fill_price, executed_quantity,
                   turnover, transaction_costs, cost_breakdown_json, rejection_reason,
                   data_provenance, data_classification, freshness_status, is_demonstration, notes
            FROM paper_orders WHERE order_id = ?
            """,
            (order_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Order '{order_id}' not found")

        cost_dict = json.loads(row[15]) if row[15] else None

        return PaperOrderRecord(
            order_id=row[0],
            idempotency_key=row[1],
            portfolio_id=row[2],
            symbol=row[3],
            side=PaperOrderSide(row[4]),
            order_type=PaperOrderType(row[5]),
            quantity=row[6],
            limit_price=row[7],
            status=PaperOrderStatus(row[8]),
            submitted_at=row[9],
            filled_at=row[10],
            fill_price=row[11],
            executed_quantity=row[12],
            turnover=row[13],
            transaction_costs=row[14],
            cost_breakdown=cost_dict,
            rejection_reason=row[16],
            data_provenance=row[17],
            data_classification=DataClassification(row[18]),
            freshness_status=FreshnessStatus(row[19]),
            is_demonstration=bool(row[20]),
            notes=row[21] or "",
        )

    def _record_audit_event(
        self,
        conn: sqlite3.Connection,
        portfolio_id: str,
        event_type: PaperEventType,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None,
    ):
        """Logs audit event to paper_audit_events and chains into SHA-256 ledger."""
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO paper_audit_events (portfolio_id, event_type, idempotency_key, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (portfolio_id, event_type.value, idempotency_key, json.dumps(payload), now_iso),
        )
        conn.commit()

        # Link into cryptographic audit ledger
        try:
            audit_ledger.record_backtest_run(
                audit_id=f"AUD-PAP-{uuid.uuid4().hex[:8].upper()}",
                symbol=payload.get("symbol", "PORTFOLIO"),
                strategy_name=f"PaperManager:{event_type.value}",
                recommendation=event_type.value,
                current_price=payload.get("fill_price", 0.0) or 0.0,
                payload_dict=payload,
            )
        except Exception:
            pass


# Singleton instance
paper_manager = PaperPortfolioManager()
