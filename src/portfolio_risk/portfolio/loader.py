from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from portfolio_risk.instruments.registry import (
    InstrumentNotFoundError,
    InstrumentRegistry,
)
from portfolio_risk.portfolio.models import Portfolio, Position

EXPECTED_COLUMNS = {
    "asset_id",
    "instrument_type",
    "book",
    "quantity",
    "price",
}


class PortfolioCsvError(ValueError):
    """Base error for invalid portfolio CSV inputs."""


class PortfolioSchemaError(PortfolioCsvError):
    """Raised when the portfolio CSV structure is invalid."""


class PortfolioRowError(PortfolioCsvError):
    """Raised when a portfolio CSV row is invalid."""


class InstrumentTypeMismatchError(PortfolioCsvError):
    """Raised when portfolio and registry instrument types disagree."""


def load_portfolio_csv(
    path: str | Path,
    registry: InstrumentRegistry,
) -> Portfolio:
    """Load and validate a portfolio from a CSV file.

    Args:
        path:
            Path to the portfolio CSV.
        registry:
            Instrument registry used to validate asset identifiers and types.

    Returns:
        A validated Portfolio.

    Raises:
        PortfolioSchemaError:
            If the CSV structure is invalid or contains no positions.
        PortfolioRowError:
            If a row cannot be converted into a valid Position or references
            an unknown instrument.
        InstrumentTypeMismatchError:
            If the instrument type in the CSV disagrees with the registry.
    """
    csv_path = Path(path)

    try:
        dataframe = pd.read_csv(csv_path)
    except (FileNotFoundError, pd.errors.EmptyDataError) as exc:
        raise PortfolioSchemaError(
            f"Could not load portfolio CSV '{csv_path}': {exc}"
        ) from exc

    _validate_columns(dataframe)

    if dataframe.empty:
        raise PortfolioSchemaError(f"Portfolio CSV '{csv_path}' contains no positions.")

    positions = tuple(
        _position_from_row(
            row=row,
            row_number=index + 2,
            registry=registry,
        )
        for index, row in dataframe.iterrows()
    )

    return Portfolio(positions=positions)


def _validate_columns(dataframe: pd.DataFrame) -> None:
    """Validate the portfolio CSV column contract."""
    actual_columns = set(dataframe.columns)

    missing_columns = EXPECTED_COLUMNS - actual_columns
    extra_columns = actual_columns - EXPECTED_COLUMNS

    if missing_columns or extra_columns:
        problems: list[str] = []

        if missing_columns:
            problems.append(f"missing columns: {sorted(missing_columns)}")

        if extra_columns:
            problems.append(f"unexpected columns: {sorted(extra_columns)}")

        raise PortfolioSchemaError(
            "Invalid portfolio CSV schema; " + "; ".join(problems) + "."
        )


def _position_from_row(
    row: pd.Series,
    row_number: int,
    registry: InstrumentRegistry,
) -> Position:
    """Convert one CSV row into a validated Position."""
    input_price = None if pd.isna(row["price"]) else row["price"]

    try:
        position = Position(
            asset_id=row["asset_id"],
            instrument_type=row["instrument_type"],
            book=row["book"],
            quantity=row["quantity"],
            input_price=input_price,
        )
    except ValidationError as exc:
        raise PortfolioRowError(
            f"Invalid portfolio data at row {row_number}: {exc}"
        ) from exc

    try:
        instrument = registry.get(position.asset_id)
    except InstrumentNotFoundError as exc:
        raise PortfolioRowError(
            f"Row {row_number}: instrument '{position.asset_id}' is not registered."
        ) from exc

    if instrument.instrument_type != position.instrument_type:
        raise InstrumentTypeMismatchError(
            f"Row {row_number}: instrument type mismatch for "
            f"'{position.asset_id}': portfolio contains "
            f"'{position.instrument_type.value}', registry contains "
            f"'{instrument.instrument_type.value}'."
        )

    return position
