import pytest

from portfolio_risk.instruments.models import Instrument, InstrumentType
from portfolio_risk.instruments.registry import (
    InstrumentAlreadyRegisteredError,
    InstrumentNotFoundError,
    InstrumentRegistry,
)


def make_equity(asset_id: str = "PETR4") -> Instrument:
    return Instrument(
        asset_id=asset_id,
        instrument_type=InstrumentType.EQUITY,
    )


def test_register_and_get_instrument() -> None:
    registry = InstrumentRegistry()
    instrument = make_equity()

    registry.register(instrument)

    assert registry.get("PETR4") == instrument


def test_contains_registered_instrument() -> None:
    registry = InstrumentRegistry()
    registry.register(make_equity())

    assert registry.contains("PETR4")
    assert not registry.contains("VALE3")


def test_registry_length() -> None:
    registry = InstrumentRegistry()

    registry.register(make_equity("PETR4"))
    registry.register(make_equity("VALE3"))

    assert len(registry) == 2


def test_reject_duplicate_asset_id() -> None:
    registry = InstrumentRegistry()
    registry.register(make_equity())

    with pytest.raises(
        InstrumentAlreadyRegisteredError,
        match="PETR4",
    ):
        registry.register(make_equity())


def test_raise_error_for_unknown_asset_id() -> None:
    registry = InstrumentRegistry()

    with pytest.raises(
        InstrumentNotFoundError,
        match="UNKNOWN",
    ):
        registry.get("UNKNOWN")
