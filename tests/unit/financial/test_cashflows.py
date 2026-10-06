from datetime import date

import pytest
from pydantic import ValidationError

from portfolio_risk.financial.cashflows import CashFlow


def test_cash_flow_stores_payment_date_and_amount() -> None:
    cash_flow = CashFlow(
        payment_date=date(2030, 1, 1),
        amount=100.0,
    )

    assert cash_flow.payment_date == date(2030, 1, 1)
    assert cash_flow.amount == 100.0


def test_cash_flow_accepts_negative_amount() -> None:
    cash_flow = CashFlow(
        payment_date=date(2030, 1, 1),
        amount=-100.0,
    )

    assert cash_flow.amount == -100.0


def test_cash_flow_accepts_zero_amount() -> None:
    cash_flow = CashFlow(
        payment_date=date(2030, 1, 1),
        amount=0.0,
    )

    assert cash_flow.amount == 0.0


def test_cash_flow_is_immutable() -> None:
    cash_flow = CashFlow(
        payment_date=date(2030, 1, 1),
        amount=100.0,
    )

    with pytest.raises(ValidationError):
        cash_flow.amount = 120.0


def test_cash_flow_accepts_historical_dates() -> None:
    cash_flow = CashFlow(
        payment_date=date(2000, 1, 1),
        amount=100.0,
    )

    assert cash_flow.payment_date == date(2000, 1, 1)


def test_cash_flow_rejects_invalid_payment_date() -> None:
    with pytest.raises(ValidationError):
        CashFlow(
            payment_date="not-a-date",
            amount=100.0,
        )
