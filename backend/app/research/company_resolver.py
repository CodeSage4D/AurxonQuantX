"""AURXON Company Identity Resolution Engine.
Resolves company queries, tickers, ISINs, aliases, and historical names.
Detects corporate ambiguity (e.g. 'Tata', 'Bajaj', 'HDFC') and requests clarification.
"""

import re
from typing import Dict, List, Optional
from app.schemas.company import CompanyIdentity, CompanyResolutionResult, ListingStatus, SecurityType

# Canonical Security Master for Indian Equities
SECURITY_MASTER: List[CompanyIdentity] = [
    CompanyIdentity(
        cin="L17110MH1973PLC019786",
        isin="INE002A01018",
        legal_name="Reliance Industries Limited",
        trade_name="Reliance Industries",
        nse_symbol="RELIANCE",
        bse_code="500325",
        primary_exchange="NSE",
        listing_status=ListingStatus.ACTIVE_LISTED,
        security_type=SecurityType.EQUITY_SHARES,
        sector="Energy / Conglomerate",
        industry="Oil & Gas / Retail / Telecom",
        aliases=["RIL", "Reliance", "Jio", "Reliance Retail"],
        historical_names=["Reliance Textiles", "Reliance Commercial Corporation"],
        website_ir="https://www.ril.com/investor-relations",
        is_financial_institution=False,
    ),
    CompanyIdentity(
        cin="L22210MH1995PLC084781",
        isin="INE467B01029",
        legal_name="Tata Consultancy Services Limited",
        trade_name="TCS",
        nse_symbol="TCS",
        bse_code="532540",
        primary_exchange="NSE",
        listing_status=ListingStatus.ACTIVE_LISTED,
        security_type=SecurityType.EQUITY_SHARES,
        sector="Information Technology",
        industry="IT Services & Consulting",
        aliases=["TCS", "Tata Consultancy", "Tata CS"],
        historical_names=["Tata Computer Systems"],
        website_ir="https://www.tcs.com/investor-relations",
        is_financial_institution=False,
    ),
    CompanyIdentity(
        cin="L28920MH1945PLC004520",
        isin="INE155A01022",
        legal_name="Tata Motors Limited",
        trade_name="Tata Motors",
        nse_symbol="TATAMOTORS",
        bse_code="500570",
        primary_exchange="NSE",
        listing_status=ListingStatus.ACTIVE_LISTED,
        security_type=SecurityType.EQUITY_SHARES,
        sector="Automotive",
        industry="Commercial & Passenger Vehicles",
        aliases=["TaMo", "Tata Motors DVR", "JLR"],
        historical_names=["TELCO", "Tata Engineering and Locomotive Company"],
        website_ir="https://www.tatamotors.com/investors",
        is_financial_institution=False,
    ),
    CompanyIdentity(
        cin="L27100MH1907PLC000260",
        isin="INE081A01020",
        legal_name="Tata Steel Limited",
        trade_name="Tata Steel",
        nse_symbol="TATASTEEL",
        bse_code="500470",
        primary_exchange="NSE",
        listing_status=ListingStatus.ACTIVE_LISTED,
        security_type=SecurityType.EQUITY_SHARES,
        sector="Metals & Mining",
        industry="Iron & Steel Products",
        aliases=["Tata Steel", "Corus"],
        historical_names=["TISCO", "Tata Iron and Steel Company"],
        website_ir="https://www.tatasteel.com/investors",
        is_financial_institution=False,
    ),
    CompanyIdentity(
        cin="L85110KA1981PLC013115",
        isin="INE009A01021",
        legal_name="Infosys Limited",
        trade_name="Infosys",
        nse_symbol="INFY",
        bse_code="500209",
        primary_exchange="NSE",
        listing_status=ListingStatus.ACTIVE_LISTED,
        security_type=SecurityType.EQUITY_SHARES,
        sector="Information Technology",
        industry="IT Consulting & Software",
        aliases=["Infy", "Infosys Tech"],
        historical_names=["Infosys Technologies Limited", "Infosys Consultants Pvt Ltd"],
        website_ir="https://www.infosys.com/investors.html",
        is_financial_institution=False,
    ),
    CompanyIdentity(
        cin="L65920MH1994PLC080618",
        isin="INE040A01034",
        legal_name="HDFC Bank Limited",
        trade_name="HDFC Bank",
        nse_symbol="HDFCBANK",
        bse_code="500180",
        primary_exchange="NSE",
        listing_status=ListingStatus.ACTIVE_LISTED,
        security_type=SecurityType.EQUITY_SHARES,
        sector="Financial Services",
        industry="Private Sector Bank",
        aliases=["HDFC", "HDFC Bank", "Housing Development Finance"],
        historical_names=["HDFC Bank Limited (Merged with HDFC Ltd)"],
        website_ir="https://www.hdfcbank.com/personal/about-us/investor-relations",
        is_financial_institution=True,
    ),
    CompanyIdentity(
        cin="L65190GJ1994PLC021012",
        isin="INE090A01021",
        legal_name="ICICI Bank Limited",
        trade_name="ICICI Bank",
        nse_symbol="ICICIBANK",
        bse_code="532174",
        primary_exchange="NSE",
        listing_status=ListingStatus.ACTIVE_LISTED,
        security_type=SecurityType.EQUITY_SHARES,
        sector="Financial Services",
        industry="Private Sector Bank",
        aliases=["ICICI", "ICICI Bank"],
        historical_names=["Industrial Credit and Investment Corporation of India"],
        website_ir="https://www.icicibank.com/about-us/investor-relations",
        is_financial_institution=True,
    ),
    CompanyIdentity(
        cin="L65110MH1955GOI004169",
        isin="INE062A01020",
        legal_name="State Bank of India",
        trade_name="State Bank of India",
        nse_symbol="SBIN",
        bse_code="500112",
        primary_exchange="NSE",
        listing_status=ListingStatus.ACTIVE_LISTED,
        security_type=SecurityType.EQUITY_SHARES,
        sector="Financial Services",
        industry="Public Sector Bank",
        aliases=["SBI", "SBIN", "State Bank"],
        historical_names=["Imperial Bank of India", "Bank of Calcutta"],
        website_ir="https://sbi.co.in/web/investor-relations",
        is_financial_institution=True,
    ),
    CompanyIdentity(
        cin="L32200DL1995PLC070609",
        isin="INE397D01024",
        legal_name="Bharti Airtel Limited",
        trade_name="Bharti Airtel",
        nse_symbol="BHARTIARTL",
        bse_code="532454",
        primary_exchange="NSE",
        listing_status=ListingStatus.ACTIVE_LISTED,
        security_type=SecurityType.EQUITY_SHARES,
        sector="Telecommunications",
        industry="Telecom Services",
        aliases=["Airtel", "Bharti", "Bharti Telecom"],
        historical_names=["Bharti Tele-Ventures Limited"],
        website_ir="https://www.airtel.in/about-bharti/equity",
        is_financial_institution=False,
    ),
    CompanyIdentity(
        cin="L16005WB1910PLC001985",
        isin="INE154A01025",
        legal_name="ITC Limited",
        trade_name="ITC",
        nse_symbol="ITC",
        bse_code="500875",
        primary_exchange="NSE",
        listing_status=ListingStatus.ACTIVE_LISTED,
        security_type=SecurityType.EQUITY_SHARES,
        sector="Consumer Goods / FMCG",
        industry="Cigarettes / Hotels / Paper / Agri",
        aliases=["ITC", "Imperial Tobacco"],
        historical_names=["Imperial Tobacco Company of India Limited", "India Tobacco Company Limited"],
        website_ir="https://www.itcportal.com/investor",
        is_financial_institution=False,
    ),
    CompanyIdentity(
        cin="L99999MH1946PLC004768",
        isin="INE018A01030",
        legal_name="Larsen & Toubro Limited",
        trade_name="L&T",
        nse_symbol="LT",
        bse_code="500510",
        primary_exchange="NSE",
        listing_status=ListingStatus.ACTIVE_LISTED,
        security_type=SecurityType.EQUITY_SHARES,
        sector="Capital Goods / Construction",
        industry="Engineering, Procurement & Construction",
        aliases=["LT", "L&T", "Larsen Toubro"],
        historical_names=["Larsen & Toubro Private Limited"],
        website_ir="https://www.larsentoubro.com/investors",
        is_financial_institution=False,
    ),
    CompanyIdentity(
        cin="L65910MH1987PLC042961",
        isin="INE296A01024",
        legal_name="Bajaj Finance Limited",
        trade_name="Bajaj Finance",
        nse_symbol="BAJFINANCE",
        bse_code="500034",
        primary_exchange="NSE",
        listing_status=ListingStatus.ACTIVE_LISTED,
        security_type=SecurityType.EQUITY_SHARES,
        sector="Financial Services",
        industry="Non-Banking Financial Company (NBFC)",
        aliases=["BajFin", "Bajaj Fin", "BFL"],
        historical_names=["Bajaj Auto Finance Limited"],
        website_ir="https://www.bajajfinserv.in/finance-investor-relations",
        is_financial_institution=True,
    ),
    CompanyIdentity(
        cin="L65923PN2007PLC130075",
        isin="INE918I01026",
        legal_name="Bajaj Finserv Limited",
        trade_name="Bajaj Finserv",
        nse_symbol="BAJAJFINSV",
        bse_code="532978",
        primary_exchange="NSE",
        listing_status=ListingStatus.ACTIVE_LISTED,
        security_type=SecurityType.EQUITY_SHARES,
        sector="Financial Services",
        industry="Financial Services Holding Company",
        aliases=["Bajaj Finserv", "BFS"],
        historical_names=[],
        website_ir="https://www.bajajfinserv.in/investor-relations",
        is_financial_institution=True,
    ),
    CompanyIdentity(
        cin="L65993PN2007PLC130076",
        isin="INE917I01010",
        legal_name="Bajaj Auto Limited",
        trade_name="Bajaj Auto",
        nse_symbol="BAJAJ-AUTO",
        bse_code="532977",
        primary_exchange="NSE",
        listing_status=ListingStatus.ACTIVE_LISTED,
        security_type=SecurityType.EQUITY_SHARES,
        sector="Automotive",
        industry="2-Wheeler & 3-Wheeler Manufacturer",
        aliases=["Bajaj Auto", "Bajaj 2W"],
        historical_names=["Bachhraj Trading Corporation"],
        website_ir="https://www.bajajauto.com/investors",
        is_financial_institution=False,
    ),
]


