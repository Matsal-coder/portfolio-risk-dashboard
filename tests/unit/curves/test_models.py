import math
from datetime import date

import pytest
from pydantic import ValidationError

from portfolio_risk.curves.models import CurveNode, YieldCurve
from portfolio_risk.financial.calendars import BusinessCalendar
from portfolio_risk.financial.compounding import (
    CompoundingConvention,
    CompoundingType,
)
from portfolio_risk.financial.day_count import DayCountConvention


@pytest.fixture
def annual_compounding() -> CompoundingConvention:
    return CompoundingConvention(
        compounding_type=CompoundingType.COMPOUNDED,
        frequency=1,
    )


def test_curve_node_stores_maturity_and_zero_rate() -> None:
    node = CurveNode(
        maturity_date=date(2027, 1, 1),
        zero_rate=0.10,
    )

    assert node.maturity_date == date(2027, 1, 1)
    assert node.zero_rate == 0.10


def test_curve_node_accepts_negative_zero_rate() -> None:
    node = CurveNode(
        maturity_date=date(2027, 1, 1),
        zero_rate=-0.01,
    )

    assert node.zero_rate == -0.01


def test_curve_node_is_immutable() -> None:
    node = CurveNode(
        maturity_date=date(2027, 1, 1),
        zero_rate=0.10,
    )

    with pytest.raises(ValidationError):
        node.zero_rate = 0.11


def test_yield_curve_requires_at_least_two_nodes(
    annual_compounding: CompoundingConvention,
) -> None:
    with pytest.raises(
        ValidationError,
        match="requires at least two nodes",
    ):
        YieldCurve(
            as_of=date(2026, 1, 1),
            nodes=(
                CurveNode(
                    maturity_date=date(2027, 1, 1),
                    zero_rate=0.10,
                ),
            ),
            day_count=DayCountConvention.ACT_365,
            compounding=annual_compounding,
        )


def test_yield_curve_rejects_node_on_as_of_date(
    annual_compounding: CompoundingConvention,
) -> None:
    with pytest.raises(
        ValidationError,
        match="must be after the curve as-of date",
    ):
        YieldCurve(
            as_of=date(2026, 1, 1),
            nodes=(
                CurveNode(
                    maturity_date=date(2026, 1, 1),
                    zero_rate=0.09,
                ),
                CurveNode(
                    maturity_date=date(2027, 1, 1),
                    zero_rate=0.10,
                ),
            ),
            day_count=DayCountConvention.ACT_365,
            compounding=annual_compounding,
        )


def test_yield_curve_rejects_node_before_as_of_date(
    annual_compounding: CompoundingConvention,
) -> None:
    with pytest.raises(
        ValidationError,
        match="must be after the curve as-of date",
    ):
        YieldCurve(
            as_of=date(2026, 1, 1),
            nodes=(
                CurveNode(
                    maturity_date=date(2025, 12, 31),
                    zero_rate=0.09,
                ),
                CurveNode(
                    maturity_date=date(2027, 1, 1),
                    zero_rate=0.10,
                ),
            ),
            day_count=DayCountConvention.ACT_365,
            compounding=annual_compounding,
        )


def test_yield_curve_rejects_duplicate_maturities(
    annual_compounding: CompoundingConvention,
) -> None:
    with pytest.raises(
        ValidationError,
        match="must be unique",
    ):
        YieldCurve(
            as_of=date(2026, 1, 1),
            nodes=(
                CurveNode(
                    maturity_date=date(2027, 1, 1),
                    zero_rate=0.10,
                ),
                CurveNode(
                    maturity_date=date(2027, 1, 1),
                    zero_rate=0.11,
                ),
            ),
            day_count=DayCountConvention.ACT_365,
            compounding=annual_compounding,
        )


def test_yield_curve_orders_nodes_by_maturity(
    annual_compounding: CompoundingConvention,
) -> None:
    curve = YieldCurve(
        as_of=date(2026, 1, 1),
        nodes=(
            CurveNode(
                maturity_date=date(2030, 1, 1),
                zero_rate=0.12,
            ),
            CurveNode(
                maturity_date=date(2027, 1, 1),
                zero_rate=0.10,
            ),
            CurveNode(
                maturity_date=date(2028, 1, 1),
                zero_rate=0.11,
            ),
        ),
        day_count=DayCountConvention.ACT_365,
        compounding=annual_compounding,
    )

    assert [node.maturity_date for node in curve.nodes] == [
        date(2027, 1, 1),
        date(2028, 1, 1),
        date(2030, 1, 1),
    ]


