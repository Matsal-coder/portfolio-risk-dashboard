from datetime import date

import pytest

from portfolio_risk.financial.calendars import BusinessCalendar
from portfolio_risk.financial.day_count import (
    DayCountConvention,
    year_fraction,
)


def test_act_365_known_period() -> None:
    result = year_fraction(
        date(2026, 1, 1),
        date(2026, 7, 1),
        DayCountConvention.ACT_365,
    )

    assert result == pytest.approx(181 / 365)


def test_act_365_uses_actual_days_across_leap_day() -> None:
    result = year_fraction(
        date(2024, 2, 28),
        date(2024, 3, 1),
        DayCountConvention.ACT_365,
    )

    assert result == pytest.approx(2 / 365)


def test_act_360_known_period() -> None:
    result = year_fraction(
        date(2026, 1, 1),
        date(2026, 4, 1),
        DayCountConvention.ACT_360,
    )

    assert result == pytest.approx(90 / 360)


def test_thirty_e_360_adjusts_day_31_to_day_30() -> None:
    result = year_fraction(
        date(2026, 1, 31),
        date(2026, 2, 28),
        DayCountConvention.THIRTY_E_360,
    )

    assert result == pytest.approx(28 / 360)


def test_thirty_e_360_full_year_is_one() -> None:
    result = year_fraction(
        date(2026, 1, 30),
        date(2027, 1, 30),
        DayCountConvention.THIRTY_E_360,
    )

    assert result == pytest.approx(1.0)


def test_bus_252_counts_business_days() -> None:
    calendar = BusinessCalendar()

    result = year_fraction(
        date(2026, 1, 5),
        date(2026, 1, 12),
        DayCountConvention.BUS_252,
        calendar=calendar,
    )

    assert result == pytest.approx(5 / 252)


def test_bus_252_respects_explicit_holidays() -> None:
    calendar = BusinessCalendar(
        holidays=frozenset({date(2026, 1, 7)}),
    )

    result = year_fraction(
        date(2026, 1, 5),
        date(2026, 1, 12),
        DayCountConvention.BUS_252,
        calendar=calendar,
    )

    assert result == pytest.approx(4 / 252)


def test_bus_252_requires_explicit_calendar() -> None:
    with pytest.raises(
        ValueError,
        match="BUS/252 requires an explicit business calendar",
    ):
        year_fraction(
            date(2026, 1, 5),
            date(2026, 1, 12),
            DayCountConvention.BUS_252,
        )


@pytest.mark.parametrize(
    "convention",
    [
        DayCountConvention.ACT_365,
        DayCountConvention.ACT_360,
        DayCountConvention.THIRTY_E_360,
        DayCountConvention.BUS_252,
    ],
)
def test_equal_dates_have_zero_year_fraction(
    convention: DayCountConvention,
) -> None:
    calendar = BusinessCalendar()

    result = year_fraction(
        date(2026, 1, 5),
        date(2026, 1, 5),
        convention,
        calendar=calendar,
    )

    assert result == 0.0


@pytest.mark.parametrize(
    "convention",
    [
        DayCountConvention.ACT_365,
        DayCountConvention.ACT_360,
        DayCountConvention.THIRTY_E_360,
        DayCountConvention.BUS_252,
    ],
)
def test_reversing_dates_changes_year_fraction_sign(
    convention: DayCountConvention,
) -> None:
    calendar = BusinessCalendar()

    forward = year_fraction(
        date(2026, 1, 5),
        date(2026, 7, 1),
        convention,
        calendar=calendar,
    )
    backward = year_fraction(
        date(2026, 7, 1),
        date(2026, 1, 5),
        convention,
        calendar=calendar,
    )

    assert backward == pytest.approx(-forward)
