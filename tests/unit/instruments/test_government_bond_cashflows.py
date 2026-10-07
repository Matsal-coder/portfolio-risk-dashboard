from datetime import date

from portfolio_risk.instruments.government_bond_cashflows import (
    generate_ltn_cash_flows,
)
from portfolio_risk.instruments.government_bonds import LTNTerms


def test_ltn_generates_single_redemption_cash_flow() -> None:
    terms = LTNTerms(
        maturity_date=date(2028, 1, 1),
        face_value=1000.0,
    )

    cash_flows = generate_ltn_cash_flows(terms)

    assert len(cash_flows) == 1
    assert cash_flows[0].payment_date == date(2028, 1, 1)
    assert cash_flows[0].amount == 1000.0


def test_ltn_cash_flow_uses_configured_face_value() -> None:
    terms = LTNTerms(
        maturity_date=date(2030, 1, 1),
        face_value=2500.0,
    )

    cash_flows = generate_ltn_cash_flows(terms)

    assert cash_flows[0].amount == 2500.0
