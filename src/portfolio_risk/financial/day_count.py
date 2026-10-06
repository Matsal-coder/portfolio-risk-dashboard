from datetime import date
from enum import StrEnum

from portfolio_risk.financial.calendars import BusinessCalendar


class DayCountConvention(StrEnum):
    """Supported financial day-count conventions."""

    ACT_365 = "ACT/365"
    ACT_360 = "ACT/360"
    THIRTY_E_360 = "30E/360"
    BUS_252 = "BUS/252"


def year_fraction(
    start_date: date,
    end_date: date,
    convention: DayCountConvention,
    calendar: BusinessCalendar | None = None,
) -> float:
    """Return the year fraction between two dates under a financial convention."""
    if start_date == end_date:
        return 0.0

    if end_date < start_date:
        return -year_fraction(
            end_date,
            start_date,
            convention,
            calendar=calendar,
        )

    if convention == DayCountConvention.ACT_365:
        return (end_date - start_date).days / 365.0

    if convention == DayCountConvention.ACT_360:
        return (end_date - start_date).days / 360.0

    if convention == DayCountConvention.THIRTY_E_360:
        return _thirty_e_360_year_fraction(start_date, end_date)

    if convention == DayCountConvention.BUS_252:
        if calendar is None:
            raise ValueError("BUS/252 requires an explicit business calendar.")

        business_days = calendar.business_days_between(start_date, end_date)
        return business_days / 252.0

    raise ValueError(f"Unsupported day-count convention: {convention!r}")


def _thirty_e_360_year_fraction(start_date: date, end_date: date) -> float:
    """Return the 30E/360 year fraction between two ordered dates."""
    start_day = min(start_date.day, 30)
    end_day = min(end_date.day, 30)

    numerator = (
        360 * (end_date.year - start_date.year)
        + 30 * (end_date.month - start_date.month)
        + (end_day - start_day)
    )

    return numerator / 360.0
