"""Custom exceptions used throughout the trading bot."""


class TradingBotError(Exception):
     """Base exception for the trading bot."""


class ConfigurationError(TradingBotError):
    """Raised when configuration is invalid."""


class ValidationError(TradingBotError):
    """Raised when user input is invalid."""


class OrderError(TradingBotError):
    """Raised when an order cannot be placed."""