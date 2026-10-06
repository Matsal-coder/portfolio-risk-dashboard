from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator


class CompoundingType(StrEnum):
    """Supported interest-rate compounding conventions."""

    SIMPLE = "SIMPLE"
    COMPOUNDED = "COMPOUNDED"
    CONTINUOUS = "CONTINUOUS"


class CompoundingConvention(BaseModel):
    """Explicit compounding convention for interest-rate calculations."""

    model_config = ConfigDict(frozen=True)

    compounding_type: CompoundingType
    frequency: int | None = None

    @model_validator(mode="after")
    def validate_frequency(self) -> "CompoundingConvention":
        """Validate whether frequency is consistent with the convention."""
        if self.compounding_type == CompoundingType.COMPOUNDED:
            if self.frequency is None:
                raise ValueError(
                    "Compounded convention requires an explicit frequency."
                )

            if self.frequency <= 0:
                raise ValueError("Compounding frequency must be greater than zero.")

            return self

        if self.frequency is not None:
            raise ValueError("Frequency is only valid for compounded conventions.")

        return self
