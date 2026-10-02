import pytest
from pydantic import ValidationError

from portfolio_risk.instruments.models import Instrument, InstrumentType


def test_create_valid_instrument() -> None:
    instrument = Instrument(
        asset_id="PETR4",
        instrument_type=InstrumentType.EQUITY,
    )

    assert instrument.asset_id == "PETR4"
    assert instrument.instrument_type == InstrumentType.EQUITY


def test_instrument_type_can_be_parsed_from_string() -> None:
    instrument = Instrument(
        asset_id="LTN_2027",
        instrument_type="LTN",
    )

    assert instrument.instrument_type == InstrumentType.LTN


def test_reject_empty_asset_id() -> None:
    with pytest.raises(ValidationError):
        Instrument(
            asset_id="",
            instrument_type=InstrumentType.EQUITY,
        )


def test_reject_invalid_instrument_type() -> None:
    with pytest.raises(ValidationError):
        Instrument(
            asset_id="PETR4",
            instrument_type="INVALID_TYPE",
        )


def test_instrument_is_immutable() -> None:
    instrument = Instrument(
        asset_id="PETR4",
        instrument_type=InstrumentType.EQUITY,
    )

    with pytest.raises(ValidationError):
        instrument.asset_id = "VALE3"
