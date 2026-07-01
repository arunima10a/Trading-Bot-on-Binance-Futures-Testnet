"""Application configuration and environment variable loading """

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

from bot.exceptions import ConfigurationError

DEFAULT_TESTNET_BASE_URL = "https://testnet.binancefuture.com"


@dataclass(frozen=True)
class Settings:
    """Application configuration"""

    api_key: str = field(repr=False)
    api_secret: str = field(repr=False)
    testnet_base_url: str = DEFAULT_TESTNET_BASE_URL
    use_testnet: bool = True


def load_settings() -> Settings:
    """Load and validate application settings"""

    load_dotenv()  
    api_key = os.getenv("BINANCE_API_KEY")
    if not api_key:
        raise ConfigurationError(
            "Missing BINANCE_API_KEY. Copy .env.example to .env and add your "
            "Binance Futures testnet API key."
        )

    api_secret = os.getenv("BINANCE_API_SECRET")
    if not api_secret:
        raise ConfigurationError(
            "Missing BINANCE_API_SECRET. Copy .env.example to .env and add your "
            "Binance Futures testnet API secret."
        )

    testnet_base_url = os.getenv("BINANCE_TESTNET_BASE_URL", DEFAULT_TESTNET_BASE_URL)

    return Settings(
        api_key=api_key,
        api_secret=api_secret,
        testnet_base_url=testnet_base_url,
    )