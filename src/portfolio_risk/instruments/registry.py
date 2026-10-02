from portfolio_risk.instruments.models import Instrument


class InstrumentAlreadyRegisteredError(ValueError):
    """Raised when attempting to register an existing asset_id."""


class InstrumentNotFoundError(KeyError):
    """Raised when an asset_id cannot be resolved by the registry."""


class InstrumentRegistry:
    """In-memory registry of financial instruments."""

    def __init__(self) -> None:
        self._instruments: dict[str, Instrument] = {}

    def register(self, instrument: Instrument) -> None:
        """Register a new instrument.

        Raises:
            InstrumentAlreadyRegisteredError:
                If the asset_id is already registered.
        """
        if instrument.asset_id in self._instruments:
            raise InstrumentAlreadyRegisteredError(
                f"Instrument '{instrument.asset_id}' is already registered."
            )

        self._instruments[instrument.asset_id] = instrument

    def get(self, asset_id: str) -> Instrument:
        """Return the instrument associated with an asset_id.

        Raises:
            InstrumentNotFoundError:
                If the asset_id is not registered.
        """
        try:
            return self._instruments[asset_id]
        except KeyError as exc:
            raise InstrumentNotFoundError(
                f"Instrument '{asset_id}' is not registered."
            ) from exc

    def contains(self, asset_id: str) -> bool:
        """Return whether an asset_id exists in the registry."""
        return asset_id in self._instruments

    def __len__(self) -> int:
        """Return the number of registered instruments."""
        return len(self._instruments)