class CompanyResolver:
    """Discovers and resolves company identifiers with strict ambiguity detection."""

    def __init__(self, master: Optional[List[CompanyIdentity]] = None):
        self._master = master or SECURITY_MASTER

    def resolve(self, query: str) -> CompanyResolutionResult:
        """Resolves a raw query string to a canonical company identity or flags ambiguity."""
        raw = query.strip()
        if not raw:
            return CompanyResolutionResult(
                query=query,
                is_resolved=False,
                is_ambiguous=False,
                ambiguity_reason="Empty search query.",
            )

        clean = re.sub(r"^(NSE:|BSE:)", "", raw, flags=re.IGNORECASE).strip()
        clean = re.sub(r"(\.NS|\.BO)$", "", clean, flags=re.IGNORECASE).strip()
        clean_upper = clean.upper()

        # 1. Exact Match on ISIN
        if re.match(r"^INE[A-Z0-9]{9}$", clean_upper):
            for c in self._master:
                if c.isin == clean_upper:
                    return CompanyResolutionResult(
                        query=query,
                        is_resolved=True,
                        is_ambiguous=False,
                        resolved_company=c,
                    )

        # 2. Exact Match on NSE Symbol
        for c in self._master:
            if c.nse_symbol and c.nse_symbol.upper() == clean_upper:
                return CompanyResolutionResult(
                    query=query,
                    is_resolved=True,
                    is_ambiguous=False,
                    resolved_company=c,
                )

        # 3. Exact Match on BSE Code
        for c in self._master:
            if c.bse_code and c.bse_code == clean_upper:
                return CompanyResolutionResult(
                    query=query,
                    is_resolved=True,
                    is_ambiguous=False,
                    resolved_company=c,
                )

        # 4. Exact Match on Trade Name or Legal Name
        for c in self._master:
            if c.trade_name.upper() == clean_upper or c.legal_name.upper() == clean_upper:
                return CompanyResolutionResult(
                    query=query,
                    is_resolved=True,
                    is_ambiguous=False,
                    resolved_company=c,
                )

        # 5. Exact Match on Aliases
        for c in self._master:
            if any(alias.upper() == clean_upper for alias in c.aliases):
                return CompanyResolutionResult(
                    query=query,
                    is_resolved=True,
                    is_ambiguous=False,
                    resolved_company=c,
                )

        # 6. Exact Match on Historical Names
        for c in self._master:
            if any(h.upper() == clean_upper for h in c.historical_names):
                return CompanyResolutionResult(
                    query=query,
                    is_resolved=True,
                    is_ambiguous=False,
                    resolved_company=c,
                )

        # 7. Ambiguity & Substring / Conglomerate Detection
        # Check if the query is a common group umbrella (e.g., "Tata", "Bajaj", "Reliance")
        matches: List[CompanyIdentity] = []
        token_lower = clean.lower()

        for c in self._master:
            all_tokens = (
                [c.legal_name.lower(), c.trade_name.lower()]
                + [a.lower() for a in c.aliases]
                + [h.lower() for h in c.historical_names]
            )
            if any(token_lower in t or t in token_lower for t in all_tokens):
                matches.append(c)

        if len(matches) == 1:
            return CompanyResolutionResult(
                query=query,
                is_resolved=True,
                is_ambiguous=False,
                resolved_company=matches[0],
            )

        if len(matches) > 1:
            candidate_list = ", ".join(f"{m.trade_name} ({m.nse_symbol})" for m in matches[:4])
            return CompanyResolutionResult(
                query=query,
                is_resolved=False,
                is_ambiguous=True,
                candidates=matches,
                ambiguity_reason=f"Multiple listed entities match '{query}'.",
                clarification_prompt=f"Found {len(matches)} matching securities: {candidate_list}. Please specify the exact entity or ticker.",
            )

        # 8. Unresolved
        return CompanyResolutionResult(
            query=query,
            is_resolved=False,
            is_ambiguous=False,
            ambiguity_reason=f"No matching listed Indian security found for '{query}'. Please verify spelling or provide NSE/BSE ticker.",
        )


company_resolver = CompanyResolver()
