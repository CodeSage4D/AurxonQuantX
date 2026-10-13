"""AURXON Indian Market Transaction Cost & Slippage Schedule.
Implements statutory Indian equity cash market cost components:
- Securities Transaction Tax (STT) under Finance Act 2004 as amended.
- Exchange Transaction Charges (NSE Equity Delivery).
- Goods and Services Tax (GST) @ 18% on eligible service components.
- Indian Stamp Duty under the Indian Stamp Act (amended July 1, 2020).
- SEBI Turnover Fees (₹10 per crore).
- Configurable broker commissions and basis-point slippage models.
"""

from enum import Enum
import math
from typing import Dict, Optional
from pydantic import BaseModel, Field


class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class TradeCostBreakdown(BaseModel):
    """Line-item audit breakdown of all statutory taxes and execution fees."""
    action: TradeAction
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
    cost_citations: Dict[str, str] = Field(default_factory=dict)


class IndianTransactionCostModel(BaseModel):
    """Configurable Indian cash equity transaction cost model with statutory defaults."""

    # Slippage (Bid-Ask spread & market impact in basis points)
    slippage_bps: float = Field(default=5.0, description="Default 5 bps (0.05%) for liquid large-caps")

    # Brokerage (Configurable discount vs full-service)
    brokerage_per_order_inr: float = Field(default=0.0, description="Flat fee per order (₹0 for zero-brokerage delivery)")
    brokerage_pct: float = Field(default=0.0, description="Variable brokerage percentage (0.0% for delivery)")

    # Statutory Indian Rates (Delivery Equity)
    stt_delivery_buy_pct: float = Field(default=0.1, description="0.1% on buy turnover (Finance Act)")
    stt_delivery_sell_pct: float = Field(default=0.1, description="0.1% on sell turnover (Finance Act)")

    # Statutory Indian Rates (Intraday Equity)
    stt_intraday_sell_pct: float = Field(default=0.025, description="0.025% on sell intraday turnover only")

    # Exchange & Regulatory Charges
    exchange_txn_charge_pct: float = Field(
        default=0.00297, description="NSE Equity delivery transaction charge (0.00297%)"
    )
    sebi_turnover_fee_pct: float = Field(
        default=0.0001, description="SEBI turnover fee: ₹10 per crore (0.0001%)"
    )
    stamp_duty_buy_pct: float = Field(
        default=0.015, description="Indian Stamp Act 2020: 0.015% on buy turnover only"
    )
    gst_rate_pct: float = Field(
        default=18.0, description="18% GST on (Brokerage + Exchange Charges + SEBI Fees)"
    )

    def calculate_trade_costs(
        self,
        action: TradeAction,
        raw_price: float,
        quantity: int,
        is_delivery: bool = True,
    ) -> TradeCostBreakdown:
        """Calculates exact statutory charges and execution cash impact for an Indian trade."""
        if quantity <= 0 or raw_price <= 0:
            raise ValueError(f"Invalid trade parameters: quantity={quantity}, price={raw_price}")

        # 1. Slippage & Execution Price
        slippage_fraction = self.slippage_bps / 10000.0
        if action == TradeAction.BUY:
            exec_price = round(raw_price * (1.0 + slippage_fraction), 4)
        else:
            exec_price = round(raw_price * (1.0 - slippage_fraction), 4)

        turnover = round(exec_price * quantity, 2)

        # 2. Brokerage
        brokerage = round(self.brokerage_per_order_inr + (turnover * (self.brokerage_pct / 100.0)), 2)

        # 3. Securities Transaction Tax (STT)
        if is_delivery:
            stt_rate = self.stt_delivery_buy_pct if action == TradeAction.BUY else self.stt_delivery_sell_pct
            stt = round(turnover * (stt_rate / 100.0), 2)
        else:
            stt = round(turnover * (self.stt_intraday_sell_pct / 100.0), 2) if action == TradeAction.SELL else 0.0

        # 4. Exchange Transaction Charges
        exchange_txn = round(turnover * (self.exchange_txn_charge_pct / 100.0), 2)

        # 5. SEBI Turnover Fee (₹10 per crore)
        sebi_fee = round(turnover * (self.sebi_turnover_fee_pct / 100.0), 4)

        # 6. Stamp Duty (Applies on BUY transactions only under Indian Stamp Act)
        stamp_duty = round(turnover * (self.stamp_duty_buy_pct / 100.0), 2) if action == TradeAction.BUY else 0.0

        # 7. GST (18% on Brokerage + Exchange Txn + SEBI Fee)
        taxable_services = brokerage + exchange_txn + sebi_fee
        gst = round(taxable_services * (self.gst_rate_pct / 100.0), 2)

        # 8. Total Costs
        total_costs = round(brokerage + stt + exchange_txn + sebi_fee + stamp_duty + gst, 2)

        # 9. Effective Net Price & Total Cash Impact
        if action == TradeAction.BUY:
            effective_net_price = round((turnover + total_costs) / quantity, 4)
            total_cash_impact = -round(turnover + total_costs, 2)
        else:
            effective_net_price = round(max(0.0, turnover - total_costs) / quantity, 4)
            total_cash_impact = round(max(0.0, turnover - total_costs), 2)

        citations = {
            "STT": "Finance Act 2004, Schedule II; 0.1% on delivery Buy & Sell",
            "Exchange_Txn": "NSE Circular NCL/CMPT/48753; ~0.00297% on equity cash turnover",
            "Stamp_Duty": "Indian Stamp (Collection of Stamp-Duty through Stock Exchanges) Rules 2019; 0.015% on Buy",
            "GST": "Central Goods and Services Tax Act 2017; 18% on brokerage and exchange services",
            "SEBI_Fee": "SEBI (Stock Brokers) Regulations, Schedule III; ₹10 per crore turnover",
        }

        return TradeCostBreakdown(
            action=action,
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
            cost_citations=citations,
        )


# Default statutory Indian market cost model instance
default_indian_cost_model = IndianTransactionCostModel()
