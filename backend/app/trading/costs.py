"""AURXON Indian Market Transaction Cost & Slippage Schedule.
Implements statutory Indian financial market transaction cost components:
- Securities Transaction Tax (STT) under Finance Act 2004 as amended by Finance (No. 2) Act 2024.
- Exchange Transaction Charges (NSE Equity Delivery, Intraday, ETF, and F&O circulars).
- Goods and Services Tax (GST) @ 18% on eligible service components.
- Indian Stamp Duty under the Indian Stamp Act (amended July 1, 2020).
- SEBI Turnover Fees (₹10 per crore).
- Configurable broker commissions and basis-point slippage models.
- Strict classification of supported vs unsupported instruments and rate versioning.
"""

from enum import Enum
import math
from typing import Dict, Optional
from pydantic import BaseModel, Field


class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class InstrumentType(str, Enum):
    """Classification of Indian financial instruments with specific statutory tax schedules."""
    EQUITY_DELIVERY = "EQUITY_DELIVERY"      # Supported & Statutorily Verified
    EQUITY_INTRADAY = "EQUITY_INTRADAY"      # Supported & Statutorily Verified
    EQUITY_ETF = "EQUITY_ETF"                # Supported & Statutorily Verified (Exempt buy STT, reduced stamp)
    EQUITY_FUTURES = "EQUITY_FUTURES"        # Supported for simulation reference (Oct 2024 rates)
    EQUITY_OPTIONS = "EQUITY_OPTIONS"        # Supported for simulation reference (Oct 2024 rates)
    COMMODITY = "COMMODITY"                  # Unsupported in cash simulation engine
    CURRENCY = "CURRENCY"                    # Unsupported in cash simulation engine


class TradeCostBreakdown(BaseModel):
    """Line-item audit breakdown of all statutory taxes and execution fees."""
    action: TradeAction
    instrument_type: InstrumentType
    quantity: int
    raw_price: float
    slippage_bps: float
    execution_price_with_slippage: float
    turnover_gross: float

    # Statutory Taxes & Levies (INR)
    brokerage: float
    stt: float  # Securities Transaction Tax
    exchange_txn_charge: float
    sebi_turnover_fee: float
    stamp_duty: float
    gst: float  # 18% on Brokerage + Exchange Txn + SEBI Fee

    total_costs: float
    effective_net_price: float
    total_cash_impact: float  # Negative for buy (outflow), positive for sell (inflow)
    schedule_version: str
    rates_effective_date: str
    cost_citations: Dict[str, str] = Field(default_factory=dict)


