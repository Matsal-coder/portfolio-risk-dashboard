from datetime import date

from pydantic import BaseModel, ConfigDict


class CashFlow(BaseModel):
    """Single monetary cash flow occurring on a payment date."""

    model_config = ConfigDict(frozen=True)

    payment_date: date
    amount: float
