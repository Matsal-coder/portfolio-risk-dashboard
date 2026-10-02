from typing import Protocol

from portfolio_risk.market_data.models import MarketSnapshot


class MarketDataProvider(Protocol):
    """Contract for market data providers."""

    def load(self) -> MarketSnapshot:
        """Load and return a normalized market snapshot."""
        ...
