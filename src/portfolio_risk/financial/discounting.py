import math

from portfolio_risk.financial.compounding import (
    CompoundingConvention,
    CompoundingType,
)


def discount_factor_from_rate(
    rate: float,
    year_fraction: float,
    convention: CompoundingConvention,
) -> float:
    """Convert an interest rate into a discount factor."""
    if year_fraction < 0:
        raise ValueError("Year fraction must be greater than or equal to zero.")

    if year_fraction == 0:
        return 1.0

    if convention.compounding_type == CompoundingType.SIMPLE:
        denominator = 1.0 + rate * year_fraction

        if denominator <= 0:
            raise ValueError("Simple compounding produced a non-positive denominator.")

        return 1.0 / denominator

    if convention.compounding_type == CompoundingType.COMPOUNDED:
        frequency = convention.frequency

        if frequency is None:
            raise ValueError("Compounded convention requires an explicit frequency.")

        base = 1.0 + rate / frequency

        if base <= 0:
            raise ValueError(
                "Compounded rate must produce a positive compounding base."
            )

        return base ** (-frequency * year_fraction)

    if convention.compounding_type == CompoundingType.CONTINUOUS:
        return math.exp(-rate * year_fraction)

    raise ValueError(f"Unsupported compounding type: {convention.compounding_type!r}")


def rate_from_discount_factor(
    discount_factor: float,
    year_fraction: float,
    convention: CompoundingConvention,
) -> float:
    """Convert a discount factor into an interest rate."""
    if discount_factor <= 0:
        raise ValueError("Discount factor must be greater than zero.")

    if year_fraction <= 0:
        raise ValueError(
            "Year fraction must be greater than zero when deriving a rate."
        )

    if convention.compounding_type == CompoundingType.SIMPLE:
        return (1.0 / discount_factor - 1.0) / year_fraction

    if convention.compounding_type == CompoundingType.COMPOUNDED:
        frequency = convention.frequency

        if frequency is None:
            raise ValueError("Compounded convention requires an explicit frequency.")

        exponent = -1.0 / (frequency * year_fraction)

        return frequency * (discount_factor**exponent - 1.0)

    if convention.compounding_type == CompoundingType.CONTINUOUS:
        return -math.log(discount_factor) / year_fraction

    raise ValueError(f"Unsupported compounding type: {convention.compounding_type!r}")
