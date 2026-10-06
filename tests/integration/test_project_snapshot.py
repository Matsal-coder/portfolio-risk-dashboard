from pathlib import Path

from portfolio_risk.instruments.loader import load_instrument_registry
from portfolio_risk.market_data.curves import CurveSnapshotProvider
from portfolio_risk.market_data.models import with_curves
from portfolio_risk.market_data.snapshot import SnapshotMarketDataProvider
from portfolio_risk.portfolio.loader import load_portfolio_csv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_load_project_portfolio_and_market_snapshot() -> None:
    instrument_path = PROJECT_ROOT / "data" / "instruments" / "instruments.csv"
    portfolio_path = PROJECT_ROOT / "data" / "portfolio" / "portfolio.csv"
    market_path = PROJECT_ROOT / "data" / "market" / "market_snapshot.csv"

    registry = load_instrument_registry(instrument_path)
    portfolio = load_portfolio_csv(portfolio_path, registry)
    market = SnapshotMarketDataProvider(market_path).load()

    assert len(registry) == 2
    assert len(portfolio) == 2

    assert market.as_of.isoformat() == "2026-09-30"
    assert market.get("PETR4") == 40.0
    assert market.get("USD_BRL") == 5.30


def test_load_project_curve_snapshot() -> None:
    market_path = PROJECT_ROOT / "data" / "market" / "market_snapshot.csv"
    curve_path = PROJECT_ROOT / "data" / "market" / "curve_snapshot.csv"

    market = SnapshotMarketDataProvider(market_path).load()
    curves = CurveSnapshotProvider(curve_path).load()

    market = with_curves(
        market,
        curves,
    )

    curve = market.get_curve("BRL_NOMINAL")

    assert curve.as_of.isoformat() == "2026-09-30"
    assert len(curve.nodes) == 5
    assert curve.nodes[0].zero_rate == 0.12
