from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MarketDataPoint(BaseModel):
    """Single normalized scalar market data observation."""

    model_config = ConfigDict(frozen=True)

    key: str = Field(min_length=1)
    value: float


class MarketDataNotFoundError(KeyError):
    """Raised when a requested market data key is unavailable."""


class MarketSnapshot(BaseModel):
    """Normalized market state for a single valuation date."""

    model_config = ConfigDict(frozen=True)

    as_of: date
    points: tuple[MarketDataPoint, ...] = ()

    @model_validator(mode="after")
    def validate_unique_keys(self) -> "MarketSnapshot":
        """Ensure each market data key appears only once."""
        keys = [point.key for point in self.points]

        if len(keys) != len(set(keys)):
            raise ValueError("Market data keys must be unique within a snapshot.")

        return self

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
