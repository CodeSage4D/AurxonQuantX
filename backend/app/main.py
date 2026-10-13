"""AURXON Investment Intelligence Hub — Core Backend Server.
Provides Server-Sent Events (SSE) research streaming, deterministic analytics,
market data connectors, audit ledger queries, and live companion OCR endpoints.
"""

import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.analytics.valuation import compute_deterministic_valuation_dossier
from app.companion.screen_ocr import screen_companion
from app.config import settings
from app.evidence.ledger import audit_ledger
from app.market_data.nse_connector import NSEDataConnector
from app.model_adapters.registry import model_registry
from app.orchestration.evidence_loop import evidence_loop_workflow
from app.schemas.research import (
    ResearchFinding,
    ResearchObjective,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation
    assert not settings.ENABLE_REAL_TRADING, "CRITICAL SAFETY VIOLATION: Real-money trading MUST be disabled!"
    yield


app = FastAPI(
    title="AURXON Investment Intelligence Hub API",
    version="1.0.0",
    description="Founder-operated financial research platform for Indian markets with deterministic verification.",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],  # Permits local dev and Tauri webview
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

market_connector = NSEDataConnector()


@app.get("/api/v1/health")
async def health_check() -> Dict[str, Any]:
    """Returns system diagnostic status, safety controls, and available engines."""
    return {
        "status": "HEALTHY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "real_trading_enabled": settings.ENABLE_REAL_TRADING,
        "paper_trading_capital_inr": settings.PAPER_TRADING_INITIAL_CAPITAL,
        "ocr_available": screen_companion.is_ocr_available(),
        "registered_models": model_registry.list_available_models(),
    }


@app.get("/api/v1/market/quote/{ticker}")
async def get_market_quote(ticker: str) -> Dict[str, Any]:
    """Fetches verified quote and deterministic baseline valuation for an Indian equity."""
    data = market_connector.get_stock_data(ticker)
    price = data.get("current_price", 0.0)

    valuation = compute_deterministic_valuation_dossier(
        ticker=ticker.upper(),
        current_price=price,
        eps=data.get("eps", 50.0),
        bvps=data.get("bvps", 200.0),
        fcf=data.get("fcf", 2000.0),
        shares_outstanding=data.get("shares_outstanding", 50.0),
        cash=data.get("cash", 1000.0),
        debt=data.get("debt", 200.0),
        pe_ratio=data.get("pe_ratio", 20.0),
        pb_ratio=data.get("pb_ratio", 2.0),
        piotroski_metrics=data.get("piotroski"),
        dividend_yield_percent=data.get("dividend_yield", 1.0),
    )

    return {
        "market_data": data,
        "deterministic_valuation": valuation.model_dump(),
    }


@app.post("/api/v1/research/stream")
async def stream_research(
    objective: ResearchObjective,
    model_key: Optional[str] = Query(default=None, description="Optional model adapter key"),
):
    """Executes the 10-step AURXON Evidence-Loop workflow and streams live events via Server-Sent Events (SSE)."""

    async def event_generator():
        try:
            async for event in evidence_loop_workflow.execute_stream(objective, model_key=model_key):
                event_data = event.model_dump_json()
                yield f"event: research_progress\ndata: {event_data}\n\n"
        except Exception as exc:
            err_payload = json.dumps({"error": str(exc), "status": "FAILED"})
            yield f"event: error\ndata: {err_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/v1/research/sync", response_model=ResearchFinding)
async def sync_research(
    objective: ResearchObjective,
    model_key: Optional[str] = Query(default=None),
) -> ResearchFinding:
    """Synchronous execution of the Evidence-Loop, returning complete research dossier."""
    last_event = None
    async for event in evidence_loop_workflow.execute_stream(objective, model_key=model_key):
        last_event = event

    if last_event and last_event.step == "RESEARCH_COMPLETE":
        finding_data = last_event.data.get("finding")
        if finding_data:
            return ResearchFinding(**finding_data)

    raise HTTPException(status_code=500, detail="Research loop completed without generating final dossier.")


