from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from portfolio_risk.curves.models import YieldCurve


class MarketDataPoint(BaseModel):
    """Single normalized scalar market data observation."""

    model_config = ConfigDict(frozen=True)

    key: str = Field(min_length=1)
    value: float


class CurveMarketData(BaseModel):
    """Named yield curve contained in a normalized market snapshot."""

    model_config = ConfigDict(frozen=True)

    key: str = Field(min_length=1)
    curve: YieldCurve


class MarketDataNotFoundError(KeyError):
    """Raised when a requested market data key is unavailable."""


class MarketSnapshot(BaseModel):
    """Normalized market state for a single valuation date."""

    model_config = ConfigDict(frozen=True)

    as_of: date
    points: tuple[MarketDataPoint, ...] = ()
    curves: tuple[CurveMarketData, ...] = ()

    @model_validator(mode="after")
    def validate_snapshot(self) -> "MarketSnapshot":
        """Validate market-data uniqueness and curve consistency."""
        point_keys = [point.key for point in self.points]

        if len(point_keys) != len(set(point_keys)):
            raise ValueError("Market data keys must be unique within a snapshot.")

        curve_keys = [curve_data.key for curve_data in self.curves]

        if len(curve_keys) != len(set(curve_keys)):
            raise ValueError("Curve keys must be unique within a snapshot.")

        if any(curve_data.curve.as_of != self.as_of for curve_data in self.curves):
            raise ValueError("All curves must share the market snapshot as-of date.")

        return self

    def contains_curve(self, key: str) -> bool:
        """Return whether the snapshot contains a curve key."""
        return any(curve_data.key == key for curve_data in self.curves)

    def get_curve(self, key: str) -> YieldCurve:
        """Return a yield curve by key."""
        for curve_data in self.curves:
            if curve_data.key == key:
                return curve_data.curve

        raise MarketDataNotFoundError(
            f"Curve key '{key}' is not available for snapshot {self.as_of.isoformat()}."
        )

    def contains(self, key: str) -> bool:
        """Return whether the snapshot contains a market data key."""
        return any(point.key == key for point in self.points)

    def get(self, key: str) -> float:
        """Return a scalar market data value.

        Raises:
            MarketDataNotFoundError:
                If the requested key is not available.
        """
        for point in self.points:
            if point.key == key:
                return point.value

        raise MarketDataNotFoundError(
            f"Market data key '{key}' is not available "
            f"for snapshot {self.as_of.isoformat()}."
        )


def with_curves(
    snapshot: MarketSnapshot,
    curves: tuple[CurveMarketData, ...],
) -> MarketSnapshot:
    """Return a market snapshot enriched with yield curves."""
    return MarketSnapshot(
        as_of=snapshot.as_of,
        points=snapshot.points,
        curves=curves,
    )
