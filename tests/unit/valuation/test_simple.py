import pytest

from portfolio_risk.instruments.models import Instrument, InstrumentType
from portfolio_risk.instruments.registry import InstrumentRegistry
from portfolio_risk.portfolio.models import Portfolio, Position
from portfolio_risk.valuation.simple import (
    MissingInputPriceError,
    SimpleValuationError,
    UnsupportedSimpleValuationError,
    calculate_simple_input_value,
    summarize_simple_portfolio_value,
)


def make_equity_position(
    *,
    asset_id: str = "PETR4",
    book: str = "EQUITIES",
    quantity: float = 100.0,
    input_price: float | None = 40.0,
) -> Position:
    return Position(
        asset_id=asset_id,
        instrument_type=InstrumentType.EQUITY,
        book=book,
        quantity=quantity,
        input_price=input_price,
    )


def make_equity_instrument(
    asset_id: str = "PETR4",
) -> Instrument:
    return Instrument(
        asset_id=asset_id,
        instrument_type=InstrumentType.EQUITY,
    )


def test_calculate_long_equity_value() -> None:
    value = calculate_simple_input_value(
        position=make_equity_position(
            quantity=100.0,
            input_price=40.0,
        ),
        instrument=make_equity_instrument(),
    )

    assert value == 4000.0


def test_calculate_short_equity_value() -> None:
    value = calculate_simple_input_value(
        position=make_equity_position(
            quantity=-100.0,
            input_price=40.0,
        ),
        instrument=make_equity_instrument(),
    )

    assert value == -4000.0


def test_calculate_zero_equity_value() -> None:
    value = calculate_simple_input_value(
        position=make_equity_position(
            quantity=0.0,
            input_price=40.0,
        ),
        instrument=make_equity_instrument(),
    )

    assert value == 0.0


def test_reject_missing_input_price() -> None:
    with pytest.raises(
        MissingInputPriceError,
        match="no input price",
    ):
        calculate_simple_input_value(
            position=make_equity_position(input_price=None),
            instrument=make_equity_instrument(),
        )


def test_reject_unsupported_instrument_type() -> None:
    position = Position(
        asset_id="LTN_2027",
        instrument_type=InstrumentType.LTN,
        book="RATES",
        quantity=10.0,
        input_price=900.0,
    )
    instrument = Instrument(
        asset_id="LTN_2027",
        instrument_type=InstrumentType.LTN,
    )

    with pytest.raises(
        UnsupportedSimpleValuationError,
        match="LTN",
    ):
        calculate_simple_input_value(
            position=position,
            instrument=instrument,
        )


def test_reject_asset_id_mismatch() -> None:
    with pytest.raises(
        SimpleValuationError,
        match="asset_id",
    ):
        calculate_simple_input_value(
            position=make_equity_position(asset_id="PETR4"),
            instrument=make_equity_instrument(asset_id="VALE3"),
        )


def test_reject_instrument_type_mismatch() -> None:
    position = make_equity_position()
    instrument = Instrument(
        asset_id="PETR4",
        instrument_type=InstrumentType.LTN,
    )

    with pytest.raises(
        UnsupportedSimpleValuationError,
        match="LTN",
    ):
        calculate_simple_input_value(
            position=position,
            instrument=instrument,
        )


def test_summarize_supported_and_unsupported_positions() -> None:
    registry = InstrumentRegistry()
    registry.register(make_equity_instrument())
    registry.register(
        Instrument(
            asset_id="LTN_2027",
            instrument_type=InstrumentType.LTN,
        )
    )

    portfolio = Portfolio(
        positions=(
            make_equity_position(
                quantity=100.0,
                input_price=40.0,
            ),
            Position(
                asset_id="LTN_2027",
                instrument_type=InstrumentType.LTN,
                book="RATES",
                quantity=10.0,
                input_price=900.0,
            ),
        )
    )

    summary = summarize_simple_portfolio_value(
        portfolio=portfolio,
        registry=registry,
    )

    assert summary.valued_positions == 1
    assert summary.unsupported_positions == 1
    assert summary.total_positions == 2
    assert summary.total_value == 4000.0
    assert summary.value_by_book == {"EQUITIES": 4000.0}
    assert summary.coverage_ratio == 0.5


def test_summarize_values_by_book() -> None:
    registry = InstrumentRegistry()
    registry.register(make_equity_instrument("PETR4"))
    registry.register(make_equity_instrument("VALE3"))

    portfolio = Portfolio(
        positions=(
            make_equity_position(
                asset_id="PETR4",
                book="LONG_ONLY",
                quantity=100.0,
                input_price=40.0,
            ),
            make_equity_position(
                asset_id="VALE3",
                book="LONG_ONLY",
                quantity=50.0,
                input_price=60.0,
            ),
            make_equity_position(
                asset_id="PETR4",
                book="HEDGE",
                quantity=-25.0,
                input_price=40.0,
            ),
        )
    )

    summary = summarize_simple_portfolio_value(
        portfolio=portfolio,
        registry=registry,
    )

    assert summary.total_value == 6000.0
    assert summary.value_by_book == {
        "LONG_ONLY": 7000.0,
        "HEDGE": -1000.0,
    }


def test_empty_portfolio_has_full_coverage() -> None:
    summary = summarize_simple_portfolio_value(
        portfolio=Portfolio(),
        registry=InstrumentRegistry(),
    )

    assert summary.total_positions == 0
    assert summary.valued_positions == 0
    assert summary.unsupported_positions == 0
    assert summary.total_value == 0.0
    assert summary.coverage_ratio == 1.0
