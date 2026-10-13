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
from pydantic import BaseModel

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
from app.schemas.ipo import IPODossier
from app.schemas.funds import FundComparisonResult, PortfolioAllocationPlan


@app.get("/api/v1/sources")
async def list_sources():
    """Returns registered regulatory, exchange, and filing data sources."""
    return source_registry.list_sources()


@app.post("/api/v1/ingestion/upload", response_model=DocumentIngestionResult)
async def upload_document(file: UploadFile = File(...)) -> DocumentIngestionResult:
    """Uploads DRHP/RHP PDF or HTML document, extracts sections/tables, and sanitizes untrusted input."""
    content = await file.read()
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


@app.get("/api/v1/funds/list")
async def list_funds():
    """Lists curated Indian mutual fund and ETF benchmark schemes."""
    return [
        {"scheme_code": "PPFAS_FLEXI", "name": "Parag Parikh Flexi Cap Fund", "category": "FLEXI_CAP", "plan": "DIRECT"},
        {"scheme_code": "NIFTYBEES", "name": "Nippon India ETF Nifty 50 BeES", "category": "INDEX_ETF", "plan": "DIRECT"},
        {"scheme_code": "MIRAE_LARGE", "name": "Mirae Asset Large Cap Fund", "category": "LARGE_CAP", "plan": "DIRECT"},
    ]


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
