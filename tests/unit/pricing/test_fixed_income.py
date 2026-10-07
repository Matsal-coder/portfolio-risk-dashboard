from datetime import date

import pytest

from portfolio_risk.curves.models import CurveNode, YieldCurve
from portfolio_risk.financial.cashflows import CashFlow
from portfolio_risk.financial.compounding import (
    CompoundingConvention,
    CompoundingType,
)
from portfolio_risk.financial.day_count import DayCountConvention
from portfolio_risk.instruments.government_bonds import LTNTerms
from portfolio_risk.pricing.fixed_income import (
    present_value_cash_flows,
    price_ltn,
)


@pytest.fixture
def annual_compounding() -> CompoundingConvention:
    return CompoundingConvention(
        compounding_type=CompoundingType.COMPOUNDED,
        frequency=1,
    )


@pytest.fixture
def curve(
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
        ),
        day_count=DayCountConvention.ACT_365,
        compounding=annual_compounding,
    )


def test_present_value_cash_flows_uses_curve_discount_factors(
    curve: YieldCurve,
) -> None:
    cash_flows = (
        CashFlow(
            payment_date=date(2027, 1, 1),
            amount=100.0,
        ),
        CashFlow(
            payment_date=date(2028, 1, 1),
            amount=100.0,
        ),
    )

    result = present_value_cash_flows(
        cash_flows=cash_flows,
        curve=curve,
    )

    expected = 100.0 * curve.discount_factor(
        date(2027, 1, 1)
    ) + 100.0 * curve.discount_factor(date(2028, 1, 1))

    assert result == pytest.approx(expected)


def test_ltn_price_on_exact_curve_node(
    curve: YieldCurve,
) -> None:
    terms = LTNTerms(
        maturity_date=date(2027, 1, 1),
        face_value=1000.0,
    )

    result = price_ltn(
        terms=terms,
        curve=curve,
    )

    assert result == pytest.approx(1000.0 / 1.10)


def test_ltn_price_uses_face_value(
    curve: YieldCurve,
) -> None:
    terms = LTNTerms(
        maturity_date=date(2027, 1, 1),
        face_value=2000.0,
    )

    result = price_ltn(
        terms=terms,
        curve=curve,
    )

    assert result == pytest.approx(2000.0 / 1.10)


def test_ltn_price_uses_interpolated_discount_factor(
    curve: YieldCurve,
) -> None:
    maturity_date = date(2027, 7, 2)

    terms = LTNTerms(
        maturity_date=maturity_date,
        face_value=1000.0,
    )

    result = price_ltn(
        terms=terms,
        curve=curve,
    )

    expected = 1000.0 * curve.discount_factor(maturity_date)

    assert result == pytest.approx(expected)


def test_ltn_price_rejects_maturity_on_curve_as_of(
    curve: YieldCurve,
) -> None:
    terms = LTNTerms(
        maturity_date=curve.as_of,
        face_value=1000.0,
    )

    with pytest.raises(
        ValueError,
        match="must be after the curve as-of date",
    ):
        price_ltn(
            terms=terms,
            curve=curve,
        )


def test_ltn_price_rejects_maturity_before_curve_as_of(
    curve: YieldCurve,
) -> None:
    terms = LTNTerms(
        maturity_date=date(2025, 12, 31),
        face_value=1000.0,
    )

    with pytest.raises(
        ValueError,
        match="must be after the curve as-of date",
    ):
        price_ltn(
            terms=terms,
            curve=curve,
        )


def test_ltn_price_rejects_curve_extrapolation(
    curve: YieldCurve,
) -> None:
    terms = LTNTerms(
        maturity_date=date(2030, 1, 1),
        face_value=1000.0,
    )

    with pytest.raises(
        ValueError,
        match="after the last curve node",
    ):
        price_ltn(
            terms=terms,
            curve=curve,
        )
