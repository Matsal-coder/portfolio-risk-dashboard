import pytest
from pydantic import ValidationError

from portfolio_risk.instruments.models import InstrumentType
from portfolio_risk.portfolio.models import Portfolio, Position


def make_position(
    *,
    asset_id: str = "PETR4",
    instrument_type: InstrumentType = InstrumentType.EQUITY,
    book: str = "EQUITIES",
    quantity: float = 100.0,
    input_price: float | None = 40.0,
) -> Position:
    return Position(
        asset_id=asset_id,
        instrument_type=instrument_type,
        book=book,
        quantity=quantity,
        input_price=input_price,
    )


def test_create_long_position() -> None:
    position = make_position(quantity=100.0)

    assert position.quantity == 100.0


def test_create_short_position() -> None:
    position = make_position(quantity=-100.0)

    assert position.quantity == -100.0


def test_create_zero_position() -> None:
    position = make_position(quantity=0.0)

    assert position.quantity == 0.0


def test_position_can_have_no_input_price() -> None:
    position = make_position(input_price=None)

    assert position.input_price is None


def test_reject_negative_input_price() -> None:
    with pytest.raises(ValidationError):
        make_position(input_price=-1.0)


def test_reject_empty_asset_id() -> None:
    with pytest.raises(ValidationError):
        make_position(asset_id="")


def test_reject_empty_book() -> None:
    with pytest.raises(ValidationError):
        make_position(book="")


def test_position_is_immutable() -> None:
    position = make_position()

    with pytest.raises(ValidationError):
        position.quantity = 200.0


def test_create_empty_portfolio() -> None:
    portfolio = Portfolio()

    assert len(portfolio) == 0
    assert portfolio.positions == ()


def test_portfolio_accepts_multiple_positions() -> None:
    positions = (
        make_position(asset_id="PETR4"),
        make_position(asset_id="VALE3"),
    )

    portfolio = Portfolio(positions=positions)

    assert len(portfolio) == 2


def test_return_portfolio_books() -> None:
    portfolio = Portfolio(
        positions=(
            make_position(asset_id="PETR4", book="EQUITIES"),
            make_position(
                asset_id="LTN_2027",
                instrument_type=InstrumentType.LTN,
                book="RATES",
            ),
        )
    )

    assert portfolio.books() == {"EQUITIES", "RATES"}


def test_return_portfolio_instrument_types() -> None:
    portfolio = Portfolio(
        positions=(
            make_position(
                asset_id="PETR4",
                instrument_type=InstrumentType.EQUITY,
            ),
            make_position(
                asset_id="LTN_2027",
                instrument_type=InstrumentType.LTN,
                book="RATES",
            ),
        )
    )

    assert portfolio.instrument_types() == {
        InstrumentType.EQUITY,
        InstrumentType.LTN,
    }


def test_group_positions_by_book() -> None:
    petr4 = make_position(asset_id="PETR4", book="EQUITIES")
    vale3 = make_position(asset_id="VALE3", book="EQUITIES")
    ltn = make_position(
        asset_id="LTN_2027",
        instrument_type=InstrumentType.LTN,
        book="RATES",
    )

    portfolio = Portfolio(positions=(petr4, vale3, ltn))

    grouped = portfolio.positions_by_book()

    assert grouped["EQUITIES"] == (petr4, vale3)
    assert grouped["RATES"] == (ltn,)


def test_group_positions_by_instrument_type() -> None:
    petr4 = make_position(asset_id="PETR4")
    vale3 = make_position(asset_id="VALE3")
    ltn = make_position(
        asset_id="LTN_2027",
        instrument_type=InstrumentType.LTN,
        book="RATES",
    )

    portfolio = Portfolio(positions=(petr4, vale3, ltn))

    grouped = portfolio.positions_by_instrument_type()

    assert grouped[InstrumentType.EQUITY] == (petr4, vale3)
    assert grouped[InstrumentType.LTN] == (ltn,)
