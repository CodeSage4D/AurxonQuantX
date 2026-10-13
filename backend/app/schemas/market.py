"""AURXON Market Data Provenance Schemas.
Enforces strict provenance, source attribution, freshness tracking, and data classification.
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class DataClassification(str, Enum):
    """Rigorous classification of data provenance and fidelity."""
    # Phase 2.2 Canonical States
    LIVE_VERIFIED = "LIVE_VERIFIED"
    DELAYED_VERIFIED = "DELAYED_VERIFIED"
    HISTORICAL_VERIFIED = "HISTORICAL_VERIFIED"
    CACHED = "CACHED"
    SYNTHETIC = "SYNTHETIC"
    UNVERIFIED = "UNVERIFIED"
    UNAVAILABLE = "UNAVAILABLE"

    # Existing milestone naming conventions preserved with identical semantics
    LIVE_EXCHANGE = "LIVE_EXCHANGE"
    DELAYED_EXCHANGE = "DELAYED_EXCHANGE"
    THIRD_PARTY_DELAYED = "THIRD_PARTY_DELAYED"
    CACHED_LOCAL = "CACHED_LOCAL"
    HISTORICAL_FILING = "HISTORICAL_FILING"
    SYNTHETIC_BENCHMARK = "SYNTHETIC_BENCHMARK"


class FreshnessStatus(str, Enum):
    FRESH = "FRESH"  # Under 15 minutes old during trading session
    STALE_ACCEPTABLE = "STALE_ACCEPTABLE"  # Under 24 hours old (after-market hours or weekend)
    STALE_WARNING = "STALE_WARNING"  # Over 24 hours old
    OFFLINE_FROZEN = "OFFLINE_FROZEN"  # Static frozen fixture for reproducibility
    UNKNOWN = "UNKNOWN"


class MarketQuote(BaseModel):
    """Complete, auditable market quote carrying strict provenance metadata."""

    symbol: str = Field(description="Trading symbol with exchange suffix (e.g. RELIANCE.NS)")
    clean_ticker: str = Field(description="Normalized ticker (e.g. RELIANCE)")
    instrument_name: str = Field(description="Full corporate entity or fund name")
    exchange: str = Field(default="NSE", description="Primary Indian exchange: NSE or BSE")
    data_provider: str = Field(description="Actual data provider identity")
    source_reference: str = Field(description="URL or official filing citation")

    classification: DataClassification = Field(description="Provenance category")
    freshness: FreshnessStatus = Field(description="Time-decay freshness state")

    currency: str = Field(default="INR", description="Denominated currency")
    price_units: str = Field(default="INR per share", description="Physical unit of the quote")
    current_price: Optional[float] = Field(default=None, description="Last traded or closing price")

    market_timestamp: Optional[str] = Field(default=None, description="Trade execution or market close ISO timestamp")
    retrieval_timestamp: str = Field(description="ISO 8601 timestamp when AURXON fetched the record")

    eps: Optional[float] = None
    bvps: Optional[float] = None
    fcf: Optional[float] = None  # in INR Crores
    shares_outstanding: Optional[float] = None  # in Crores shares
    cash: Optional[float] = None
    debt: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    sector: str = Field(default="Unknown", description="Industry classification")
    is_financial_institution: bool = Field(default=False, description="True for Banks and NBFCs requiring specialized metrics")

    piotroski_raw: Optional[Dict[str, Any]] = None
    provenance_notes: Optional[str] = None
