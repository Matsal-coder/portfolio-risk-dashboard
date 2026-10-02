from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from portfolio_risk.instruments.models import Instrument
from portfolio_risk.instruments.registry import (
    InstrumentAlreadyRegisteredError,
    InstrumentRegistry,
)

EXPECTED_COLUMNS = {
    "asset_id",
    "instrument_type",
}


class InstrumentCsvError(ValueError):
    """Base error for invalid instrument CSV inputs."""


class InstrumentSchemaError(InstrumentCsvError):
    """Raised when the instrument CSV structure is invalid."""


class InstrumentRowError(InstrumentCsvError):
    """Raised when an instrument CSV row is invalid."""


def load_instrument_registry(
    path: str | Path,
) -> InstrumentRegistry:
    """Load and validate an instrument registry from a CSV file.

    Args:
        path:
            Path to the instrument master CSV.

    Returns:
        A populated InstrumentRegistry.

    Raises:
        InstrumentSchemaError:
            If the CSV structure is invalid or contains no instruments.
        InstrumentRowError:
            If a row cannot be converted into a valid Instrument or contains
            a duplicated asset identifier.
    """
    csv_path = Path(path)

    try:
        dataframe = pd.read_csv(csv_path)
    except (FileNotFoundError, pd.errors.EmptyDataError) as exc:
        raise InstrumentSchemaError(
            f"Could not load instrument CSV '{csv_path}': {exc}"
        ) from exc

    _validate_columns(dataframe)

    if dataframe.empty:
        raise InstrumentSchemaError(
            f"Instrument CSV '{csv_path}' contains no instruments."
        )

    registry = InstrumentRegistry()

    for index, row in dataframe.iterrows():
        row_number = index + 2

        try:
            instrument = Instrument(
                asset_id=row["asset_id"],
                instrument_type=row["instrument_type"],
            )
        except ValidationError as exc:
            raise InstrumentRowError(
                f"Invalid instrument data at row {row_number}: {exc}"
            ) from exc

        try:
            registry.register(instrument)
        except InstrumentAlreadyRegisteredError as exc:
            raise InstrumentRowError(
                f"Row {row_number}: duplicate instrument '{instrument.asset_id}'."
            ) from exc

    return registry


def _validate_columns(dataframe: pd.DataFrame) -> None:
    """Validate the instrument CSV column contract."""
    actual_columns = set(dataframe.columns)

    missing_columns = EXPECTED_COLUMNS - actual_columns
    extra_columns = actual_columns - EXPECTED_COLUMNS

    if missing_columns or extra_columns:
        problems: list[str] = []

        if missing_columns:
            problems.append(f"missing columns: {sorted(missing_columns)}")

        if extra_columns:
            problems.append(f"unexpected columns: {sorted(extra_columns)}")

        raise InstrumentSchemaError(
            "Invalid instrument CSV schema; " + "; ".join(problems) + "."
        )
