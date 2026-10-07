from collections.abc import Iterable

from portfolio_risk.curves.models import YieldCurve
from portfolio_risk.financial.cashflows import CashFlow
from portfolio_risk.instruments.government_bond_cashflows import (
    generate_ltn_cash_flows,
)
from portfolio_risk.instruments.government_bonds import LTNTerms


def present_value_cash_flows(
    cash_flows: Iterable[CashFlow],
    curve: YieldCurve,
) -> float:
    """Return the present value of cash flows using a zero curve."""
    return sum(
        cash_flow.amount * curve.discount_factor(cash_flow.payment_date)
        for cash_flow in cash_flows
    )


def price_ltn(
    terms: LTNTerms,
    curve: YieldCurve,
) -> float:
    """Return the model price of one LTN unit.

    The LTN is priced from its contractual redemption cash flow using
    discount factors implied by the supplied zero curve.

    The returned value is a unit price. Position quantity and position
    sign are intentionally excluded from instrument pricing.
    """
    if terms.maturity_date <= curve.as_of:
        raise ValueError("LTN maturity date must be after the curve as-of date.")

    cash_flows = generate_ltn_cash_flows(terms)

    return present_value_cash_flows(
        cash_flows=cash_flows,
        curve=curve,
    )


def test_present_value_of_empty_cash_flows_is_zero(
    curve: YieldCurve,
) -> None:
    result = present_value_cash_flows(
        cash_flows=(),
        curve=curve,
    )

    assert result == 0.0
