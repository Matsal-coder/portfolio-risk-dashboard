from datetime import date

import pytest
from pydantic import ValidationError

from portfolio_risk.curves.models import CurveNode, YieldCurve
from portfolio_risk.financial.compounding import (
    CompoundingConvention,
    CompoundingType,
)
from portfolio_risk.financial.day_count import DayCountConvention
from portfolio_risk.market_data.models import (
    CurveMarketData,
    MarketDataNotFoundError,
    MarketDataPoint,
    MarketSnapshot,
    with_curves,
)


def make_point(
    key: str = "PETR4",
    value: float = 40.0,
) -> MarketDataPoint:
    return MarketDataPoint(
        key=key,
        value=value,
    )


def make_curve(
    as_of: date = date(2026, 9, 30),
) -> YieldCurve:
    return YieldCurve(
        as_of=as_of,
        nodes=(
            CurveNode(
                maturity_date=date(2027, 9, 30),
                zero_rate=0.12,
            ),
            CurveNode(
                maturity_date=date(2028, 9, 30),
                zero_rate=0.115,
            ),
        ),
        day_count=DayCountConvention.ACT_365,
        compounding=CompoundingConvention(
            compounding_type=CompoundingType.COMPOUNDED,
            frequency=1,
        ),
    )


def test_create_curve_market_data() -> None:
    curve = make_curve()

    curve_data = CurveMarketData(
        key="BRL_NOMINAL",
        curve=curve,
    )

    assert curve_data.key == "BRL_NOMINAL"
    assert curve_data.curve == curve


def test_curve_market_data_rejects_empty_key() -> None:
    with pytest.raises(ValidationError):
        CurveMarketData(
            key="",
            curve=make_curve(),
        )


def test_curve_market_data_is_immutable() -> None:
    curve_data = CurveMarketData(
        key="BRL_NOMINAL",
        curve=make_curve(),
    )

    with pytest.raises(ValidationError):
        curve_data.key = "OTHER"


def test_market_snapshot_accepts_curves() -> None:
    curve = make_curve()

    snapshot = MarketSnapshot(
        as_of=date(2026, 9, 30),
        curves=(
            CurveMarketData(
                key="BRL_NOMINAL",
                curve=curve,
            ),
        ),
    )

    assert len(snapshot.curves) == 1


def test_snapshot_contains_curve_key() -> None:
    snapshot = MarketSnapshot(
        as_of=date(2026, 9, 30),
        curves=(
            CurveMarketData(
                key="BRL_NOMINAL",
                curve=make_curve(),
            ),
        ),
    )

    assert snapshot.contains_curve("BRL_NOMINAL")
    assert not snapshot.contains_curve("BRL_REAL")


def test_get_curve_from_market_snapshot() -> None:
    curve = make_curve()

    snapshot = MarketSnapshot(
        as_of=date(2026, 9, 30),
        curves=(
            CurveMarketData(
                key="BRL_NOMINAL",
                curve=curve,
            ),
        ),
    )

    assert snapshot.get_curve("BRL_NOMINAL") == curve


def test_get_missing_curve_raises_error() -> None:
    snapshot = MarketSnapshot(
        as_of=date(2026, 9, 30),
    )

    with pytest.raises(
        MarketDataNotFoundError,
        match="BRL_NOMINAL",
    ):
        snapshot.get_curve("BRL_NOMINAL")


def test_reject_duplicate_curve_keys() -> None:
    curve = make_curve()

    with pytest.raises(
        ValidationError,
        match="Curve keys must be unique",
    ):
        MarketSnapshot(
            as_of=date(2026, 9, 30),
            curves=(
                CurveMarketData(
                    key="BRL_NOMINAL",
                    curve=curve,
                ),
                CurveMarketData(
                    key="BRL_NOMINAL",
                    curve=curve,
                ),
            ),
        )


def test_reject_curve_with_different_as_of_date() -> None:
    curve = make_curve(
        as_of=date(2026, 10, 1),
    )

    with pytest.raises(
        ValidationError,
        match="must share the market snapshot as-of date",
    ):
        MarketSnapshot(
            as_of=date(2026, 9, 30),
            curves=(
                CurveMarketData(
                    key="BRL_NOMINAL",
                    curve=curve,
                ),
            ),
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


def test_enrich_market_snapshot_with_curves() -> None:
    scalar_snapshot = MarketSnapshot(
        as_of=date(2026, 9, 30),
        points=(make_point("PETR4", 40.0),),
    )

    curve = make_curve()

    enriched = with_curves(
        scalar_snapshot,
        (
            CurveMarketData(
                key="BRL_NOMINAL",
                curve=curve,
            ),
        ),
    )

    assert enriched.get("PETR4") == 40.0
    assert enriched.get_curve("BRL_NOMINAL") == curve
    assert scalar_snapshot.curves == ()
