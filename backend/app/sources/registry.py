"""AURXON Source Registry Module.
Defines source types, access protocols, reliability weights, attribution, and fallback behavior.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SourceCategory(str, Enum):
    PRIMARY_REGULATORY = "PRIMARY_REGULATORY"  # SEBI, RBI, MCA official gazettes/orders
    ISSUER_OFFICIAL = "ISSUER_OFFICIAL"  # DRHP, RHP, Prospectus, Investor Relations, Annual Reports
    EXCHANGE_OFFICIAL = "EXCHANGE_OFFICIAL"  # NSE, BSE official disclosures and circulars
    AMFI_AMC_OFFICIAL = "AMFI_AMC_OFFICIAL"  # AMFI, AMC Scheme Information Documents (SID), Factsheets
    REPUTABLE_SECONDARY = "REPUTABLE_SECONDARY"  # CRISIL, ICRA rating rationales, Tier-1 business press
    AGGREGATOR = "AGGREGATOR"  # Yahoo Finance, Google Finance, Moneycontrol, Screener
    CACHED_LOCAL = "CACHED_LOCAL"  # Local disk-cached snapshot from previous fetch
    SYNTHETIC_BENCHMARK = "SYNTHETIC_BENCHMARK"  # Curated offline reference fixtures for regression


class AccessMethod(str, Enum):
    REST_API = "REST_API"
    DIRECT_HTTP = "DIRECT_HTTP"
    LOCAL_PARSER = "LOCAL_PARSER"
    MANUAL_UPLOAD = "MANUAL_UPLOAD"


class SourceRegistration(BaseModel):
    source_id: str
    name: str
    category: SourceCategory
    access_method: AccessMethod
    base_url_or_pattern: str
    reliability_weight: float = Field(ge=0.0, le=1.0)
    update_frequency: str
    attribution_notice: str
    fallback_behavior: str
    respects_robots_txt: bool = True
    authentication_required: bool = False


class SourceRegistry:
    """Central registry tracking all data and document sources with provenance policies."""

    def __init__(self):
        self._sources: Dict[str, SourceRegistration] = {}
        self._register_default_sources()

    def _register_default_sources(self):
        defaults = [
            SourceRegistration(
                source_id="SRC_SEBI",
                name="Securities and Exchange Board of India (SEBI)",
                category=SourceCategory.PRIMARY_REGULATORY,
                access_method=AccessMethod.DIRECT_HTTP,
                base_url_or_pattern="https://www.sebi.gov.in",
                reliability_weight=1.0,
                update_frequency="Daily / Circular-driven",
                attribution_notice="Statutory Regulatory Body of India",
                fallback_behavior="Log failure; search exchange circulars; do not fabricate.",
            ),
            SourceRegistration(
                source_id="SRC_NSE_BSE",
                name="National Stock Exchange & BSE India Filings",
                category=SourceCategory.EXCHANGE_OFFICIAL,
                access_method=AccessMethod.DIRECT_HTTP,
                base_url_or_pattern="https://www.nseindia.com, https://www.bseindia.com",
                reliability_weight=0.98,
                update_frequency="Continuous (Market Hours) / Real-Time Disclosures",
                attribution_notice="Regulated Indian Exchanges (LODR Disclosures)",
                fallback_behavior="Cascade to local cached disclosures or offline benchmark archive.",
            ),
            SourceRegistration(
                source_id="SRC_ISSUER_PROSPECTUS",
                name="Issuer DRHP / RHP Filing",
                category=SourceCategory.ISSUER_OFFICIAL,
                access_method=AccessMethod.MANUAL_UPLOAD,
                base_url_or_pattern="Local PDF / SEBI IPO Repository",
                reliability_weight=0.95,
                update_frequency="Milestone-driven (Pre-IPO / Post-Issue)",
                attribution_notice="Legal Offering Prospectus filed with SEBI/ROC",
                fallback_behavior="Prompt founder for manual PDF prospectus upload; do not guess terms.",
            ),
            SourceRegistration(
                source_id="SRC_AMFI",
                name="Association of Mutual Funds in India (AMFI)",
                category=SourceCategory.AMFI_AMC_OFFICIAL,
                access_method=AccessMethod.DIRECT_HTTP,
                base_url_or_pattern="https://www.amfiindia.com",
                reliability_weight=0.98,
                update_frequency="Daily NAVs (9:00 PM IST) / Monthly Portfolio Disclosures",
                attribution_notice="Official AMFI NAV & Scheme Master Registry",
                fallback_behavior="Use cached NAV or benchmark scheme history; clearly label staleness.",
            ),
            SourceRegistration(
                source_id="SRC_AMC_SID",
                name="AMC Scheme Information Documents & Monthly Factsheets",
                category=SourceCategory.AMFI_AMC_OFFICIAL,
                access_method=AccessMethod.LOCAL_PARSER,
                base_url_or_pattern="Official AMC Portals",
                reliability_weight=0.96,
                update_frequency="Monthly (Portfolio) / Periodic (SID)",
                attribution_notice="Asset Management Company Official Disclosure",
                fallback_behavior="Mark incomplete fields as 'AWAITING_MONTHLY_FACTSHEET'.",
            ),
            SourceRegistration(
                source_id="SRC_BENCHMARK_ARCHIVE",
                name="AURXON Curated Ground-Truth Benchmark Fixtures",
                category=SourceCategory.SYNTHETIC_BENCHMARK,
                access_method=AccessMethod.LOCAL_PARSER,
                base_url_or_pattern="data/benchmark_fixtures/",
                reliability_weight=0.90,
                update_frequency="Static / Version-Controlled",
                attribution_notice="Audited Historical Ground-Truth Calibration Dataset",
                fallback_behavior="Terminal offline safety net; strictly tagged as SYNTHETIC_BENCHMARK.",
            ),
        ]
        for src in defaults:
            self.register_source(src)

    def register_source(self, source: SourceRegistration):
        self._sources[source.source_id] = source

    def get_source(self, source_id: str) -> Optional[SourceRegistration]:
        return self._sources.get(source_id)

    def list_sources(self) -> List[SourceRegistration]:
        return list(self._sources.values())


source_registry = SourceRegistry()
