from portfolio_risk.financial.cashflows import CashFlow
from portfolio_risk.instruments.government_bonds import LTNTerms


def generate_ltn_cash_flows(
    terms: LTNTerms,
) -> tuple[CashFlow, ...]:
    """Generate the contractual cash flows of an LTN.

    An LTN is a nominal zero-coupon government bond. Its contractual
    cash flow consists of a single redemption of face value at maturity.
    """
    return (
        CashFlow(
            payment_date=terms.maturity_date,
            amount=terms.face_value,
        ),
    )
