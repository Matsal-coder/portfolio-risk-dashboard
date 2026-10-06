from datetime import date

import pytest
from pydantic import ValidationError

from portfolio_risk.financial.calendars import BusinessCalendar


def test_weekday_is_business_day() -> None:
    calendar = BusinessCalendar()

    assert calendar.is_business_day(date(2026, 1, 5))


def test_weekend_is_not_business_day() -> None:
    calendar = BusinessCalendar()

    assert not calendar.is_business_day(date(2026, 1, 10))


def test_explicit_holiday_is_not_business_day() -> None:
    holiday = date(2026, 1, 7)
    calendar = BusinessCalendar(holidays=frozenset({holiday}))

    assert not calendar.is_business_day(holiday)


def test_business_days_between_excludes_start_and_includes_end() -> None:
    calendar = BusinessCalendar()

    result = calendar.business_days_between(
        date(2026, 1, 5),
        date(2026, 1, 12),
    )

    assert result == 5


def test_business_days_between_respects_holidays() -> None:
    calendar = BusinessCalendar(
        holidays=frozenset({date(2026, 1, 7)}),
    )

    result = calendar.business_days_between(
        date(2026, 1, 5),
        date(2026, 1, 12),
    )

    assert result == 4


def test_business_days_between_same_date_is_zero() -> None:
    calendar = BusinessCalendar()

    assert (
        calendar.business_days_between(
            date(2026, 1, 5),
            date(2026, 1, 5),
        )
        == 0
    )


def test_business_days_between_reversed_dates_changes_sign() -> None:
    calendar = BusinessCalendar()

    forward = calendar.business_days_between(
        date(2026, 1, 5),
        date(2026, 1, 12),
    )
    backward = calendar.business_days_between(
        date(2026, 1, 12),
        date(2026, 1, 5),
    )

    assert backward == -forward


def test_invalid_weekend_day_is_rejected() -> None:
    with pytest.raises(ValidationError):
        BusinessCalendar(weekend_days=frozenset({6, 7}))
