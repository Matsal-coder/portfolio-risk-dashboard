from datetime import date

import pytest
from pydantic import ValidationError

from portfolio_risk.market_data.models import (
    MarketDataNotFoundError,
    MarketDataPoint,
    MarketSnapshot,
)


def make_point(
    key: str = "PETR4",
    value: float = 40.0,
) -> MarketDataPoint:
    return MarketDataPoint(
        key=key,
        value=value,
    )


def test_create_market_data_point() -> None:
    point = make_point()

    assert point.key == "PETR4"
    assert point.value == 40.0


def test_reject_empty_market_data_key() -> None:
    with pytest.raises(ValidationError):
        make_point(key="")


def test_market_data_point_is_immutable() -> None:
    point = make_point()

    with pytest.raises(ValidationError):
        point.value = 41.0


def test_create_market_snapshot() -> None:
    snapshot = MarketSnapshot(
        as_of=date(2026, 9, 30),
        points=(
            make_point("PETR4", 40.0),
            make_point("USD_BRL", 5.30),
        ),
    )

    assert snapshot.as_of == date(2026, 9, 30)
    assert len(snapshot.points) == 2


def test_snapshot_contains_market_data_key() -> None:
    snapshot = MarketSnapshot(
        as_of=date(2026, 9, 30),
        points=(make_point(),),
    )

    assert snapshot.contains("PETR4")
    assert not snapshot.contains("VALE3")


def test_get_market_data_value() -> None:
    snapshot = MarketSnapshot(
        as_of=date(2026, 9, 30),
        points=(make_point("PETR4", 40.0),),
    )

    assert snapshot.get("PETR4") == 40.0


def test_raise_error_for_missing_market_data_key() -> None:
    snapshot = MarketSnapshot(
        as_of=date(2026, 9, 30),
        points=(make_point(),),
    )

    with pytest.raises(
        MarketDataNotFoundError,
        match="VALE3",
    ):
        snapshot.get("VALE3")


def test_reject_duplicate_market_data_keys() -> None:
    with pytest.raises(
        ValidationError,
        match="Market data keys must be unique",
    ):
        MarketSnapshot(
            as_of=date(2026, 9, 30),
            points=(
                make_point("PETR4", 40.0),
                make_point("PETR4", 41.0),
            ),
        )


def test_snapshot_is_immutable() -> None:
    snapshot = MarketSnapshot(
        as_of=date(2026, 9, 30),
        points=(make_point(),),
    )

    with pytest.raises(ValidationError):
        snapshot.as_of = date(2026, 10, 1)
