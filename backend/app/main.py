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
    """Retrieves immutable records from the SQLite audit ledger."""
    return audit_ledger.list_records(limit=limit)


@app.get("/api/v1/audit/records/{audit_id}")
async def get_audit_record(audit_id: str) -> Dict[str, Any]:
    """Retrieves full research dossier payload for an audit record."""
    record = audit_ledger.get_record_by_id(audit_id)
    if not record:
        raise HTTPException(status_code=404, detail="Audit record not found")
    return record


class CompanionContextRequest(BaseModel):
    manual_text: Optional[str] = None
    paused: Optional[bool] = None


@app.post("/api/v1/companion/context")
async def process_companion_context(req: CompanionContextRequest) -> Dict[str, Any]:
    """Processes live context from companion screen capture or manual text input with privacy redactor."""
    if req.paused is not None:
        screen_companion.paused = req.paused

    return screen_companion.process_screen_context(manual_text=req.manual_text)