def test_bus_252_curve_requires_calendar(
    annual_compounding: CompoundingConvention,
) -> None:
    with pytest.raises(
        ValidationError,
        match="require an explicit business calendar",
    ):
        YieldCurve(
            as_of=date(2026, 1, 1),
            nodes=(
                CurveNode(
                    maturity_date=date(2027, 1, 1),
                    zero_rate=0.10,
                ),
                CurveNode(
                    maturity_date=date(2028, 1, 1),
                    zero_rate=0.11,
                ),
            ),
            day_count=DayCountConvention.BUS_252,
            compounding=annual_compounding,
        )


def test_bus_252_curve_accepts_calendar(
    annual_compounding: CompoundingConvention,
) -> None:
    calendar = BusinessCalendar()

    curve = YieldCurve(
        as_of=date(2026, 1, 1),
        nodes=(
            CurveNode(
                maturity_date=date(2027, 1, 1),
                zero_rate=0.10,
            ),
            CurveNode(
                maturity_date=date(2028, 1, 1),
                zero_rate=0.11,
            ),
        ),
        day_count=DayCountConvention.BUS_252,
        compounding=annual_compounding,
        calendar=calendar,
    )

    assert curve.calendar == calendar


def test_non_bus_252_curve_does_not_require_calendar(
    annual_compounding: CompoundingConvention,
) -> None:
    curve = YieldCurve(
        as_of=date(2026, 1, 1),
        nodes=(
            CurveNode(
                maturity_date=date(2027, 1, 1),
                zero_rate=0.10,
            ),
            CurveNode(
                maturity_date=date(2028, 1, 1),
                zero_rate=0.11,
            ),
        ),
        day_count=DayCountConvention.ACT_365,
        compounding=annual_compounding,
    )

    assert curve.calendar is None


def test_yield_curve_is_immutable(
    annual_compounding: CompoundingConvention,
) -> None:
    curve = YieldCurve(
        as_of=date(2026, 1, 1),
        nodes=(
            CurveNode(
                maturity_date=date(2027, 1, 1),
                zero_rate=0.10,
            ),
            CurveNode(
                maturity_date=date(2028, 1, 1),
                zero_rate=0.11,
            ),
        ),
        day_count=DayCountConvention.ACT_365,
        compounding=annual_compounding,
    )

    with pytest.raises(ValidationError):
        curve.as_of = date(2026, 2, 1)


@pytest.fixture
def simple_curve(
    annual_compounding: CompoundingConvention,
) -> YieldCurve:
    return YieldCurve(
        as_of=date(2026, 1, 1),
        nodes=(
            CurveNode(
                maturity_date=date(2027, 1, 1),
                zero_rate=0.10,
            ),
            CurveNode(
                maturity_date=date(2028, 1, 1),
                zero_rate=0.12,
            ),
            CurveNode(
                maturity_date=date(2030, 1, 1),
                zero_rate=0.13,
            ),
        ),
        day_count=DayCountConvention.ACT_365,
        compounding=annual_compounding,
    )


def test_discount_factor_on_as_of_date_is_one(
    simple_curve: YieldCurve,
) -> None:
    assert simple_curve.discount_factor(date(2026, 1, 1)) == 1.0


def test_zero_rate_on_exact_node_returns_stored_rate(
    simple_curve: YieldCurve,
) -> None:
    result = simple_curve.zero_rate(date(2027, 1, 1))

    assert result == pytest.approx(0.10)


def test_discount_factor_on_exact_node_uses_node_zero_rate(
    simple_curve: YieldCurve,
) -> None:
    result = simple_curve.discount_factor(date(2027, 1, 1))

    assert result == pytest.approx(1 / 1.10)


def test_discount_factor_interpolates_between_nodes(
    simple_curve: YieldCurve,
) -> None:
    target_date = date(2027, 7, 2)

    result = simple_curve.discount_factor(target_date)

    left_time = 365 / 365
    right_time = 730 / 365
    target_time = 547 / 365

    left_df = 1 / (1.10**left_time)
    right_df = 1 / (1.12**right_time)

    weight = (target_time - left_time) / (right_time - left_time)

    expected = math.exp(
        math.log(left_df) + weight * (math.log(right_df) - math.log(left_df))
    )

    assert result == pytest.approx(expected)