@app.get("/api/v1/audit/records")
async def list_audit_records(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves records from the cryptographic audit ledger."""
    return audit_ledger.list_records(limit=limit)


@app.get("/api/v1/audit/integrity")
async def verify_audit_integrity() -> Dict[str, Any]:
    """Verifies the cryptographic hash-chain integrity of the entire audit trail."""
    is_valid, count, err = audit_ledger.verify_chain_integrity()
    return {
        "is_valid": is_valid,
        "records_verified": count,
        "error": err,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/audit/records/{audit_id}")
async def get_audit_record(audit_id: str) -> Dict[str, Any]:
    """Retrieves full research dossier payload for an audit record."""
    record = audit_ledger.get_record_by_id(audit_id)
    if not record:
        raise HTTPException(status_code=404, detail="Audit record not found")
    return record


# ============================================================================
# PHASE 2: SOURCE REGISTRY, INGESTION, IPO & MUTUAL FUND INTELLIGENCE
# ============================================================================

from fastapi import File, UploadFile
from app.sources.registry import source_registry
from app.ingestion.parser import document_parser, DocumentIngestionResult
from app.ipo.analyzer import ipo_analyzer
from app.funds.analyzer import fund_analyzer
from app.connectors.amfi_connector import amfi_connector, AMFINavRecord
from app.schemas.semantics import FieldLineageRecord, RecommendationReadinessGate
from app.schemas.ipo import IPODossier
from app.schemas.funds import FundComparisonResult, PortfolioAllocationPlan
from app.trading.engine import (
    backtest_engine,
    BacktestExecutionResult,
    DeterministicBacktestEngine,
    DualMovingAverageStrategy,
    BuyAndHoldStrategy,
)
from app.trading.costs import IndianTransactionCostModel
from app.trading.fixtures import (
    RELIANCE_SERIES,
    TCS_BONUS_SERIES,
    NIFTY50_BENCHMARK_SERIES,
)
from app.schemas.historical_data import validate_historical_series
from app.trading.paper_manager import paper_manager
from app.schemas.paper_trading import (
    PaperOrderRequest,
    PaperOrderRecord,
    PaperPortfolioState,
    CancelOrderRequest,
    KillSwitchRequest,
    PaperCorporateActionRequest,
)


@app.get("/api/v1/sources")
async def list_sources():
    """Returns registered regulatory, exchange, and filing data sources."""
    return source_registry.list_sources()


MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


@app.post("/api/v1/ingestion/upload", response_model=DocumentIngestionResult)
async def upload_document(file: UploadFile = File(...)) -> DocumentIngestionResult:
    """Uploads DRHP/RHP PDF or HTML document, extracts sections/tables, and sanitizes untrusted input."""
    content = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file exceeds maximum allowed limit of {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB",
        )

    filename = file.filename or "uploaded_filing.pdf"

    if filename.lower().endswith(".pdf"):
        return document_parser.parse_pdf_bytes(content, filename)
    else:
        text_content = content.decode("utf-8", errors="ignore")
        return document_parser.parse_text_or_html(text_content, filename)


@app.get("/api/v1/ipo/list")
async def list_ipos():
    """Lists tracked Indian IPOs available for research."""
    return [
        {
            "symbol": "BAJAJHFL",
            "issuer_name": "Bajaj Housing Finance Limited",
            "price_band": "₹66 - ₹70",
            "issue_size_cr": 6560.0,
            "status": "RHP Filed / Benchmark Fixture",
        },
        {
            "symbol": "TATATECH",
            "issuer_name": "Tata Technologies Limited",
            "price_band": "₹475 - ₹500",
            "issue_size_cr": 3042.5,
            "status": "Listed / Benchmark Fixture",
        },
    ]


@app.get("/api/v1/ipo/analyze/{symbol_or_name}", response_model=IPODossier)
async def analyze_ipo_endpoint(symbol_or_name: str) -> IPODossier:
    """Produces comprehensive 7-point IPO prospectus dossier with deterministic dilution and peer valuation."""
    dossier = ipo_analyzer.analyze_ipo(symbol_or_name)
    return dossier


@app.get("/api/v1/ipo/lineage/{symbol_or_name}", response_model=List[FieldLineageRecord])
async def get_ipo_lineage_endpoint(symbol_or_name: str) -> List[FieldLineageRecord]:
    """Retrieves document-level audit lineage records for material prospectus metrics."""
    return ipo_analyzer.get_lineage_records(symbol_or_name)


@app.get("/api/v1/gates/readiness/{symbol_or_name}", response_model=RecommendationReadinessGate)
async def get_readiness_gate_endpoint(symbol_or_name: str) -> RecommendationReadinessGate:
    """Retrieves multi-dimensional evidence readiness gates evaluating if recommendation can be safely issued."""
    return ipo_analyzer.get_readiness_gate(symbol_or_name)


@app.get("/api/v1/funds/list")
async def list_funds():
    """Lists curated Indian mutual fund and ETF benchmark schemes."""
    return [
        {"scheme_code": "PPFAS_FLEXI", "name": "Parag Parikh Flexi Cap Fund", "category": "FLEXI_CAP", "plan": "DIRECT"},
        {"scheme_code": "NIFTYBEES", "name": "Nippon India ETF Nifty 50 BeES", "category": "INDEX_ETF", "plan": "DIRECT"},
        {"scheme_code": "MIRAE_LARGE", "name": "Mirae Asset Large Cap Fund", "category": "LARGE_CAP", "plan": "DIRECT"},
    ]


@app.get("/api/v1/funds/nav/{scheme_code}", response_model=AMFINavRecord)
async def get_fund_nav_endpoint(scheme_code: str) -> AMFINavRecord:
    """Fetches official statutory daily AMFI NAV record with verified primary source attribution."""
    record = await amfi_connector.get_nav(scheme_code)
    if not record:
        raise HTTPException(status_code=404, detail=f"Scheme code '{scheme_code}' not found in official AMFI daily records")
    return record


@app.get("/api/v1/funds/compare", response_model=FundComparisonResult)
async def compare_funds_endpoint(code_a: str = Query(default="PPFAS_FLEXI"), code_b: str = Query(default="NIFTYBEES")) -> FundComparisonResult:
    """Compares two mutual fund/ETF schemes with mathematical portfolio overlap and direct plan savings."""
    return fund_analyzer.compare_funds(code_a, code_b)


class AllocationRequest(BaseModel):
    goal_name: str = "Wealth Creation"
    horizon_years: int = 7
    risk_profile: str = "moderate"


@app.post("/api/v1/funds/allocate", response_model=PortfolioAllocationPlan)
async def allocate_portfolio_endpoint(req: AllocationRequest) -> PortfolioAllocationPlan:
    """Generates transparent goal-based asset allocation proposal with downside stress testing."""
    return fund_analyzer.generate_portfolio_allocation(
        goal_name=req.goal_name,
        horizon_years=req.horizon_years,
        risk_profile=req.risk_profile,
    )


class BacktestRunRequest(BaseModel):
    symbol: str = "RELIANCE"
    strategy: str = "DualMovingAverage"
    parameters: Dict[str, Any] = Field(default_factory=lambda: {"fast_period": 10, "slow_period": 30, "quantity": 10})
    initial_capital: float = 100000.0
    slippage_bps: float = 5.0


@app.get("/api/v1/backtest/strategies")
async def list_backtest_strategies():
    """Lists available deterministic strategies with parameter specifications."""
    return [
        {
            "id": "DualMovingAverage",
            "name": "Dual Moving Average Crossover",
            "description": "Trend-following strategy generating signals when fast SMA crosses slow SMA. Next-bar execution (T+1 Open).",
            "default_parameters": {"fast_period": 10, "slow_period": 30, "quantity": 10},
        },
        {
            "id": "BuyAndHold",
            "name": "Buy & Hold Benchmark",
            "description": "Allocates once on first eligible bar and holds throughout simulation for passive benchmark comparison.",
            "default_parameters": {"quantity": 10},
        },
    ]


@app.get("/api/v1/backtest/fixtures")
async def list_backtest_fixtures():
    """Lists validated historical OHLCV bar fixtures available for deterministic replay."""
    return [
        {
            "symbol": "RELIANCE",
            "bars_count": len(RELIANCE_SERIES),
            "corporate_actions": "Interim Dividend ₹10",
            "classification": "SYNTHETIC_BENCHMARK",
            "is_demonstration": True,
            "caveat": "Curated benchmark fixture. Not a live exchange feed.",
        },
        {
            "symbol": "TCS",
            "bars_count": len(TCS_BONUS_SERIES),
            "corporate_actions": "1:1 Bonus Issue",
            "classification": "SYNTHETIC_BENCHMARK",
            "is_demonstration": True,
            "caveat": "Curated benchmark fixture. Not a live exchange feed.",
        },
        {
            "symbol": "NIFTY50_INDEX",
            "bars_count": len(NIFTY50_BENCHMARK_SERIES),
            "corporate_actions": "None (Benchmark Index)",
            "classification": "SYNTHETIC_BENCHMARK",
            "is_demonstration": True,
            "caveat": "Curated benchmark fixture. Not a live exchange feed.",
        },
    ]


@app.post("/api/v1/backtest/run", response_model=BacktestExecutionResult)
async def run_backtest_endpoint(req: BacktestRunRequest) -> BacktestExecutionResult:
    """Executes deterministic, event-driven backtest with statutory Indian transaction costs."""
    # Match historical series fixture explicitly; never substitute silently
    clean_sym = req.symbol.strip().upper()
    if clean_sym in ["TCS", "TCS.NS"]:
        bars = TCS_BONUS_SERIES
    elif clean_sym in ["RELIANCE", "RIL", "RELIANCE.NS"]:
        bars = RELIANCE_SERIES
    elif clean_sym in ["NIFTY", "NIFTY50", "NIFTY_50", "NIFTY50_INDEX"]:
        bars = NIFTY50_BENCHMARK_SERIES
    else:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Historical equity data for '{req.symbol}' is unavailable. "
                "Empirical backtesting on uncurated Indian equities is BLOCKED until licensed exchange feeds (Bhavcopy/Tick) are integrated. "
                "Supported demonstration benchmark fixtures: RELIANCE, TCS, NIFTY50_INDEX."
            ),
        )

    # Configure Strategy
    strat_id = req.strategy.strip()
    if strat_id in ["DualMovingAverage", "DualMovingAverageCrossover"]:
        strategy = DualMovingAverageStrategy(
            fast_period=req.parameters.get("fast_period", 10),
            slow_period=req.parameters.get("slow_period", 30),
            quantity=req.parameters.get("quantity", 10),
        )
    elif strat_id in ["BuyAndHold", "BuyAndHoldBenchmark"]:
        strategy = BuyAndHoldStrategy(quantity=req.parameters.get("quantity", 10))
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported strategy '{req.strategy}'")

    # Cost model with requested slippage
    cost_model = IndianTransactionCostModel(slippage_bps=req.slippage_bps)
    custom_engine = DeterministicBacktestEngine(cost_model=cost_model)

    result = custom_engine.run_backtest(
        strategy=strategy,
        bars=bars,
        initial_capital=req.initial_capital,
        benchmark_bars=NIFTY50_BENCHMARK_SERIES,
    )
    return result


@app.get("/api/v1/export/report")
async def export_report(
    target_type: str = Query(default="ipo", description="equity, ipo, or allocation"),
    identifier: str = Query(default="BAJAJHFL"),
):
    """Generates an exportable, auditable research dossier in Markdown and JSON formats."""
    if target_type == "ipo":
        dossier = ipo_analyzer.analyze_ipo(identifier)
        md_text = f"""# AURXON IPO Research Dossier: {dossier.issuer_name}
**Audit ID:** {dossier.audit_id}  
**Recommendation:** {dossier.overall_recommendation.value}  
**Price Band:** ₹{dossier.structure.price_band_floor} - ₹{dossier.structure.price_band_cap}  
**Total Issue Size:** ₹{dossier.structure.total_issue_crores:,.1f} Cr (Fresh: ₹{dossier.structure.fresh_issue_crores:,.1f} Cr | OFS: ₹{dossier.structure.offer_for_sale_crores:,.1f} Cr)  
**Equity Dilution:** {dossier.structure.dilution_percent}%  

### 1. Business Quality Verdict
{dossier.business_quality_verdict}

### 2. Financial Quality Verdict
{dossier.financial_quality_verdict}

### 3. Valuation Verdict vs Listed Peers
{dossier.valuation_verdict}

### 4. Disclosed Material Risks ({len(dossier.risks)})
"""
        for r in dossier.risks:
            md_text += f"- **[{r.severity.value}] {r.title}**: {r.description} *(Ref: Page {r.page_reference})*\n"

        md_text += f"\n### 5. Listing Speculation vs Long-Term Ownership\n{dossier.listing_speculation_vs_long_term}\n"

        return {
            "target_type": "ipo",
            "identifier": identifier,
            "markdown_report": md_text,
            "payload_json": dossier.model_dump(),
        }
    else:
        alloc = fund_analyzer.generate_portfolio_allocation("Founder Long-Term Allocation", 7, "moderate")
        return {
            "target_type": "allocation",
            "identifier": "allocation_plan",
            "markdown_report": f"# AURXON Portfolio Allocation Plan\nEquity: {alloc.recommended_equity_pct}%\nDebt: {alloc.recommended_debt_pct}%\nGold: {alloc.recommended_gold_pct}%\nStress Drawdown: -{alloc.downside_stress_scenario_drawdown_pct}%\n",
            "payload_json": alloc.model_dump(),
        }


class CompanionContextRequest(BaseModel):
    manual_text: Optional[str] = None
    paused: Optional[bool] = None


@app.post("/api/v1/companion/context")
async def process_companion_context(req: CompanionContextRequest) -> Dict[str, Any]:
    """Processes live context from companion screen capture or manual text input with privacy redactor."""
    if req.paused is not None:
        screen_companion.paused = req.paused

    return screen_companion.process_screen_context(manual_text=req.manual_text)


# ============================================================================
# PHASE 3 STAGE 2: PAPER TRADING PORTFOLIO MANAGER API
# ============================================================================

@app.get("/api/v1/paper/portfolio", response_model=PaperPortfolioState)
async def get_paper_portfolio_endpoint(portfolio_id: str = "DEFAULT") -> PaperPortfolioState:
    """Returns the persistent virtual cash, equity, open positions, and risk status of the paper portfolio."""
    return paper_manager.get_portfolio_state(portfolio_id=portfolio_id)


@app.post("/api/v1/paper/order", response_model=PaperOrderRecord)
async def submit_paper_order_endpoint(req: PaperOrderRequest) -> PaperOrderRecord:
    """Submits and simulates execution of a paper order with statutory costs, risk vetoes, and duplicate protection."""
    return paper_manager.submit_order(req)


@app.post("/api/v1/paper/order/cancel", response_model=PaperOrderRecord)
async def cancel_paper_order_endpoint(req: CancelOrderRequest) -> PaperOrderRecord:
    """Cancels an open or submitted paper order if not yet filled."""
    try:
        return paper_manager.cancel_order(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/paper/orders", response_model=List[PaperOrderRecord])
async def list_paper_orders_endpoint(portfolio_id: str = "DEFAULT", limit: int = 50) -> List[PaperOrderRecord]:
    """Lists recent paper orders and execution history."""
    return paper_manager.list_orders(portfolio_id=portfolio_id, limit=limit)


@app.post("/api/v1/paper/kill-switch", response_model=PaperPortfolioState)
async def toggle_paper_kill_switch_endpoint(req: KillSwitchRequest) -> PaperPortfolioState:
    """Engages or disengages the emergency risk kill switch to halt all simulated order placement."""
    return paper_manager.toggle_kill_switch(req)


@app.post("/api/v1/paper/corporate-action")
async def apply_paper_corporate_action_endpoint(req: PaperCorporateActionRequest) -> Dict[str, Any]:
    """Simulates a statutory corporate action (cash dividend, stock split, bonus) on open virtual positions."""
    try:
        return paper_manager.apply_corporate_action(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/paper/reset", response_model=PaperPortfolioState)
async def reset_paper_portfolio_endpoint(portfolio_id: str = "DEFAULT", initial_cash: float = 1000000.0) -> PaperPortfolioState:
    """Resets the virtual paper portfolio to initial cash for testing/demo scenarios."""
    return paper_manager.reset_portfolio(portfolio_id=portfolio_id, initial_cash=initial_cash)

