"""CLI entry point for the Binance Futures trading bot"""

from __future__ import annotations

import argparse
import logging
import sys

from bot.client import BinanceFuturesClient
from bot.config import load_settings
from bot.exceptions import TradingBotError
from bot.logging_config import configure_logging, get_logger
from bot.orders import OrderService

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Define and return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Place MARKET and LIMIT orders on the Binance Futures (USDT-M) testnet.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--symbol", required=True,
        help="Trading pair, e.g. BTCUSDT.",
    )
    parser.add_argument(
        "--side", required=True,
        choices=["BUY", "SELL", "buy", "sell"],
        help="Order side.",
    )
    parser.add_argument(
        "--type", dest="order_type", required=True,
        choices=["MARKET", "LIMIT", "market", "limit"],
        help="Order type.",
    )
    parser.add_argument(
        "--quantity", required=True, type=float,
        help="Order quantity in the base asset (e.g. 0.002 BTC).",
    )
    parser.add_argument(
        "--price", type=float, default=None,
        help="Limit price. Required for LIMIT orders; ignored for MARKET.",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show DEBUG-level detail (full request/response) on the console.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entry point. Returns a process exit code (0 = success)"""
    args = build_parser().parse_args(argv)

    console_level = logging.DEBUG if args.verbose else logging.INFO
    configure_logging(console_level=console_level)

    try:
         # Initialize application components
        settings = load_settings()
        client = BinanceFuturesClient(settings)
        service = OrderService(client)

       
        result = service.place_order(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )

        print(result.summary)
        print(result.details)
        print("\n✅ SUCCESS: order placed.")
        return 0

    except TradingBotError as exc:
        # Handle expected application errors
        logger.error("Order failed: %s", exc)
        print(f"\n❌ FAILURE: {exc}", file=sys.stderr)
        return 1

    except Exception as exc:  # noqa: BLE001 
        # Catch unexpected errors and log the traceback.
        logger.exception("Unexpected error: %s", exc)
        print(
            "\n❌ UNEXPECTED ERROR: something went wrong. See logs/trading_bot.log.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())