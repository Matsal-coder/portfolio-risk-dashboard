from dataclasses import dataclass
from pathlib import Path

from portfolio_risk.instruments.loader import load_instrument_registry
from portfolio_risk.instruments.registry import InstrumentRegistry
from portfolio_risk.market_data.curves import CurveSnapshotProvider
from portfolio_risk.market_data.models import MarketSnapshot, with_curves
from portfolio_risk.market_data.snapshot import SnapshotMarketDataProvider
from portfolio_risk.portfolio.loader import load_portfolio_csv
from portfolio_risk.portfolio.models import Portfolio
from portfolio_risk.valuation.simple import (
    PortfolioValuationSummary,
    summarize_simple_portfolio_value,
)


@dataclass(frozen=True)
class ProjectState:
    """Loaded application state used by presentation layers."""

    registry: InstrumentRegistry
    portfolio: Portfolio
    market: MarketSnapshot
    valuation: PortfolioValuationSummary


def load_project_state(
    *,
    instrument_path: str | Path,
    portfolio_path: str | Path,
    market_path: str | Path,
    curve_path: str | Path | None = None,
) -> ProjectState:
    """Load the current project state from normalized local data sources."""
    registry = load_instrument_registry(instrument_path)
    portfolio = load_portfolio_csv(
        portfolio_path,
        registry,
    )
    market = SnapshotMarketDataProvider(market_path).load()

    if curve_path is not None:
        curves = CurveSnapshotProvider(curve_path).load()
        market = with_curves(
            market,
            curves,
        )

    valuation = summarize_simple_portfolio_value(
        portfolio=portfolio,
        registry=registry,
    )

    return ProjectState(
        registry=registry,
        portfolio=portfolio,
        market=market,
        valuation=valuation,
    )
