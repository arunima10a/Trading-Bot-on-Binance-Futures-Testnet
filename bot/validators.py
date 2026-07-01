"""Input validation and exchange rule helpers"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Any

from bot.exceptions import ValidationError
from bot.logging_config import get_logger

logger = get_logger(__name__)

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


@dataclass(frozen=True)
class ValidatedOrder:
    """A fully validated, normalized order request"""

    symbol: str
    side: str
    order_type: str
    quantity: float
    price: float | None = None  # None for MARKET orders


@dataclass(frozen=True)
class SymbolFilters:
    """The subset of a symbol's exchange rules we enforce."""

    symbol: str
    step_size: float
    tick_size: float
    min_qty: float
    min_notional: float | None = None


# ── Individual field validators ─────────────────────────────────────────────

def validate_symbol(symbol: str) -> str:
    if symbol is None or not symbol.strip():
        raise ValidationError("Symbol must not be empty.")
    normalized = symbol.strip().upper()
    if not normalized.isalnum():
        raise ValidationError(
            f"Symbol '{symbol}' contains invalid characters; expected e.g. BTCUSDT."
        )
    return normalized


def validate_side(side: str) -> str:
    """Normalize BUY/SELL, case-insensitively"""
    normalized = (side or "").strip().upper()
    if normalized not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Expected one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return normalized


def validate_order_type(order_type: str) -> str:
    """Normalize MARKET/LIMIT, case-insensitively."""
    normalized = (order_type or "").strip().upper()
    if normalized not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Expected one of: "
            f"{', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return normalized


def validate_quantity(quantity: Any) -> float:
    
    try:
        value = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity '{quantity}' is not a valid number.")
    if not math.isfinite(value):
        raise ValidationError("Quantity must be a finite number.")
    if value <= 0:
        raise ValidationError("Quantity must be greater than zero.")
    return value


def validate_price(price: Any, order_type: str) -> float | None:
    """Validate the order price"""
    if order_type == "MARKET":
        if price is not None:
            logger.debug("Ignoring price for MARKET order.")
        return None

    # LIMIT from here on.
    if price is None:
        raise ValidationError("Price is required for LIMIT orders.")
    try:
        value = float(price)
    except (TypeError, ValueError):
        raise ValidationError(f"Price '{price}' is not a valid number.")
    if not math.isfinite(value) or value <= 0:
        raise ValidationError("Price must be a positive, finite number for LIMIT orders.")
    return value


def validate_order_args(
    symbol: str,
    side: str,
    order_type: str,
    quantity: Any,
    price: Any = None,
) -> ValidatedOrder:
    """Validate and normalize order input."""
    norm_type = validate_order_type(order_type)
    return ValidatedOrder(
        symbol=validate_symbol(symbol),
        side=validate_side(side),
        order_type=norm_type,
        quantity=validate_quantity(quantity),
        price=validate_price(price, norm_type),
    )


# ── Exchange-precision normalization ────────────────────────────────────────

def extract_symbol_filters(exchange_info: dict[str, Any], symbol: str) -> SymbolFilters:

    """Extract exchange filters for a trading symbol."""

    symbols = exchange_info.get("symbols", [])
    info = next((s for s in symbols if s.get("symbol") == symbol), None)
    if info is None:
        raise ValidationError(f"Symbol '{symbol}' is not available on this exchange.")

    by_type = {f.get("filterType"): f for f in info.get("filters", [])}
    lot = by_type.get("LOT_SIZE", {})
    price_filter = by_type.get("PRICE_FILTER", {})
    notional = by_type.get("MIN_NOTIONAL", {})

    return SymbolFilters(
        symbol=symbol,
        step_size=float(lot.get("stepSize", "0") or 0),
        tick_size=float(price_filter.get("tickSize", "0") or 0),
        min_qty=float(lot.get("minQty", "0") or 0),
        min_notional=(
            float(notional["notional"]) if notional.get("notional") else None
        ),
    )


def round_to_step(value: float, step: float) -> float:
    """Round value DOWN to the nearest multiple of step using exact decimals."""
    if step <= 0:
        return value
    d_value = Decimal(str(value))
    d_step = Decimal(str(step))
    steps = (d_value / d_step).to_integral_value(rounding=ROUND_DOWN)
    return float(steps * d_step)


def apply_symbol_filters(order: ValidatedOrder, filters: SymbolFilters) -> ValidatedOrder:
    """Return a new ValidatedOrder with quantity/price snapped to exchange rules."""
    adj_qty = round_to_step(order.quantity, filters.step_size)
    if adj_qty <= 0 or adj_qty < filters.min_qty:
        raise ValidationError(
            f"Quantity {order.quantity} is below the minimum {filters.min_qty} "
            f"for {filters.symbol}."
        )
    if adj_qty != order.quantity:
        logger.info(
            "Adjusted quantity %s -> %s to meet step size %s",
            order.quantity, adj_qty, filters.step_size,
        )

    adj_price = order.price
    if order.price is not None:
        adj_price = round_to_step(order.price, filters.tick_size)
        if adj_price <= 0:
            raise ValidationError(
                f"Price {order.price} is invalid after applying tick size "
                f"{filters.tick_size}."
            )
        if adj_price != order.price:
            logger.info(
                "Adjusted price %s -> %s to meet tick size %s",
                order.price, adj_price, filters.tick_size,
            )

    return dataclasses.replace(order, quantity=adj_qty, price=adj_price)