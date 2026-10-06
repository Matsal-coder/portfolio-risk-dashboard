from datetime import date
from pathlib import Path

import pytest

from portfolio_risk.market_data.snapshot import (
    MarketDataRowError,
    MarketDataSchemaError,
    SnapshotMarketDataProvider,
)


def write_csv(
    tmp_path: Path,
    content: str,
) -> Path:
    path = tmp_path / "market_snapshot.csv"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_valid_market_snapshot(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        ("as_of,key,value\n2026-09-30,PETR4,40.0\n2026-09-30,USD_BRL,5.30\n"),
    )

    snapshot = SnapshotMarketDataProvider(path).load()

    assert snapshot.as_of == date(2026, 9, 30)
    assert snapshot.get("PETR4") == 40.0
    assert snapshot.get("USD_BRL") == 5.30


def test_reject_missing_column(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        ("as_of,key\n2026-09-30,PETR4\n"),
    )

    with pytest.raises(
        MarketDataSchemaError,
        match="missing columns",
    ):
        SnapshotMarketDataProvider(path).load()


def test_reject_extra_column(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        ("as_of,key,value,source\n2026-09-30,PETR4,40.0,TEST\n"),
    )

    with pytest.raises(
        MarketDataSchemaError,
        match="unexpected columns",
    ):
        SnapshotMarketDataProvider(path).load()


def test_reject_multiple_as_of_dates(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        ("as_of,key,value\n2026-09-30,PETR4,40.0\n2026-10-01,USD_BRL,5.30\n"),
    )

    with pytest.raises(
        MarketDataSchemaError,
        match="exactly one as_of date",
    ):
        SnapshotMarketDataProvider(path).load()


def test_reject_invalid_as_of_date(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        ("as_of,key,value\nINVALID,PETR4,40.0\n"),
    )

    with pytest.raises(
        MarketDataSchemaError,
        match="Invalid as_of date",
    ):
        SnapshotMarketDataProvider(path).load()


def test_reject_duplicate_market_data_keys(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        ("as_of,key,value\n2026-09-30,PETR4,40.0\n2026-09-30,PETR4,41.0\n"),
    )

    with pytest.raises(
        MarketDataSchemaError,
        match="Market data keys must be unique",
    ):
        SnapshotMarketDataProvider(path).load()


def test_reject_invalid_market_data_value(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        ("as_of,key,value\n2026-09-30,PETR4,INVALID\n"),
    )

    with pytest.raises(
        MarketDataRowError,
        match="row 2",
    ):
        SnapshotMarketDataProvider(path).load()


def test_reject_empty_market_data_key(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        ("as_of,key,value\n2026-09-30,,40.0\n"),
    )

    with pytest.raises(
        MarketDataRowError,
        match="row 2",
    ):
        SnapshotMarketDataProvider(path).load()


def test_reject_headers_only(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        "as_of,key,value\n",
    )

    with pytest.raises(
        MarketDataSchemaError,
        match="contains no observations",
    ):
        SnapshotMarketDataProvider(path).load()


def test_reject_completely_empty_file(
    tmp_path: Path,
) -> None:
    path = write_csv(tmp_path, "")

    with pytest.raises(
        MarketDataSchemaError,
        match="Could not load market data CSV",
    ):
        SnapshotMarketDataProvider(path).load()


def test_reject_missing_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "does-not-exist.csv"

    with pytest.raises(
        MarketDataSchemaError,
        match="Could not load market data CSV",
    ):
        SnapshotMarketDataProvider(path).load()
