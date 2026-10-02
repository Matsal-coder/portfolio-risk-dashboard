from pathlib import Path

import pytest

from portfolio_risk.instruments.models import Instrument, InstrumentType
from portfolio_risk.instruments.registry import InstrumentRegistry
from portfolio_risk.portfolio.loader import (
    InstrumentTypeMismatchError,
    PortfolioRowError,
    PortfolioSchemaError,
    load_portfolio_csv,
)


@pytest.fixture
def registry() -> InstrumentRegistry:
    instrument_registry = InstrumentRegistry()

    instrument_registry.register(
        Instrument(
            asset_id="PETR4",
            instrument_type=InstrumentType.EQUITY,
        )
    )
    instrument_registry.register(
        Instrument(
            asset_id="LTN_2027",
            instrument_type=InstrumentType.LTN,
        )
    )

    return instrument_registry


def write_csv(
    tmp_path: Path,
    content: str,
) -> Path:
    path = tmp_path / "portfolio.csv"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_valid_portfolio(
    tmp_path: Path,
    registry: InstrumentRegistry,
) -> None:
    path = write_csv(
        tmp_path,
        (
            "asset_id,instrument_type,book,quantity,price\n"
            "PETR4,EQUITY,EQUITIES,100,40.5\n"
            "LTN_2027,LTN,RATES,10,900\n"
        ),
    )

    portfolio = load_portfolio_csv(path, registry)

    assert len(portfolio) == 2
    assert portfolio.positions[0].asset_id == "PETR4"
    assert portfolio.positions[0].input_price == 40.5


def test_load_long_short_and_zero_positions(
    tmp_path: Path,
    registry: InstrumentRegistry,
) -> None:
    path = write_csv(
        tmp_path,
        (
            "asset_id,instrument_type,book,quantity,price\n"
            "PETR4,EQUITY,LONG,100,40\n"
            "PETR4,EQUITY,SHORT,-50,40\n"
            "PETR4,EQUITY,ZERO,0,40\n"
        ),
    )

    portfolio = load_portfolio_csv(path, registry)

    assert [position.quantity for position in portfolio.positions] == [
        100.0,
        -50.0,
        0.0,
    ]


def test_blank_price_becomes_none(
    tmp_path: Path,
    registry: InstrumentRegistry,
) -> None:
    path = write_csv(
        tmp_path,
        ("asset_id,instrument_type,book,quantity,price\nPETR4,EQUITY,EQUITIES,100,\n"),
    )

    portfolio = load_portfolio_csv(path, registry)

    assert portfolio.positions[0].input_price is None


def test_reject_missing_column(
    tmp_path: Path,
    registry: InstrumentRegistry,
) -> None:
    path = write_csv(
        tmp_path,
        ("asset_id,instrument_type,book,quantity\nPETR4,EQUITY,EQUITIES,100\n"),
    )

    with pytest.raises(
        PortfolioSchemaError,
        match="missing columns",
    ):
        load_portfolio_csv(path, registry)


def test_reject_extra_column(
    tmp_path: Path,
    registry: InstrumentRegistry,
) -> None:
    path = write_csv(
        tmp_path,
        (
            "asset_id,instrument_type,book,quantity,price,issuer\n"
            "PETR4,EQUITY,EQUITIES,100,40,Example\n"
        ),
    )

    with pytest.raises(
        PortfolioSchemaError,
        match="unexpected columns",
    ):
        load_portfolio_csv(path, registry)


def test_reject_invalid_quantity(
    tmp_path: Path,
    registry: InstrumentRegistry,
) -> None:
    path = write_csv(
        tmp_path,
        (
            "asset_id,instrument_type,book,quantity,price\n"
            "PETR4,EQUITY,EQUITIES,INVALID,40\n"
        ),
    )

    with pytest.raises(
        PortfolioRowError,
        match="row 2",
    ):
        load_portfolio_csv(path, registry)


def test_reject_negative_price(
    tmp_path: Path,
    registry: InstrumentRegistry,
) -> None:
    path = write_csv(
        tmp_path,
        (
            "asset_id,instrument_type,book,quantity,price\n"
            "PETR4,EQUITY,EQUITIES,100,-1\n"
        ),
    )

    with pytest.raises(
        PortfolioRowError,
        match="row 2",
    ):
        load_portfolio_csv(path, registry)


def test_reject_invalid_instrument_type(
    tmp_path: Path,
    registry: InstrumentRegistry,
) -> None:
    path = write_csv(
        tmp_path,
        (
            "asset_id,instrument_type,book,quantity,price\n"
            "PETR4,INVALID,EQUITIES,100,40\n"
        ),
    )

    with pytest.raises(
        PortfolioRowError,
        match="row 2",
    ):
        load_portfolio_csv(path, registry)


def test_reject_unknown_asset_id(
    tmp_path: Path,
    registry: InstrumentRegistry,
) -> None:
    path = write_csv(
        tmp_path,
        (
            "asset_id,instrument_type,book,quantity,price\n"
            "UNKNOWN,EQUITY,EQUITIES,100,40\n"
        ),
    )

    with pytest.raises(
        PortfolioRowError,
        match="UNKNOWN",
    ):
        load_portfolio_csv(path, registry)


def test_reject_instrument_type_mismatch(
    tmp_path: Path,
    registry: InstrumentRegistry,
) -> None:
    path = write_csv(
        tmp_path,
        ("asset_id,instrument_type,book,quantity,price\nPETR4,LTN,EQUITIES,100,40\n"),
    )

    with pytest.raises(
        InstrumentTypeMismatchError,
        match="PETR4",
    ):
        load_portfolio_csv(path, registry)


def test_reject_empty_book(
    tmp_path: Path,
    registry: InstrumentRegistry,
) -> None:
    path = write_csv(
        tmp_path,
        ("asset_id,instrument_type,book,quantity,price\nPETR4,EQUITY,,100,40\n"),
    )

    with pytest.raises(
        PortfolioRowError,
        match="row 2",
    ):
        load_portfolio_csv(path, registry)


def test_reject_csv_with_headers_only(
    tmp_path: Path,
    registry: InstrumentRegistry,
) -> None:
    path = write_csv(
        tmp_path,
        "asset_id,instrument_type,book,quantity,price\n",
    )

    with pytest.raises(
        PortfolioSchemaError,
        match="contains no positions",
    ):
        load_portfolio_csv(path, registry)


def test_reject_completely_empty_file(
    tmp_path: Path,
    registry: InstrumentRegistry,
) -> None:
    path = write_csv(tmp_path, "")

    with pytest.raises(
        PortfolioSchemaError,
        match="Could not load portfolio CSV",
    ):
        load_portfolio_csv(path, registry)


def test_reject_missing_file(
    tmp_path: Path,
    registry: InstrumentRegistry,
) -> None:
    path = tmp_path / "does-not-exist.csv"

    with pytest.raises(
        PortfolioSchemaError,
        match="Could not load portfolio CSV",
    ):
        load_portfolio_csv(path, registry)