class IndianTransactionCostModel(BaseModel):
    """Configurable, versioned Indian transaction cost model with statutory defaults."""

    schedule_version: str = Field(default="2024.2-STATUTORY", description="Statutory schedule version identifier")
    rates_effective_date: str = Field(default="2024-10-01", description="Effective date of active statutory rate schedule")

    # Slippage (Bid-Ask spread & market impact in basis points)
    slippage_bps: float = Field(default=5.0, description="Default 5 bps (0.05%) for liquid large-caps")

    # Brokerage (Configurable discount vs full-service)
    brokerage_per_order_inr: float = Field(default=0.0, description="Flat fee per order (₹0 for zero-brokerage delivery)")
    brokerage_pct: float = Field(default=0.0, description="Variable brokerage percentage (0.0% for delivery)")

    # 1. Statutory Indian Rates (Equity Delivery)
    stt_delivery_buy_pct: float = Field(default=0.1, description="0.1% on buy delivery turnover (Finance Act 2004)")
    stt_delivery_sell_pct: float = Field(default=0.1, description="0.1% on sell delivery turnover (Finance Act 2004)")
    stamp_duty_delivery_buy_pct: float = Field(default=0.015, description="0.015% on buy delivery turnover (Stamp Act 2020)")

    # 2. Statutory Indian Rates (Equity Intraday)
    stt_intraday_sell_pct: float = Field(default=0.025, description="0.025% on sell intraday turnover only (Finance Act 2016)")
    stamp_duty_intraday_buy_pct: float = Field(default=0.003, description="0.003% on buy intraday turnover (Stamp Act 2020)")

    # 3. Statutory Indian Rates (Equity ETFs)
    stt_etf_buy_pct: float = Field(default=0.0, description="0.0% on buy ETF units on exchange (Finance Act 2019 / CBDT)")
    stt_etf_sell_pct: float = Field(default=0.001, description="0.001% on sell ETF units on exchange (Finance Act 2019 / CBDT)")
    stamp_duty_etf_buy_pct: float = Field(default=0.005, description="0.005% on buy ETF units on exchange (Stamp Act 2020)")

    # 4. Reference Rates (Equity Futures & Options - Simulation Reference)
    stt_futures_sell_pct: float = Field(default=0.02, description="0.02% on sell futures turnover (Finance (No. 2) Act 2024, effective Oct 1, 2024)")
    stamp_duty_futures_buy_pct: float = Field(default=0.002, description="0.002% on buy futures turnover (Stamp Act 2020)")
    exchange_txn_futures_pct: float = Field(default=0.00173, description="0.00173% NSE futures transaction charge (NSE Circular Oct 2024)")

    stt_options_sell_pct: float = Field(default=0.1, description="0.1% on sell options premium (Finance (No. 2) Act 2024, effective Oct 1, 2024)")
    stamp_duty_options_buy_pct: float = Field(default=0.003, description="0.003% on buy options premium (Stamp Act 2020)")
    exchange_txn_options_pct: float = Field(default=0.03503, description="0.03503% NSE options premium transaction charge (NSE Circular Oct 2024)")

    # 5. Common Exchange & Regulatory Charges (Cash)
    exchange_txn_charge_pct: float = Field(
        default=0.00297, description="NSE Equity delivery/intraday transaction charge: 0.00297% (NSE Circular Oct 2024)"
    )
    sebi_turnover_fee_pct: float = Field(
        default=0.0001, description="SEBI turnover fee: ₹10 per crore (0.0001%) across cash and derivatives"
    )
    gst_rate_pct: float = Field(
        default=18.0, description="18% GST on (Brokerage + Exchange Charges + SEBI Fees)"
    )

    def calculate_trade_costs(
        self,
        action: TradeAction,
        raw_price: float,
        quantity: int,
        instrument_type: InstrumentType = InstrumentType.EQUITY_DELIVERY,
        is_delivery: Optional[bool] = None,
    ) -> TradeCostBreakdown:
        """Calculates exact statutory charges and execution cash impact for an Indian trade."""
        if quantity <= 0 or raw_price <= 0:
            raise ValueError(f"Invalid trade parameters: quantity={quantity}, price={raw_price}")

        # Backward compatibility for boolean is_delivery flag
        if is_delivery is not None:
            instrument_type = InstrumentType.EQUITY_DELIVERY if is_delivery else InstrumentType.EQUITY_INTRADAY

        # Explicit rejection of unsupported asset classes
        if instrument_type in [InstrumentType.COMMODITY, InstrumentType.CURRENCY]:
            raise ValueError(
                f"Statutory cost schedule for '{instrument_type.value}' is UNSUPPORTED. "
                "Current engine is strictly validated for Indian Cash Equities, Intraday, and ETFs."
            )

        # 1. Slippage & Execution Price
        slippage_fraction = self.slippage_bps / 10000.0
        if action == TradeAction.BUY:
            exec_price = round(raw_price * (1.0 + slippage_fraction), 4)
        else:
            exec_price = round(raw_price * (1.0 - slippage_fraction), 4)

        turnover = round(exec_price * quantity, 2)

        # 2. Brokerage
        brokerage = round(self.brokerage_per_order_inr + (turnover * (self.brokerage_pct / 100.0)), 2)

        # 3. Instrument-Specific Statutory Taxes
        if instrument_type == InstrumentType.EQUITY_DELIVERY:
            stt_rate = self.stt_delivery_buy_pct if action == TradeAction.BUY else self.stt_delivery_sell_pct
            stt = round(turnover * (stt_rate / 100.0), 2)
            stamp_duty = round(turnover * (self.stamp_duty_delivery_buy_pct / 100.0), 2) if action == TradeAction.BUY else 0.0
            exchange_txn = round(turnover * (self.exchange_txn_charge_pct / 100.0), 2)

        elif instrument_type == InstrumentType.EQUITY_INTRADAY:
            stt = round(turnover * (self.stt_intraday_sell_pct / 100.0), 2) if action == TradeAction.SELL else 0.0
            stamp_duty = round(turnover * (self.stamp_duty_intraday_buy_pct / 100.0), 2) if action == TradeAction.BUY else 0.0
            exchange_txn = round(turnover * (self.exchange_txn_charge_pct / 100.0), 2)

        elif instrument_type == InstrumentType.EQUITY_ETF:
            stt_rate = self.stt_etf_buy_pct if action == TradeAction.BUY else self.stt_etf_sell_pct
            stt = round(turnover * (stt_rate / 100.0), 2)
            stamp_duty = round(turnover * (self.stamp_duty_etf_buy_pct / 100.0), 2) if action == TradeAction.BUY else 0.0
            exchange_txn = round(turnover * (self.exchange_txn_charge_pct / 100.0), 2)

        elif instrument_type == InstrumentType.EQUITY_FUTURES:
            stt = round(turnover * (self.stt_futures_sell_pct / 100.0), 2) if action == TradeAction.SELL else 0.0
            stamp_duty = round(turnover * (self.stamp_duty_futures_buy_pct / 100.0), 2) if action == TradeAction.BUY else 0.0
            exchange_txn = round(turnover * (self.exchange_txn_futures_pct / 100.0), 2)

        elif instrument_type == InstrumentType.EQUITY_OPTIONS:
            stt = round(turnover * (self.stt_options_sell_pct / 100.0), 2) if action == TradeAction.SELL else 0.0
            stamp_duty = round(turnover * (self.stamp_duty_options_buy_pct / 100.0), 2) if action == TradeAction.BUY else 0.0
            exchange_txn = round(turnover * (self.exchange_txn_options_pct / 100.0), 2)

        else:
            raise ValueError(f"Unrecognized instrument type: {instrument_type}")

        # 4. SEBI Turnover Fee (₹10 per crore across all categories)
        sebi_fee = round(turnover * (self.sebi_turnover_fee_pct / 100.0), 4)

        # 5. GST (18% on Brokerage + Exchange Txn + SEBI Fee)
        taxable_services = brokerage + exchange_txn + sebi_fee
        gst = round(taxable_services * (self.gst_rate_pct / 100.0), 2)

        # 6. Total Costs
        total_costs = round(brokerage + stt + exchange_txn + sebi_fee + stamp_duty + gst, 2)

        # 7. Effective Net Price & Total Cash Impact
        if action == TradeAction.BUY:
            effective_net_price = round((turnover + total_costs) / quantity, 4)
            total_cash_impact = -round(turnover + total_costs, 2)
        else:
            effective_net_price = round(max(0.0, turnover - total_costs) / quantity, 4)
            total_cash_impact = round(max(0.0, turnover - total_costs), 2)

        citations = {
            "STT": f"Finance Act 2004 / Finance (No. 2) Act 2024; {instrument_type.value} rate applied; Effective {self.rates_effective_date}",
            "Exchange_Txn": f"NSE Circular NSE/CMTR/63897 (Unified Member Charges); Effective {self.rates_effective_date}",
            "Stamp_Duty": "Indian Stamp (Collection of Stamp-Duty through Stock Exchanges) Rules 2019; Effective 2020-07-01; Buy Only",
            "GST": "Central Goods and Services Tax Act 2017; 18% on brokerage, exchange, and SEBI fee services",
            "SEBI_Fee": "SEBI (Stock Brokers) Regulations, Schedule III; ₹10 per crore turnover",
        }

        return TradeCostBreakdown(
            action=action,
            instrument_type=instrument_type,
            quantity=quantity,
            raw_price=raw_price,
            slippage_bps=self.slippage_bps,
            execution_price_with_slippage=exec_price,
            turnover_gross=turnover,
            brokerage=brokerage,
            stt=stt,
            exchange_txn_charge=exchange_txn,
            sebi_turnover_fee=sebi_fee,
            stamp_duty=stamp_duty,
            gst=gst,
            total_costs=total_costs,
            effective_net_price=effective_net_price,
            total_cash_impact=total_cash_impact,
            schedule_version=self.schedule_version,
            rates_effective_date=self.rates_effective_date,
            cost_citations=citations,
        )


# Default statutory Indian market cost model instance
default_indian_cost_model = IndianTransactionCostModel()
