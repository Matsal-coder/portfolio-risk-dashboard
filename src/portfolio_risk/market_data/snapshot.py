from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from portfolio_risk.market_data.models import MarketDataPoint, MarketSnapshot

EXPECTED_COLUMNS = {
    "as_of",
    "key",
    "value",
}


class MarketDataCsvError(ValueError):
    """Base error for invalid market data CSV inputs."""


class MarketDataSchemaError(MarketDataCsvError):
    """Raised when the market data CSV structure is invalid."""


class MarketDataRowError(MarketDataCsvError):
    """Raised when a market data CSV row is invalid."""


class SnapshotMarketDataProvider:
    """Load normalized market data from a local CSV snapshot."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> MarketSnapshot:
        """Load and validate a market snapshot from CSV."""
        try:
            dataframe = pd.read_csv(self._path)
        except (FileNotFoundError, pd.errors.EmptyDataError) as exc:
            raise MarketDataSchemaError(
                f"Could not load market data CSV '{self._path}': {exc}"
            ) from exc

        self._validate_columns(dataframe)

        if dataframe.empty:
            raise MarketDataSchemaError(
                f"Market data CSV '{self._path}' contains no observations."
            )

        as_of_values = dataframe["as_of"].dropna().unique()

        if len(as_of_values) != 1:
            raise MarketDataSchemaError(
                "Market data snapshot must contain exactly one as_of date."
            )

        try:
            as_of = pd.to_datetime(as_of_values[0]).date()
        except (ValueError, TypeError) as exc:
            raise MarketDataSchemaError(
                f"Invalid as_of date '{as_of_values[0]}'."
            ) from exc

        points: list[MarketDataPoint] = []

        for index, row in dataframe.iterrows():
            row_number = index + 2

            try:
                point = MarketDataPoint(
                    key=row["key"],
                    value=row["value"],
                )
            except ValidationError as exc:
                raise MarketDataRowError(
                    f"Invalid market data at row {row_number}: {exc}"
                ) from exc

            points.append(point)

        try:
            return MarketSnapshot(
                as_of=as_of,
                points=tuple(points),
            )
        except ValidationError as exc:
            raise MarketDataSchemaError(f"Invalid market data snapshot: {exc}") from exc

    @staticmethod
    def _validate_columns(dataframe: pd.DataFrame) -> None:
        """Validate the market data CSV column contract."""
        actual_columns = set(dataframe.columns)

        missing_columns = EXPECTED_COLUMNS - actual_columns
        extra_columns = actual_columns - EXPECTED_COLUMNS

        if missing_columns or extra_columns:
            problems: list[str] = []

            if missing_columns:
                problems.append(f"missing columns: {sorted(missing_columns)}")

            if extra_columns:
                problems.append(f"unexpected columns: {sorted(extra_columns)}")

            raise MarketDataSchemaError(
                "Invalid market data CSV schema; " + "; ".join(problems) + "."
            )