def test_interpolated_zero_rate_is_consistent_with_discount_factor(
    simple_curve: YieldCurve,
) -> None:
    target_date = date(2027, 7, 2)

    discount_factor = simple_curve.discount_factor(target_date)
    zero_rate = simple_curve.zero_rate(target_date)

    target_time = (target_date - simple_curve.as_of).days / 365

    reconstructed_discount_factor = 1 / (1 + zero_rate) ** target_time

    assert reconstructed_discount_factor == pytest.approx(discount_factor)


def test_discount_factor_rejects_date_before_as_of(
    simple_curve: YieldCurve,
) -> None:
    with pytest.raises(
        ValueError,
        match="before the curve as-of date",
    ):
        simple_curve.discount_factor(date(2025, 12, 31))


def test_zero_rate_rejects_as_of_date(
    simple_curve: YieldCurve,
) -> None:
    with pytest.raises(
        ValueError,
        match="requires a target date after",
    ):
        simple_curve.zero_rate(date(2026, 1, 1))


def test_zero_rate_rejects_date_before_as_of(
    simple_curve: YieldCurve,
) -> None:
    with pytest.raises(
        ValueError,
        match="requires a target date after",
    ):
        simple_curve.zero_rate(date(2025, 12, 31))


def test_discount_factor_rejects_extrapolation_before_first_node(
    simple_curve: YieldCurve,
) -> None:
    with pytest.raises(
        ValueError,
        match="before the first curve node",
    ):
        simple_curve.discount_factor(date(2026, 6, 1))


def test_discount_factor_rejects_extrapolation_after_last_node(
    simple_curve: YieldCurve,
) -> None:
    with pytest.raises(
        ValueError,
        match="after the last curve node",
    ):
        simple_curve.discount_factor(date(2031, 1, 1))


def test_forward_rate_between_exact_nodes(
    simple_curve: YieldCurve,
) -> None:
    result = simple_curve.forward_rate(
        date(2027, 1, 1),
        date(2028, 1, 1),
    )

    start_df = 1 / 1.10
    end_df = 1 / (1.12**2)
    forward_df = end_df / start_df

    expected = 1 / forward_df - 1

    assert result == pytest.approx(expected)


def test_forward_rate_from_as_of_matches_zero_rate_at_node(
    simple_curve: YieldCurve,
) -> None:
    result = simple_curve.forward_rate(
        simple_curve.as_of,
        date(2028, 1, 1),
    )

    assert result == pytest.approx(0.12)


def test_forward_rate_supports_interpolated_dates(
    simple_curve: YieldCurve,
) -> None:
    start_date = date(2027, 7, 2)
    end_date = date(2028, 1, 1)

    result = simple_curve.forward_rate(
        start_date,
        end_date,
    )

    start_df = simple_curve.discount_factor(start_date)
    end_df = simple_curve.discount_factor(end_date)

    period = (end_date - start_date).days / 365
    forward_df = end_df / start_df

    expected = forward_df ** (-1 / period) - 1

    assert result == pytest.approx(expected)


def test_forward_rate_rejects_start_before_as_of(
    simple_curve: YieldCurve,
) -> None:
    with pytest.raises(
        ValueError,
        match="cannot be before the curve as-of date",
    ):
        simple_curve.forward_rate(
            date(2025, 12, 31),
            date(2027, 1, 1),
        )


def test_forward_rate_rejects_equal_dates(
    simple_curve: YieldCurve,
) -> None:
    with pytest.raises(
        ValueError,
        match="must be after the start date",
    ):
        simple_curve.forward_rate(
            date(2027, 1, 1),
            date(2027, 1, 1),
        )


def test_forward_rate_rejects_end_before_start(
    simple_curve: YieldCurve,
) -> None:
    with pytest.raises(
        ValueError,
        match="must be after the start date",
    ):
        simple_curve.forward_rate(
            date(2028, 1, 1),
            date(2027, 1, 1),
        )


def test_forward_rate_preserves_no_extrapolation_policy(
    simple_curve: YieldCurve,
) -> None:
    with pytest.raises(
        ValueError,
        match="after the last curve node",
    ):
        simple_curve.forward_rate(
            date(2028, 1, 1),
            date(2031, 1, 1),
        )
