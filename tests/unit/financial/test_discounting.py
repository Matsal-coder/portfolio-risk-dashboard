import math

import pytest

from portfolio_risk.financial.compounding import (
    CompoundingConvention,
    CompoundingType,
)
from portfolio_risk.financial.discounting import (
    discount_factor_from_rate,
    rate_from_discount_factor,
)


@pytest.fixture
def simple_convention() -> CompoundingConvention:
    return CompoundingConvention(
        compounding_type=CompoundingType.SIMPLE,
    )


@pytest.fixture
def annual_compounded_convention() -> CompoundingConvention:
    return CompoundingConvention(
        compounding_type=CompoundingType.COMPOUNDED,
        frequency=1,
    )


@pytest.fixture
def semiannual_compounded_convention() -> CompoundingConvention:
    return CompoundingConvention(
        compounding_type=CompoundingType.COMPOUNDED,
        frequency=2,
    )


@pytest.fixture
def continuous_convention() -> CompoundingConvention:
    return CompoundingConvention(
        compounding_type=CompoundingType.CONTINUOUS,
    )


def test_simple_discount_factor_known_case(
    simple_convention: CompoundingConvention,
) -> None:
    result = discount_factor_from_rate(
        rate=0.10,
        year_fraction=1.0,
        convention=simple_convention,
    )

    assert result == pytest.approx(1 / 1.10)


def test_annual_compounded_discount_factor_known_case(
    annual_compounded_convention: CompoundingConvention,
) -> None:
    result = discount_factor_from_rate(
        rate=0.10,
        year_fraction=2.0,
        convention=annual_compounded_convention,
    )

    assert result == pytest.approx(1 / (1.10**2))


def test_semiannual_compounded_discount_factor_known_case(
    semiannual_compounded_convention: CompoundingConvention,
) -> None:
    result = discount_factor_from_rate(
        rate=0.10,
        year_fraction=1.0,
        convention=semiannual_compounded_convention,
    )

    assert result == pytest.approx(1 / (1.05**2))


def test_continuous_discount_factor_known_case(
    continuous_convention: CompoundingConvention,
) -> None:
    result = discount_factor_from_rate(
        rate=0.10,
        year_fraction=1.0,
        convention=continuous_convention,
    )

    assert result == pytest.approx(math.exp(-0.10))


@pytest.mark.parametrize(
    ("convention", "rate"),
    [
        (
            CompoundingConvention(
                compounding_type=CompoundingType.SIMPLE,
            ),
            0.10,
        ),
        (
            CompoundingConvention(
                compounding_type=CompoundingType.COMPOUNDED,
                frequency=1,
            ),
            0.10,
        ),
        (
            CompoundingConvention(
                compounding_type=CompoundingType.COMPOUNDED,
                frequency=2,
            ),
            0.10,
        ),
        (
            CompoundingConvention(
                compounding_type=CompoundingType.CONTINUOUS,
            ),
            0.10,
        ),
    ],
)
def test_rate_discount_factor_round_trip(
    convention: CompoundingConvention,
    rate: float,
) -> None:
    discount_factor = discount_factor_from_rate(
        rate=rate,
        year_fraction=2.5,
        convention=convention,
    )

    recovered_rate = rate_from_discount_factor(
        discount_factor=discount_factor,
        year_fraction=2.5,
        convention=convention,
    )

    assert recovered_rate == pytest.approx(rate)


@pytest.mark.parametrize(
    "convention",
    [
        CompoundingConvention(
            compounding_type=CompoundingType.SIMPLE,
        ),
        CompoundingConvention(
            compounding_type=CompoundingType.COMPOUNDED,
            frequency=1,
        ),
        CompoundingConvention(
            compounding_type=CompoundingType.CONTINUOUS,
        ),
    ],
)
def test_zero_time_has_discount_factor_one(
    convention: CompoundingConvention,
) -> None:
    result = discount_factor_from_rate(
        rate=0.10,
        year_fraction=0.0,
        convention=convention,
    )

    assert result == 1.0


@pytest.mark.parametrize(
    "convention",
    [
        CompoundingConvention(
            compounding_type=CompoundingType.SIMPLE,
        ),
        CompoundingConvention(
            compounding_type=CompoundingType.COMPOUNDED,
            frequency=1,
        ),
        CompoundingConvention(
            compounding_type=CompoundingType.CONTINUOUS,
        ),
    ],
)
def test_zero_rate_has_discount_factor_one(
    convention: CompoundingConvention,
) -> None:
    result = discount_factor_from_rate(
        rate=0.0,
        year_fraction=5.0,
        convention=convention,
    )

    assert result == pytest.approx(1.0)


@pytest.mark.parametrize(
    "convention",
    [
        CompoundingConvention(
            compounding_type=CompoundingType.SIMPLE,
        ),
        CompoundingConvention(
            compounding_type=CompoundingType.COMPOUNDED,
            frequency=1,
        ),
        CompoundingConvention(
            compounding_type=CompoundingType.CONTINUOUS,
        ),
    ],
)
def test_negative_rate_is_supported_when_formula_is_valid(
    convention: CompoundingConvention,
) -> None:
    result = discount_factor_from_rate(
        rate=-0.01,
        year_fraction=1.0,
        convention=convention,
    )

    assert result > 1.0


def test_negative_year_fraction_is_rejected(
    annual_compounded_convention: CompoundingConvention,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than or equal to zero",
    ):
        discount_factor_from_rate(
            rate=0.10,
            year_fraction=-1.0,
            convention=annual_compounded_convention,
        )


def test_non_positive_discount_factor_is_rejected(
    annual_compounded_convention: CompoundingConvention,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        rate_from_discount_factor(
            discount_factor=0.0,
            year_fraction=1.0,
            convention=annual_compounded_convention,
        )


def test_rate_cannot_be_derived_at_zero_time(
    annual_compounded_convention: CompoundingConvention,
) -> None:
    with pytest.raises(
        ValueError,
        match="Year fraction must be greater than zero",
    ):
        rate_from_discount_factor(
            discount_factor=1.0,
            year_fraction=0.0,
            convention=annual_compounded_convention,
        )


def test_simple_compounding_rejects_non_positive_denominator(
    simple_convention: CompoundingConvention,
) -> None:
    with pytest.raises(
        ValueError,
        match="non-positive denominator",
    ):
        discount_factor_from_rate(
            rate=-1.0,
            year_fraction=1.0,
            convention=simple_convention,
        )


def test_compounded_rate_rejects_non_positive_base(
    annual_compounded_convention: CompoundingConvention,
) -> None:
    with pytest.raises(
        ValueError,
        match="positive compounding base",
    ):
        discount_factor_from_rate(
            rate=-1.0,
            year_fraction=1.0,
            convention=annual_compounded_convention,
        )
