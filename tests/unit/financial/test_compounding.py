import pytest
from pydantic import ValidationError

from portfolio_risk.financial.compounding import (
    CompoundingConvention,
    CompoundingType,
)


def test_simple_compounding_does_not_require_frequency() -> None:
    convention = CompoundingConvention(
        compounding_type=CompoundingType.SIMPLE,
    )

    assert convention.frequency is None


def test_continuous_compounding_does_not_require_frequency() -> None:
    convention = CompoundingConvention(
        compounding_type=CompoundingType.CONTINUOUS,
    )

    assert convention.frequency is None


def test_compounded_convention_requires_frequency() -> None:
    with pytest.raises(
        ValidationError,
        match="requires an explicit frequency",
    ):
        CompoundingConvention(
            compounding_type=CompoundingType.COMPOUNDED,
        )


def test_compounded_convention_accepts_positive_frequency() -> None:
    convention = CompoundingConvention(
        compounding_type=CompoundingType.COMPOUNDED,
        frequency=2,
    )

    assert convention.frequency == 2


def test_compounded_convention_rejects_zero_frequency() -> None:
    with pytest.raises(
        ValidationError,
        match="must be greater than zero",
    ):
        CompoundingConvention(
            compounding_type=CompoundingType.COMPOUNDED,
            frequency=0,
        )


def test_simple_compounding_rejects_frequency() -> None:
    with pytest.raises(
        ValidationError,
        match="Frequency is only valid",
    ):
        CompoundingConvention(
            compounding_type=CompoundingType.SIMPLE,
            frequency=1,
        )


def test_continuous_compounding_rejects_frequency() -> None:
    with pytest.raises(
        ValidationError,
        match="Frequency is only valid",
    ):
        CompoundingConvention(
            compounding_type=CompoundingType.CONTINUOUS,
            frequency=1,
        )
