from pathlib import Path

from portfolio_risk.instruments.loader import load_instrument_registry
from portfolio_risk.instruments.models import InstrumentType
from portfolio_risk.portfolio.loader import load_portfolio_csv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_load_project_portfolio_from_instrument_master() -> None:
    instrument_path = PROJECT_ROOT / "data" / "instruments" / "instruments.csv"
    portfolio_path = PROJECT_ROOT / "data" / "portfolio" / "portfolio.csv"

    registry = load_instrument_registry(instrument_path)
    portfolio = load_portfolio_csv(portfolio_path, registry)

    assert len(registry) == 2
    assert len(portfolio) == 2

    assert portfolio.positions[0].asset_id == "PETR4"
    assert portfolio.positions[0].instrument_type == InstrumentType.EQUITY

    assert portfolio.positions[1].asset_id == "LTN_2027"
    assert portfolio.positions[1].instrument_type == InstrumentType.LTN
