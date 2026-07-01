"""Order processing service"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bot.client import BinanceFuturesClient
from bot.exceptions import OrderError, ValidationError
from bot.logging_config import get_logger
from bot.validators import (
    ValidatedOrder,
    apply_symbol_filters,
    extract_symbol_filters,
    validate_order_args,
)

logger = get_logger(__name__)


@dataclass(frozen=True)
class OrderResult:
    """The outcome of a placement, ready for the CLI to display"""

    order: ValidatedOrder          
    response: dict[str, Any]       
    summary: str                   
    details: str                   


class OrderService:
    """Coordinates validation, precision, placement, and formatting."""

    def __init__(self, client: BinanceFuturesClient) -> None:
        self._client = client

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Any,
        price: Any = None,
    ) -> OrderResult:
        
        """Validate and place an order"""

        # Validate user input
        order = validate_order_args(symbol, side, order_type, quantity, price)

        # Apply exchange precision rules
        exchange_info = self._client.get_exchange_info()
        filters = extract_symbol_filters(exchange_info, order.symbol)
        order = apply_symbol_filters(order, filters)

        # Log the request
        summary = self._build_summary(order)
        logger.info("Order request summary:\n%s", summary)

       # Place the order
        response = self._client.create_order(
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price,
        )

       
        details = self._format_response(response)
        logger.info("Order response details:\n%s", details)

        return OrderResult(
            order=order, response=response, summary=summary, details=details
        )

    @staticmethod
    def _build_summary(order: ValidatedOrder) -> str:
        """Format the order summary"""
        lines = [
            "──────── ORDER REQUEST ────────",
            f"  Symbol     : {order.symbol}",
            f"  Side       : {order.side}",
            f"  Type       : {order.order_type}",
            f"  Quantity   : {order.quantity}",
        ]
        if order.price is not None:
            lines.append(f"  Price      : {order.price}")
        lines.append("───────────────────────────────")
        return "\n".join(lines)

    @staticmethod
    def _format_response(response: dict[str, Any]) -> str:
        """Format the exchange response """
        order_id = response.get("orderId", "n/a")
        status = response.get("status", "n/a")
        executed_qty = response.get("executedQty", "0")
        orig_qty = response.get("origQty", "n/a")

        # avgPrice is "0"/"0.00000" for an unfilled (resting) order → show n/a.
        raw_avg = response.get("avgPrice", "0")
        try:
            avg_price = raw_avg if float(raw_avg) > 0 else "n/a"
        except (TypeError, ValueError):
            avg_price = "n/a"

        lines = [
            "──────── ORDER RESPONSE ───────",
            f"  Order ID     : {order_id}",
            f"  Status       : {status}",
            f"  Orig Qty     : {orig_qty}",
            f"  Executed Qty : {executed_qty}",
            f"  Avg Price    : {avg_price}",
            "───────────────────────────────",
        ]
        return "\n".join(lines)