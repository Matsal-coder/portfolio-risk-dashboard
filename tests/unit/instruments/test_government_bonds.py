from datetime import date

import pytest
from pydantic import ValidationError

from portfolio_risk.instruments.government_bonds import (
    GovernmentBondIndexer,
    LFTTerms,
    LTNTerms,
    NTNBTerms,
    NTNFTerms,
)


def test_create_valid_ltn_terms() -> None:
    terms = LTNTerms(
        maturity_date=date(2028, 1, 1),
        face_value=1000.0,
    )

    assert terms.maturity_date == date(2028, 1, 1)
    assert terms.face_value == 1000.0
    assert terms.indexer == GovernmentBondIndexer.NONE


def test_create_valid_ntnf_terms() -> None:
    terms = NTNFTerms(
        maturity_date=date(2031, 1, 1),
        face_value=1000.0,
        coupon_rate=0.10,
        coupon_frequency_per_year=2,
    )

    assert terms.coupon_rate == 0.10
    assert terms.coupon_frequency_per_year == 2
    assert terms.indexer == GovernmentBondIndexer.NONE


def test_create_valid_lft_terms() -> None:
    terms = LFTTerms(
        maturity_date=date(2030, 3, 1),
        face_value=1000.0,
    )

    assert terms.indexer == GovernmentBondIndexer.SELIC


def test_create_valid_ntnb_terms() -> None:
    terms = NTNBTerms(
        maturity_date=date(2035, 5, 15),
        face_value=1000.0,
        coupon_rate=0.06,
        coupon_frequency_per_year=2,
    )

    assert terms.coupon_rate == 0.06
    assert terms.coupon_frequency_per_year == 2
    assert terms.indexer == GovernmentBondIndexer.IPCA


def test_ntnb_can_represent_zero_coupon_contract() -> None:
    terms = NTNBTerms(
        maturity_date=date(2035, 5, 15),
        face_value=1000.0,
        coupon_rate=0.0,
        coupon_frequency_per_year=2,
    )

    assert terms.coupon_rate == 0.0


@pytest.mark.parametrize(
    ("terms_class", "kwargs"),
    [
        (
            LTNTerms,
            {},
        ),
        (
            NTNFTerms,
            {
                "coupon_rate": 0.10,
                "coupon_frequency_per_year": 2,
            },
        ),
        (
            LFTTerms,
            {},
        ),
        (
            NTNBTerms,
            {
                "coupon_rate": 0.06,
                "coupon_frequency_per_year": 2,
            },
        ),
    ],
)
def test_reject_non_positive_face_value(
    terms_class: type,
    kwargs: dict[str, float | int],
) -> None:
    with pytest.raises(ValidationError):
        terms_class(
            maturity_date=date(2030, 1, 1),
            face_value=0.0,
            **kwargs,
        )


def test_reject_non_positive_ntnf_coupon_rate() -> None:
    with pytest.raises(ValidationError):
        NTNFTerms(
            maturity_date=date(2030, 1, 1),
            face_value=1000.0,
            coupon_rate=0.0,
            coupon_frequency_per_year=2,
        )


def test_reject_non_positive_coupon_frequency() -> None:
    with pytest.raises(ValidationError):
        NTNFTerms(
            maturity_date=date(2030, 1, 1),
            face_value=1000.0,
            coupon_rate=0.10,
            coupon_frequency_per_year=0,
        )


def test_government_bond_terms_are_immutable() -> None:
    terms = LTNTerms(
        maturity_date=date(2030, 1, 1),
        face_value=1000.0,
    )

    with pytest.raises(ValidationError):
        terms.face_value = 1200.0


@pytest.mark.parametrize(
    ("terms_class", "kwargs", "wrong_indexer"),
    [
        (
            LTNTerms,
            {},
            GovernmentBondIndexer.IPCA,
        ),
        (
            NTNFTerms,
            {
                "coupon_rate": 0.10,
                "coupon_frequency_per_year": 2,
            },
            GovernmentBondIndexer.SELIC,
        ),
        (
            LFTTerms,
            {},
            GovernmentBondIndexer.NONE,
        ),
        (
            NTNBTerms,
            {
                "coupon_rate": 0.06,
                "coupon_frequency_per_year": 2,
            },
            GovernmentBondIndexer.NONE,
        ),
    ],
)
def test_reject_indexer_incompatible_with_bond_type(
    terms_class: type,
    kwargs: dict[str, float | int],
    wrong_indexer: GovernmentBondIndexer,
) -> None:
    with pytest.raises(ValidationError):
        terms_class(
            maturity_date=date(2030, 1, 1),
            face_value=1000.0,
            indexer=wrong_indexer,
            **kwargs,
        )
