from pathlib import Path

from portfolio_risk.instruments.loader import load_instrument_registry
from portfolio_risk.portfolio.loader import load_portfolio_csv
from portfolio_risk.valuation.simple import summarize_simple_portfolio_value

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_summarize_project_portfolio_simple_valuation() -> None:
    instrument_path = PROJECT_ROOT / "data" / "instruments" / "instruments.csv"
    portfolio_path = PROJECT_ROOT / "data" / "portfolio" / "portfolio.csv"

    registry = load_instrument_registry(instrument_path)
    portfolio = load_portfolio_csv(portfolio_path, registry)

    summary = summarize_simple_portfolio_value(
        portfolio=portfolio,
        registry=registry,
    )

    assert summary.total_positions == 2
    assert summary.valued_positions == 1
    assert summary.unsupported_positions == 1
    assert summary.total_value == 20000.0
    assert summary.value_by_book == {"EQUITIES": 20000.0}
    assert summary.coverage_ratio == 0.5
