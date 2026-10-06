from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from portfolio_risk.curves.models import CurveNode, YieldCurve
from portfolio_risk.financial.compounding import (
    CompoundingConvention,
    CompoundingType,
)
from portfolio_risk.financial.day_count import DayCountConvention
from portfolio_risk.market_data.models import CurveMarketData

EXPECTED_CURVE_COLUMNS = {
    "as_of",
    "curve_key",
    "maturity_date",
    "zero_rate",
    "day_count",
    "compounding",
    "frequency",
}


class CurveSnapshotCsvError(ValueError):
    """Base error for invalid curve snapshot CSV inputs."""


class CurveSnapshotSchemaError(CurveSnapshotCsvError):
    """Raised when the curve snapshot CSV structure is invalid."""


class CurveSnapshotRowError(CurveSnapshotCsvError):
    """Raised when a curve snapshot CSV row is invalid."""


class CurveSnapshotProvider:
    """Load normalized yield curves from a local CSV snapshot."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> tuple[CurveMarketData, ...]:
        """Load and validate named yield curves from CSV."""
        try:
            dataframe = pd.read_csv(self._path)
        except (FileNotFoundError, pd.errors.EmptyDataError) as exc:
            raise CurveSnapshotSchemaError(
                f"Could not load curve snapshot CSV '{self._path}': {exc}"
            ) from exc

        self._validate_columns(dataframe)

        if dataframe.empty:
            raise CurveSnapshotSchemaError(
                f"Curve snapshot CSV '{self._path}' contains no observations."
            )

        as_of_values = dataframe["as_of"].dropna().unique()

        if len(as_of_values) != 1:
            raise CurveSnapshotSchemaError(
                "Curve snapshot must contain exactly one as_of date."
            )

        try:
            as_of = pd.to_datetime(as_of_values[0]).date()
        except (ValueError, TypeError) as exc:
            raise CurveSnapshotSchemaError(
                f"Invalid curve snapshot as_of date '{as_of_values[0]}'."
            ) from exc

        curves: list[CurveMarketData] = []

        for curve_key, group in dataframe.groupby("curve_key", sort=True):
            curves.append(
                self._build_curve_market_data(
                    curve_key=str(curve_key),
                    as_of=as_of,
                    group=group,
                )
            )

        return tuple(curves)

    def _build_curve_market_data(
        self,
        *,
        curve_key: str,
        as_of,
        group: pd.DataFrame,
    ) -> CurveMarketData:
        """Build one named curve from grouped CSV rows."""
        if not curve_key or curve_key == "nan":
            raise CurveSnapshotSchemaError(
                "Curve snapshot contains an empty curve_key."
            )

        day_count_values = group["day_count"].dropna().unique()
        compounding_values = group["compounding"].dropna().unique()
        frequency_values = group["frequency"].dropna().unique()

        if len(day_count_values) != 1:
            raise CurveSnapshotSchemaError(
                f"Curve '{curve_key}' must contain exactly one day-count convention."
            )

        if len(compounding_values) != 1:
            raise CurveSnapshotSchemaError(
                f"Curve '{curve_key}' must contain exactly one compounding convention."
            )

        try:
            day_count = DayCountConvention(day_count_values[0])
            compounding_type = CompoundingType(compounding_values[0])
        except ValueError as exc:
            raise CurveSnapshotSchemaError(
                f"Curve '{curve_key}' contains an unsupported convention."
            ) from exc

        frequency: int | None

        if compounding_type == CompoundingType.COMPOUNDED:
            if len(frequency_values) != 1:
                raise CurveSnapshotSchemaError(
                    f"""
                    Curve '{curve_key}' must contain 
                    exactly one compounding frequency.
                    """
                )

            try:
                frequency = int(frequency_values[0])
            except (ValueError, TypeError) as exc:
                raise CurveSnapshotSchemaError(
                    f"Curve '{curve_key}' contains an invalid compounding frequency."
                ) from exc
        else:
            frequency = None

        try:
            compounding = CompoundingConvention(
                compounding_type=compounding_type,
                frequency=frequency,
            )
        except ValidationError as exc:
            raise CurveSnapshotSchemaError(
                f"Invalid compounding convention for curve '{curve_key}': {exc}"
            ) from exc

        nodes: list[CurveNode] = []

        for index, row in group.iterrows():
            row_number = index + 2

            try:
                maturity_date = pd.to_datetime(row["maturity_date"]).date()

                node = CurveNode(
                    maturity_date=maturity_date,
                    zero_rate=row["zero_rate"],
                )
            except (ValidationError, ValueError, TypeError) as exc:
                raise CurveSnapshotRowError(
                    f"Invalid curve data at row {row_number}: {exc}"
                ) from exc

            nodes.append(node)

        try:
            curve = YieldCurve(
                as_of=as_of,
                nodes=tuple(nodes),
                day_count=day_count,
                compounding=compounding,
            )

            return CurveMarketData(
                key=curve_key,
                curve=curve,
            )
        except ValidationError as exc:
            raise CurveSnapshotSchemaError(
                f"Invalid yield curve '{curve_key}': {exc}"
            ) from exc

    @staticmethod
    def _validate_columns(dataframe: pd.DataFrame) -> None:
        """Validate the curve snapshot CSV column contract."""
        actual_columns = set(dataframe.columns)

        missing_columns = EXPECTED_CURVE_COLUMNS - actual_columns
        extra_columns = actual_columns - EXPECTED_CURVE_COLUMNS

        if missing_columns or extra_columns:
            problems: list[str] = []

            if missing_columns:
                problems.append(f"missing columns: {sorted(missing_columns)}")

            if extra_columns:
                problems.append(f"unexpected columns: {sorted(extra_columns)}")

            raise CurveSnapshotSchemaError(
                "Invalid curve snapshot CSV schema; " + "; ".join(problems) + "."
            )
