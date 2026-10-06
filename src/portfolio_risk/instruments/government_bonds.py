from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GovernmentBondIndexer(StrEnum):
    """Supported government-bond indexation conventions."""

    NONE = "NONE"
    SELIC = "SELIC"
    IPCA = "IPCA"


class GovernmentBondTerms(BaseModel):
    """Shared contractual terms for Brazilian government bonds.

    This model contains contract state only. Market-dependent values
    such as yields, curves, current VNA, prices and sensitivities are
    intentionally excluded.
    """

    model_config = ConfigDict(frozen=True)

    maturity_date: date
    face_value: float = Field(gt=0)


class LTNTerms(GovernmentBondTerms):
    """Contractual definition of an LTN."""

    indexer: Literal[GovernmentBondIndexer.NONE] = GovernmentBondIndexer.NONE


class NTNFTerms(GovernmentBondTerms):
    """Contractual definition of an NTN-F."""

    coupon_rate: float = Field(gt=0)
    coupon_frequency_per_year: int = Field(gt=0)
    indexer: Literal[GovernmentBondIndexer.NONE] = GovernmentBondIndexer.NONE


class LFTTerms(GovernmentBondTerms):
    """Contractual definition of an LFT."""

    indexer: Literal[GovernmentBondIndexer.SELIC] = GovernmentBondIndexer.SELIC


class NTNBTerms(GovernmentBondTerms):
    """Contractual definition of an NTN-B."""

    coupon_rate: float = Field(ge=0)
    coupon_frequency_per_year: int = Field(gt=0)
    indexer: Literal[GovernmentBondIndexer.IPCA] = GovernmentBondIndexer.IPCA
