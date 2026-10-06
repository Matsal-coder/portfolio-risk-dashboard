from pathlib import Path

from portfolio_risk.config.settings import Settings


def test_default_paths_are_derived_from_project_root(
    tmp_path: Path,
) -> None:
    settings = Settings(project_root=tmp_path)

    assert settings.instrument_path == (
        tmp_path / "data" / "instruments" / "instruments.csv"
    )
    assert settings.portfolio_path == (
        tmp_path / "data" / "portfolio" / "portfolio.csv"
    )
    assert settings.market_path == (
        tmp_path / "data" / "market" / "market_snapshot.csv"
    )
