from collections import defaultdict

from pydantic import BaseModel, ConfigDict, Field

from portfolio_risk.instruments.models import InstrumentType


class Position(BaseModel):
    """A portfolio position in a financial instrument."""

    model_config = ConfigDict(frozen=True)

    asset_id: str = Field(min_length=1)
    instrument_type: InstrumentType
    book: str = Field(min_length=1)
    quantity: float
    input_price: float | None = Field(default=None, ge=0)


class Portfolio(BaseModel):
    """Collection of financial positions."""

    model_config = ConfigDict(frozen=True)

    positions: tuple[Position, ...] = ()

    def __len__(self) -> int:
        """Return the number of positions in the portfolio."""
        return len(self.positions)

    def books(self) -> set[str]:
        """Return the books represented in the portfolio."""
        return {position.book for position in self.positions}

    def instrument_types(self) -> set[InstrumentType]:
        """Return the instrument types represented in the portfolio."""
        return {position.instrument_type for position in self.positions}

    def positions_by_book(self) -> dict[str, tuple[Position, ...]]:
        """Group positions by book."""
        grouped: defaultdict[str, list[Position]] = defaultdict(list)

        for position in self.positions:
            grouped[position.book].append(position)

        return {book: tuple(book_positions) for book, book_positions in grouped.items()}

    def positions_by_instrument_type(
        self,
    ) -> dict[InstrumentType, tuple[Position, ...]]:
        """Group positions by instrument type."""
        grouped: defaultdict[InstrumentType, list[Position]] = defaultdict(list)

        for position in self.positions:
            grouped[position.instrument_type].append(position)

        return {
            instrument_type: tuple(type_positions)
            for instrument_type, type_positions in grouped.items()
        }
