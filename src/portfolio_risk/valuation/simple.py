from collections import defaultdict
from dataclasses import dataclass

from portfolio_risk.instruments.models import Instrument, InstrumentType
from portfolio_risk.instruments.registry import InstrumentRegistry
from portfolio_risk.portfolio.models import Portfolio, Position


class SimpleValuationError(ValueError):
    """Base error for simplified input valuation."""


class MissingInputPriceError(SimpleValuationError):
    """Raised when a supported position has no input price."""


class UnsupportedSimpleValuationError(SimpleValuationError):
    """Raised when simplified valuation is not defined for an instrument."""


SUPPORTED_INSTRUMENT_TYPES = {
    InstrumentType.EQUITY,
}


@dataclass(frozen=True)
class PortfolioValuationSummary:
    """Summary of simplified portfolio valuation coverage."""

    valued_positions: int
    unsupported_positions: int
    total_positions: int
    total_value: float
    value_by_book: dict[str, float]

    @property
    def coverage_ratio(self) -> float:
        """Return the fraction of positions successfully valued."""
        if self.total_positions == 0:
            return 1.0

        return self.valued_positions / self.total_positions


def calculate_simple_input_value(
    position: Position,
    instrument: Instrument,
) -> float:
    """Calculate simplified input value for supported instruments.

    This is not a general pricing function. It only implements conventions
    that are explicitly supported by the current educational foundation.
    """
    if instrument.instrument_type not in SUPPORTED_INSTRUMENT_TYPES:
        raise UnsupportedSimpleValuationError(
            f"Simple input valuation is not supported for "
            f"instrument type '{instrument.instrument_type.value}'."
        )

    if position.instrument_type != instrument.instrument_type:
        raise SimpleValuationError(
            f"Position type '{position.instrument_type.value}' does not match "
            f"instrument type '{instrument.instrument_type.value}' for "
            f"'{position.asset_id}'."
        )

    if position.asset_id != instrument.asset_id:
        raise SimpleValuationError(
            f"Position asset_id '{position.asset_id}' does not match "
            f"instrument asset_id '{instrument.asset_id}'."
        )

    if position.input_price is None:
        raise MissingInputPriceError(
            f"Position '{position.asset_id}' has no input price."
        )

    return position.quantity * position.input_price


def summarize_simple_portfolio_value(
    portfolio: Portfolio,
    registry: InstrumentRegistry,
) -> PortfolioValuationSummary:
    """Summarize simplified valuation without hiding unsupported positions."""
    total_value = 0.0
    valued_positions = 0
    unsupported_positions = 0
    value_by_book: defaultdict[str, float] = defaultdict(float)

    for position in portfolio.positions:
        instrument = registry.get(position.asset_id)

        try:
            value = calculate_simple_input_value(
                position=position,
                instrument=instrument,
            )
        except UnsupportedSimpleValuationError:
            unsupported_positions += 1
            continue

        total_value += value
        valued_positions += 1
        value_by_book[position.book] += value

    return PortfolioValuationSummary(
        valued_positions=valued_positions,
        unsupported_positions=unsupported_positions,
        total_positions=len(portfolio),
        total_value=total_value,
        value_by_book=dict(value_by_book),
    )
