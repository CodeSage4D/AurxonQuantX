"""AURXON Market Data & Historical Store.
Provides SQLite WAL-backed persistence for normalized market quotes, historical OHLCV bars,
financial statements, and corporate actions with strict observation timestamps, units, and provenance.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

from app.schemas.historical_data import (
    AdjustmentMethod,
    CorporateAction,
    CorporateActionType,
    Exchange,
    HistoricalBar,
)
from app.schemas.market import DataClassification, FreshnessStatus, MarketQuote

logger = logging.getLogger("aurxon.market_data_store")

DB_PATH = Path("data/aurxon_market_data.sqlite")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class MarketDataStore:
    """Persistent local store for verified quotes, OHLCV bars, and corporate financials."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS quotes (
                    symbol TEXT PRIMARY KEY,
                    clean_ticker TEXT NOT NULL,
                    instrument_name TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    current_price REAL,
                    market_timestamp TEXT,
                    retrieval_timestamp TEXT NOT NULL,
                    data_provider TEXT NOT NULL,
                    source_reference TEXT,
                    classification TEXT NOT NULL,
                    freshness TEXT NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'INR',
                    price_units TEXT NOT NULL DEFAULT 'INR per share',
                    pe_ratio REAL,
                    pb_ratio REAL,
                    eps REAL,
                    bvps REAL,
                    dividend_yield REAL,
                    market_cap_cr REAL,
                    debt_cr REAL,
                    cash_cr REAL,
                    raw_json TEXT
                );

                CREATE TABLE IF NOT EXISTS historical_bars (
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL DEFAULT 'NSE',
                    trading_date TEXT NOT NULL,
                    interval TEXT NOT NULL DEFAULT 'DAILY',
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER NOT NULL,
                    adjustment_method TEXT NOT NULL DEFAULT 'RAW_UNADJUSTED',
                    observation_timestamp TEXT NOT NULL,
                    retrieval_timestamp TEXT NOT NULL,
                    data_provider TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    freshness TEXT NOT NULL,
                    PRIMARY KEY (symbol, trading_date, interval)
                );

                CREATE TABLE IF NOT EXISTS corporate_actions (
                    symbol TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    ex_date TEXT NOT NULL,
                    ratio_multiplier REAL NOT NULL DEFAULT 1.0,
                    dividend_amount_inr REAL,
                    description TEXT NOT NULL,
                    source_filing TEXT,
                    PRIMARY KEY (symbol, action_type, ex_date)
                );

                CREATE TABLE IF NOT EXISTS financial_statements (
                    symbol TEXT NOT NULL,
                    fiscal_period TEXT NOT NULL,
                    period_end_date TEXT NOT NULL,
                    filing_date TEXT NOT NULL,
                    revenue_cr REAL,
                    ebitda_cr REAL,
                    pat_cr REAL,
                    eps REAL,
                    total_debt_cr REAL,
                    cash_equivalents_cr REAL,
                    operating_cash_flow_cr REAL,
                    free_cash_flow_cr REAL,
                    net_worth_cr REAL,
                    audit_status TEXT NOT NULL DEFAULT 'AUDITED',
                    source_reference TEXT,
                    PRIMARY KEY (symbol, fiscal_period)
                );
                """
            )
            conn.commit()

    def upsert_quote(self, quote: MarketQuote):
        """Stores or updates latest quote with strict metadata."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO quotes (
                    symbol, clean_ticker, instrument_name, exchange, current_price,
                    market_timestamp, retrieval_timestamp, data_provider, source_reference,
                    classification, freshness, currency, price_units, pe_ratio, pb_ratio,
                    eps, bvps, dividend_yield, market_cap_cr, debt_cr, cash_cr, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    current_price=excluded.current_price,
                    market_timestamp=excluded.market_timestamp,
                    retrieval_timestamp=excluded.retrieval_timestamp,
                    data_provider=excluded.data_provider,
                    source_reference=excluded.source_reference,
                    classification=excluded.classification,
                    freshness=excluded.freshness,
                    pe_ratio=excluded.pe_ratio,
                    pb_ratio=excluded.pb_ratio,
                    eps=excluded.eps,
                    bvps=excluded.bvps,
                    dividend_yield=excluded.dividend_yield,
                    market_cap_cr=excluded.market_cap_cr,
                    debt_cr=excluded.debt_cr,
                    cash_cr=excluded.cash_cr,
                    raw_json=excluded.raw_json;
                """,
                (
                    quote.symbol,
                    quote.clean_ticker,
                    quote.instrument_name,
                    quote.exchange,
                    quote.current_price,
                    quote.market_timestamp,
                    quote.retrieval_timestamp,
                    quote.data_provider,
                    quote.source_reference,
                    quote.classification.value if hasattr(quote.classification, "value") else str(quote.classification),
                    quote.freshness.value if hasattr(quote.freshness, "value") else str(quote.freshness),
                    quote.currency,
                    quote.price_units,
                    quote.pe_ratio,
                    quote.pb_ratio,
                    quote.eps,
                    quote.bvps,
                    quote.dividend_yield,
                    None,
                    quote.debt,
                    quote.cash,
                    quote.model_dump_json(),
                ),
            )
            conn.commit()

    def get_quote(self, symbol: str) -> Optional[MarketQuote]:
        """Retrieves cached quote for symbol."""
        clean = symbol.replace(".NS", "").replace(".BO", "").upper()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT raw_json FROM quotes WHERE symbol=? OR clean_ticker=?",
                (symbol, clean),
            )
            row = cursor.fetchone()
            if row and row["raw_json"]:
                return MarketQuote(**json.loads(row["raw_json"]))
        return None

    def insert_historical_bars(self, bars: List[HistoricalBar]):
        """Bulk inserts or updates daily historical bars with exact provenance."""
        if not bars:
            return
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            for b in bars:
                conn.execute(
                    """
                    INSERT INTO historical_bars (
                        symbol, exchange, trading_date, interval, open, high, low, close, volume,
                        adjustment_method, observation_timestamp, retrieval_timestamp,
                        data_provider, classification, freshness
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(symbol, trading_date, interval) DO UPDATE SET
                        open=excluded.open,
                        high=excluded.high,
                        low=excluded.low,
                        close=excluded.close,
                        volume=excluded.volume,
                        retrieval_timestamp=excluded.retrieval_timestamp;
                    """,
                    (
                        b.symbol,
                        b.exchange.value if hasattr(b.exchange, "value") else str(b.exchange),
                        b.trading_date,
                        "DAILY",
                        b.open,
                        b.high,
                        b.low,
                        b.close,
                        b.volume,
                        b.adjustment_method.value if hasattr(b.adjustment_method, "value") else str(b.adjustment_method),
                        b.timestamp_iso,
                        now_iso,
                        b.source,
                        b.data_classification.value if hasattr(b.data_classification, "value") else str(b.data_classification),
                        "FRESH",
                    ),
                )
            conn.commit()

    def get_historical_bars(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[HistoricalBar]:
        """Fetches chronological historical bars from store."""
        clean = symbol.replace(".NS", "").replace(".BO", "").upper()
        query = "SELECT * FROM historical_bars WHERE (symbol=? OR symbol=?) "
        params: List[Any] = [symbol, f"{clean}.NS"]
        if start_date:
            query += " AND trading_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND trading_date <= ?"
            params.append(end_date)
        query += " ORDER BY trading_date ASC"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            bars: List[HistoricalBar] = []
            for r in rows:
                bars.append(
                    HistoricalBar(
                        symbol=r["symbol"],
                        exchange=Exchange(r["exchange"]) if r["exchange"] in ["NSE", "BSE", "MCX"] else Exchange.NSE,
                        trading_date=r["trading_date"],
                        timestamp_iso=r["observation_timestamp"],
                        open=r["open"],
                        high=r["high"],
                        low=r["low"],
                        close=r["close"],
                        volume=r["volume"],
                        adjustment_method=AdjustmentMethod(r["adjustment_method"]) if r["adjustment_method"] in ["RAW_UNADJUSTED", "SPLIT_BONUS_ADJUSTED", "TOTAL_RETURN_ADJUSTED"] else AdjustmentMethod.RAW_UNADJUSTED,
                        source=r["data_provider"],
                        data_classification=DataClassification(r["classification"]) if r["classification"] in DataClassification._value2member_map_ else DataClassification.HISTORICAL_VERIFIED,
                    )
                )
            return bars


    def upsert_financial_statement(self, statement: Dict[str, Any]):
        """Upserts a quarterly or annual financial filing statement."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO financial_statements (
                    symbol, fiscal_period, period_end_date, filing_date, revenue_cr,
                    ebitda_cr, pat_cr, eps, total_debt_cr, cash_equivalents_cr,
                    operating_cash_flow_cr, free_cash_flow_cr, net_worth_cr,
                    audit_status, source_reference
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, fiscal_period) DO UPDATE SET
                    revenue_cr=excluded.revenue_cr,
                    ebitda_cr=excluded.ebitda_cr,
                    pat_cr=excluded.pat_cr,
                    eps=excluded.eps,
                    total_debt_cr=excluded.total_debt_cr,
                    cash_equivalents_cr=excluded.cash_equivalents_cr,
                    operating_cash_flow_cr=excluded.operating_cash_flow_cr,
                    free_cash_flow_cr=excluded.free_cash_flow_cr,
                    net_worth_cr=excluded.net_worth_cr,
                    source_reference=excluded.source_reference;
                """,
                (
                    statement["symbol"],
                    statement["fiscal_period"],
                    statement["period_end_date"],
                    statement["filing_date"],
                    statement.get("revenue_cr"),
                    statement.get("ebitda_cr"),
                    statement.get("pat_cr"),
                    statement.get("eps"),
                    statement.get("total_debt_cr"),
                    statement.get("cash_equivalents_cr"),
                    statement.get("operating_cash_flow_cr"),
                    statement.get("free_cash_flow_cr"),
                    statement.get("net_worth_cr"),
                    statement.get("audit_status", "AUDITED"),
                    statement.get("source_reference"),
                ),
            )
            conn.commit()

    def get_financial_statements(self, symbol: str) -> List[Dict[str, Any]]:
        """Retrieves financial statements ordered chronologically by period."""
        clean = symbol.replace(".NS", "").replace(".BO", "").upper()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM financial_statements WHERE symbol=? OR symbol=? ORDER BY period_end_date ASC",
                (symbol, clean),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]


market_data_store = MarketDataStore()
