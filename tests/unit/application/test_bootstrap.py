from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

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
    assert state.market.curves == ()


def test_load_project_state_with_curve_snapshot(
    tmp_path: Path,
) -> None:
    instrument_path = tmp_path / "instruments.csv"
    portfolio_path = tmp_path / "portfolio.csv"
    market_path = tmp_path / "market.csv"
    curve_path = tmp_path / "curves.csv"

    instrument_path.write_text(
        ("asset_id,instrument_type\nPETR4,EQUITY\n"),
        encoding="utf-8",
    )

    portfolio_path.write_text(
        ("asset_id,instrument_type,book,quantity,price\nPETR4,EQUITY,BOOK_A,10,40.0\n"),
        encoding="utf-8",
    )

    market_path.write_text(
        ("as_of,key,value\n2026-09-30,PETR4,40.0\n"),
        encoding="utf-8",
    )

    curve_path.write_text(
        (
            "as_of,curve_key,maturity_date,zero_rate,"
            "day_count,compounding,frequency\n"
            "2026-09-30,BRL_NOMINAL,2027-09-30,0.1200,"
            "ACT/365,COMPOUNDED,1\n"
            "2026-09-30,BRL_NOMINAL,2028-09-30,0.1180,"
            "ACT/365,COMPOUNDED,1\n"
        ),
        encoding="utf-8",
    )

    state = load_project_state(
        instrument_path=instrument_path,
        portfolio_path=portfolio_path,
        market_path=market_path,
        curve_path=curve_path,
    )

    assert state.market.get("PETR4") == 40.0
    assert state.market.contains_curve("BRL_NOMINAL")

    curve = state.market.get_curve("BRL_NOMINAL")

    assert curve.as_of == date(2026, 9, 30)
    assert len(curve.nodes) == 2
    assert curve.nodes[0].zero_rate == pytest.approx(0.12)


def test_load_project_state_rejects_curve_snapshot_with_different_as_of(
    tmp_path: Path,
) -> None:
    instrument_path = tmp_path / "instruments.csv"
    portfolio_path = tmp_path / "portfolio.csv"
    market_path = tmp_path / "market.csv"
    curve_path = tmp_path / "curves.csv"

    instrument_path.write_text(
        ("asset_id,instrument_type\nPETR4,EQUITY\n"),
        encoding="utf-8",
    )

    portfolio_path.write_text(
        ("asset_id,instrument_type,book,quantity,price\nPETR4,EQUITY,BOOK_A,10,40.0\n"),
        encoding="utf-8",
    )

    market_path.write_text(
        ("as_of,key,value\n2026-09-30,PETR4,40.0\n"),
        encoding="utf-8",
    )

    curve_path.write_text(
        (
            "as_of,curve_key,maturity_date,zero_rate,"
            "day_count,compounding,frequency\n"
            "2026-10-01,BRL_NOMINAL,2027-10-01,0.1200,"
            "ACT/365,COMPOUNDED,1\n"
            "2026-10-01,BRL_NOMINAL,2028-10-01,0.1180,"
            "ACT/365,COMPOUNDED,1\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValidationError,
        match="must share the market snapshot as-of date",
    ):
        load_project_state(
            instrument_path=instrument_path,
            portfolio_path=portfolio_path,
            market_path=market_path,
            curve_path=curve_path,
        )
