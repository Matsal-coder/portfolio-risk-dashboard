from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class InstrumentType(StrEnum):
    """Supported instrument classifications."""

    LTN = "LTN"
    NTNF = "NTNF"
    LFT = "LFT"
    NTNB = "NTNB"

    DEB_PRE = "DEB_PRE"
    DEB_CDI = "DEB_CDI"
    DEB_IPCA = "DEB_IPCA"

    DI_FUTURE = "DI_FUTURE"
    FX_FUTURE = "FX_FUTURE"

    EQUITY = "EQUITY"
    EQUITY_OPTION = "EQUITY_OPTION"

    EVENT = "EVENT"


class Instrument(BaseModel):
    """Minimal representation of a financial instrument."""

    model_config = ConfigDict(frozen=True)

    asset_id: str = Field(min_length=1)
    instrument_type: InstrumentType
