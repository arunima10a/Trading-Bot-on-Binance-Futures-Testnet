"""Binance Futures client wrapper"""

from __future__ import annotations

from typing import Any

from binance import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from requests.exceptions import RequestException

from bot.config import Settings
from bot.exceptions import OrderError
from bot.logging_config import get_logger

logger = get_logger(__name__)


class BinanceFuturesClient:
    """Client for interacting with Binance futures """

    def __init__(self, settings: Settings) -> None:
        """Initialize the Binance Futures client"""

        self._settings = settings
        self._client = Client(
            api_key=settings.api_key,
            api_secret=settings.api_secret,
            testnet=settings.use_testnet,
        )
        logger.info(
            "Initialized Binance Futures client (testnet=%s)", settings.use_testnet
        )

    def get_balance(self) -> list[dict[str, Any]]:
        """Return futures account balances"""

        try:
            balances = self._client.futures_account_balance()
        except (BinanceAPIException, BinanceOrderException) as exc:
            logger.error("API error fetching balance: %s", exc)
            raise OrderError(f"Failed to fetch account balance: {exc}") from exc
        except RequestException as exc:
            logger.error("Network error fetching balance: %s", exc)
            raise OrderError(f"Network error fetching account balance: {exc}") from exc

        logger.debug("futures_account_balance response: %s", balances)
        return balances
    
    def get_exchange_info(self) -> dict[str, Any]:

        """Return exchange information"""

        try:
            info = self._client.futures_exchange_info()
        except (BinanceAPIException, BinanceOrderException) as exc:
            logger.error("API error fetching exchange info: %s", exc)
            raise OrderError(f"Failed to fetch exchange info: {exc}") from exc
        except RequestException as exc:
            logger.error("Network error fetching exchange info: %s", exc)
            raise OrderError(f"Network error fetching exchange info: {exc}") from exc

        logger.debug(
            "futures_exchange_info returned %d symbols",
            len(info.get("symbols", [])),
        )
        return info

    def create_order(
        self,
        *,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        time_in_force: str = "GTC",
    ) -> dict[str, Any]:
        
        """Place a futures order.""" 

        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }
        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force

        logger.info(
            "Placing order: %s %s %s qty=%s%s",
            side,
            order_type,
            symbol,
            quantity,
            f" price={price}" if price is not None else "",
        )
        logger.debug("futures_create_order request params: %s", params)

        try:
            response = self._client.futures_create_order(**params)
        except (BinanceAPIException, BinanceOrderException) as exc:
            logger.error("API error placing order: %s", exc)
            raise OrderError(f"Exchange rejected the order: {exc}") from exc
        except RequestException as exc:
            logger.error("Network error placing order: %s", exc)
            raise OrderError(f"Network error while placing order: {exc}") from exc

        logger.info(
            "Order accepted: orderId=%s status=%s",
            response.get("orderId"),
            response.get("status"),
        )
        logger.debug("futures_create_order response: %s", response)
        return response