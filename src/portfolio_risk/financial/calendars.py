from datetime import date, timedelta

from pydantic import BaseModel, ConfigDict, field_validator


class BusinessCalendar(BaseModel):
    """Minimal business-day calendar used by financial conventions."""

    model_config = ConfigDict(frozen=True)

    holidays: frozenset[date] = frozenset()
    weekend_days: frozenset[int] = frozenset({5, 6})

    @field_validator("weekend_days")
    @classmethod
    def validate_weekend_days(cls, value: frozenset[int]) -> frozenset[int]:
        """Ensure weekday indexes follow datetime.weekday() conventions."""
        if any(day < 0 or day > 6 for day in value):
            raise ValueError("Weekend days must be integers between 0 and 6.")

        return value

    def is_business_day(self, target_date: date) -> bool:
        """Return whether a date is a business day."""
        return (
            target_date.weekday() not in self.weekend_days
            and target_date not in self.holidays
        )

    def business_days_between(self, start_date: date, end_date: date) -> int:
        """Count business days in the interval (start_date, end_date].

        Reversing the dates reverses the sign of the result.
        """
        if start_date == end_date:
            return 0

        if end_date < start_date:
            return -self.business_days_between(end_date, start_date)

        business_days = 0
        current_date = start_date + timedelta(days=1)

        while current_date <= end_date:
            if self.is_business_day(current_date):
                business_days += 1

            current_date += timedelta(days=1)

        return business_days
