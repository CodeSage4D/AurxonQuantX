"""AURXON Enhanced Source Registry.
Provides exhaustive source provenance, data field definitions, rate limits, license terms,
health state probes, and fallback hierarchy for Phase 4.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.company import EnhancedSourceMetadata, SourceHealthStatus


class EnhancedSourceRegistry:
    """Central registry tracking permitted data providers with health status and operational constraints."""

    def __init__(self):
        self._sources: Dict[str, EnhancedSourceMetadata] = {}
        self._initialize_registry()

    def _initialize_registry(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        sources = [
            EnhancedSourceMetadata(
                source_id="SRC_NSE_BSE",
                name="National Stock Exchange & BSE Official Feeds",
                category="EXCHANGE_OFFICIAL",
                supported_asset_classes=["Equities", "ETFs", "Indices", "Corporate Actions"],
                supported_symbols_or_scope="All actively listed Indian securities (Nifty 500 & BSE 500)",
                data_fields=["LTP", "Open", "High", "Low", "Close", "Volume", "52W High/Low", "Corporate Disclosures"],
                history_depth="Up to 10 years for historical Bhavcopy; real-time LODR disclosures",
                geographic_coverage="India (IN)",
                update_frequency="Continuous during trading hours (9:15 AM - 3:30 PM IST)",
                rate_limits="Bounded to max 30 requests/minute with jitter",
                authentication_required=False,
                license_status="Statutory Public Disclosures / Regulated Exchange Data",
                permitted_usage_notes="Private research analysis. High-frequency redistribution restricted.",
                last_successful_fetch=now_iso,
                last_observation_time=now_iso,
                health_status=SourceHealthStatus.HEALTHY,
                known_limitations=[
                    "Public web endpoints apply anti-scraping and header checks",
                    "After-market hours quotes reflect closing auction prices",
                ],
                fallback_policy="Fallback to local disk cache, then to curated audited benchmark archive.",
            ),
            EnhancedSourceMetadata(
                source_id="SRC_AMFI",
                name="Association of Mutual Funds in India (AMFI)",
                category="AMFI_AMC_OFFICIAL",
                supported_asset_classes=["Mutual Funds", "ETFs"],
                supported_symbols_or_scope="All registered Indian Mutual Fund schemes (>15,000 schemes)",
                data_fields=["Scheme Code", "Scheme Name", "Net Asset Value (NAV)", "Repurchase Price", "Sale Price", "Date"],
                history_depth="Complete historical NAV archive via official portal endpoints",
                geographic_coverage="India (IN)",
                update_frequency="Daily by 9:00 PM IST (statutory upload deadline 11:00 PM IST)",
                rate_limits="Max 60 requests/minute",
                authentication_required=False,
                license_status="Open Public Financial Data for Indian Investors",
                permitted_usage_notes="Free educational and quantitative analysis for Indian mutual fund portfolios.",
                last_successful_fetch=now_iso,
                last_observation_time=now_iso,
                health_status=SourceHealthStatus.HEALTHY,
                known_limitations=[
                    "Daily NAV text feed is ~4 MB; parsing requires structured regex streaming",
                    "Occasional delayed uploads for illiquid FMP schemes",
                ],
                fallback_policy="Use cached daily snapshot (data/cache/amfi_nav_history.txt); clearly label staleness.",
            ),
            EnhancedSourceMetadata(
                source_id="SRC_COMPANY_IR",
                name="Official Company Investor Relations & SEBI Filings",
                category="ISSUER_OFFICIAL",
                supported_asset_classes=["Equities"],
                supported_symbols_or_scope="Major listed corporate issuers on NSE/BSE",
                data_fields=["Quarterly Balance Sheets", "P&L Statements", "Cash Flow Statements", "Auditor Notes", "Investor Presentations"],
                history_depth="5 to 10 fiscal years (Annual Reports & SEBI Formats)",
                geographic_coverage="India (IN)",
                update_frequency="Quarterly financial results / Event-driven material announcements",
                rate_limits="On-demand document download with 10s backoff",
                authentication_required=False,
                license_status="Statutory Corporate Disclosures under SEBI LODR Regulations",
                permitted_usage_notes="Authoritative primary source for financial valuation and forensic accounting.",
                last_successful_fetch=now_iso,
                last_observation_time=now_iso,
                health_status=SourceHealthStatus.HEALTHY,
                known_limitations=[
                    "Unstructured PDF documents require OCR or tabular text extraction",
                    "Segmental reporting structures vary across industries",
                ],
                fallback_policy="Prompt operator for manual filing upload; do not interpolate missing line items.",
            ),
            EnhancedSourceMetadata(
                source_id="SRC_RBI",
                name="Reserve Bank of India Database on Indian Economy (DBIE)",
                category="CENTRAL_BANK_REGULATORY",
                supported_asset_classes=["Macroeconomic Indicators", "Banking Sector", "Government Securities"],
                supported_symbols_or_scope="Monetary policy rates, 10Y G-Sec yield, banking credit growth",
                data_fields=["Policy Repo Rate", "SDF Rate", "MSF Rate", "10Y Benchmark G-Sec Yield", "CPI Inflation"],
                history_depth="Over 25 years of official monthly/weekly time series",
                geographic_coverage="India (IN)",
                update_frequency="Bi-monthly Monetary Policy Committee (MPC) meetings / Weekly statistical supplements",
                rate_limits="Max 20 requests/minute",
                authentication_required=False,
                license_status="Official Government Statistical Portal (Creative Commons / Public Domain)",
                permitted_usage_notes="Authoritative risk-free rate calibration (Rf = 6.5%) and macro stress modeling.",
                last_successful_fetch=now_iso,
                last_observation_time=now_iso,
                health_status=SourceHealthStatus.HEALTHY,
                known_limitations=[
                    "Macro time series updated weekly/monthly; not suitable for intraday tick triggers",
                ],
                fallback_policy="Apply hardcoded statutory benchmark risk-free rate (6.50% annualized).",
            ),
            EnhancedSourceMetadata(
                source_id="SRC_ALPHA_VANTAGE",
                name="Alpha Vantage Market Data API",
                category="AGGREGATOR",
                supported_asset_classes=["Equities", "FX"],
                supported_symbols_or_scope="Indian securities with .BSE or .NSE suffix",
                data_fields=["Daily OHLCV", "Adjusted Close", "Volume", "Technical Indicators"],
                history_depth="20+ years of daily OHLCV historical series",
                geographic_coverage="Global (including India)",
                update_frequency="End-of-day daily bars / 15-minute delayed quotes",
                rate_limits="Free tier: 25 requests/day and 5 requests/minute",
                authentication_required=True,
                license_status="Commercial API / Free Tier Personal Use",
                permitted_usage_notes="Permitted for personal research; quota must be conserved.",
                last_successful_fetch=None,
                last_observation_time=None,
                health_status=SourceHealthStatus.UNCONFIGURED,
                known_limitations=[
                    "Free tier limited to 25 requests/day",
                    "Requires ALPHA_VANTAGE_API_KEY environment variable",
                ],
                fallback_policy="Fallback to local Bhavcopy archive or synthetic benchmark fixtures.",
            ),
            EnhancedSourceMetadata(
                source_id="SRC_BENCHMARK_ARCHIVE",
                name="AURXON Curated Audited Benchmark Archive",
                category="SYNTHETIC_BENCHMARK",
                supported_asset_classes=["Equities", "Indices", "Corporate Actions"],
                supported_symbols_or_scope="Audited Nifty 50 benchmarks (RELIANCE, TCS, INFY, HDFCBANK, NIFTY50)",
                data_fields=["Verified Daily OHLCV", "Audited Financials", "Piotroski Raw", "Corporate Actions", "Ratios"],
                history_depth="2020 to 2026 ground-truth historical daily series",
                geographic_coverage="India (IN)",
                update_frequency="Static / Version-Controlled Fixtures",
                rate_limits="Unlimited (Local disk / in-memory read)",
                authentication_required=False,
                license_status="Proprietary / Audited Calibration Dataset",
                permitted_usage_notes="Deterministic testing and offline regression baseline.",
                last_successful_fetch=now_iso,
                last_observation_time=now_iso,
                health_status=SourceHealthStatus.HEALTHY,
                known_limitations=[
                    "Covers curated top benchmarks only; uncurated tickers return UNAVAILABLE",
                ],
                fallback_policy="Terminal baseline. Clearly labeled as SYNTHETIC_BENCHMARK / OFFLINE_FROZEN.",
            ),
            EnhancedSourceMetadata(
                source_id="SRC_WEB_DISCOVERY",
                name="Permitted Web Discovery & Regulatory Announcements",
                category="DISCOVERY_TOOL",
                supported_asset_classes=["Corporate Announcements", "Press Releases", "Regulatory Orders"],
                supported_symbols_or_scope="SEBI Press, Exchange News, Tier-1 Business Daily Portals",
                data_fields=["Headline", "Publication Date", "Source URL", "Extracted Paragraphs", "Citations"],
                history_depth="Recent 12 months news & material events",
                geographic_coverage="India (IN)",
                update_frequency="Real-time / Event-driven",
                rate_limits="Bounded to max 10 requests/minute",
                authentication_required=False,
                license_status="Public News & Web Content",
                permitted_usage_notes="Treated strictly as UNTRUSTED PASSIVE INPUT. Prompt injection filters enforced.",
                last_successful_fetch=now_iso,
                last_observation_time=now_iso,
                health_status=SourceHealthStatus.HEALTHY,
                known_limitations=[
                    "Secondary discovery only; must be corroborated by official filings before trade consideration",
                    "No unauthorized scraping of paywalled or terms-restricted services",
                ],
                fallback_policy="Report missing news evidence; never synthesize fictitious rumors.",
            ),
        ]
        for s in sources:
            self._sources[s.source_id] = s

    def get_source(self, source_id: str) -> Optional[EnhancedSourceMetadata]:
        return self._sources.get(source_id)

    def list_sources(self) -> List[EnhancedSourceMetadata]:
        return list(self._sources.values())

    def update_fetch_status(self, source_id: str, success: bool, observation_time: Optional[str] = None):
        """Updates health status and timestamps upon fetch completion."""
        src = self._sources.get(source_id)
        if not src:
            return
        now_iso = datetime.now(timezone.utc).isoformat()
        if success:
            src.last_successful_fetch = now_iso
            src.health_status = SourceHealthStatus.HEALTHY
            if observation_time:
                src.last_observation_time = observation_time
        else:
            src.health_status = SourceHealthStatus.DEGRADED


enhanced_source_registry = EnhancedSourceRegistry()
