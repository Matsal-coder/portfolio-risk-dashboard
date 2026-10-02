from pathlib import Path

from portfolio_risk.application.bootstrap import load_project_state
from portfolio_risk.instruments.models import InstrumentType


def test_load_project_state_from_local_files(
    tmp_path: Path,
) -> None:
    instrument_path = tmp_path / "instruments.csv"
    portfolio_path = tmp_path / "portfolio.csv"
    market_path = tmp_path / "market.csv"

    instrument_path.write_text(
        ("asset_id,instrument_type\nPETR4,EQUITY\nLTN_2027,LTN\n"),
        encoding="utf-8",
    )

    portfolio_path.write_text(
        (
            "asset_id,instrument_type,book,quantity,price\n"
            "PETR4,EQUITY,EQUITIES,500,40\n"
            "LTN_2027,LTN,RATES,10,900\n"
        ),
        encoding="utf-8",
    )

    market_path.write_text(
        ("as_of,key,value\n2026-09-30,PETR4,40\n2026-09-30,USD_BRL,5.30\n"),
        encoding="utf-8",
    )

    state = load_project_state(
        instrument_path=instrument_path,
        portfolio_path=portfolio_path,
        market_path=market_path,
    )

    assert len(state.registry) == 2
    assert len(state.portfolio) == 2

    assert state.registry.get("PETR4").instrument_type == InstrumentType.EQUITY

    assert state.market.get("PETR4") == 40.0
    assert state.market.get("USD_BRL") == 5.30

    assert state.valuation.total_positions == 2
    assert state.valuation.valued_positions == 1
    assert state.valuation.unsupported_positions == 1
    assert state.valuation.total_value == 20000.0
    assert state.valuation.coverage_ratio == 0.5
