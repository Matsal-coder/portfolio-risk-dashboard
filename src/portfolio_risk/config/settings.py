from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration."""

    model_config = SettingsConfigDict(
        env_prefix="PORTFOLIO_RISK_",
        env_file=".env",
        extra="ignore",
    )

    project_root: Path = Path(__file__).resolve().parents[3]

    @computed_field
    @property
    def instrument_path(self) -> Path:
        return self.project_root / "data" / "instruments" / "instruments.csv"

    @computed_field
    @property
    def portfolio_path(self) -> Path:
        return self.project_root / "data" / "portfolio" / "portfolio.csv"

    @computed_field
    @property
    def market_path(self) -> Path:
        return self.project_root / "data" / "market" / "market_snapshot.csv"


settings = Settings()
