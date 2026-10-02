from pathlib import Path

import pytest

from portfolio_risk.instruments.loader import (
    InstrumentRowError,
    InstrumentSchemaError,
    load_instrument_registry,
)
from portfolio_risk.instruments.models import InstrumentType


def write_csv(
    tmp_path: Path,
    content: str,
) -> Path:
    path = tmp_path / "instruments.csv"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_valid_instrument_registry(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        ("asset_id,instrument_type\nPETR4,EQUITY\nLTN_2027,LTN\n"),
    )

    registry = load_instrument_registry(path)

    assert len(registry) == 2
    assert registry.get("PETR4").instrument_type == InstrumentType.EQUITY
    assert registry.get("LTN_2027").instrument_type == InstrumentType.LTN


def test_reject_missing_column(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        ("asset_id\nPETR4\n"),
    )

    with pytest.raises(
        InstrumentSchemaError,
        match="missing columns",
    ):
        load_instrument_registry(path)


def test_reject_extra_column(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        ("asset_id,instrument_type,issuer\nPETR4,EQUITY,Petrobras\n"),
    )

    with pytest.raises(
        InstrumentSchemaError,
        match="unexpected columns",
    ):
        load_instrument_registry(path)


def test_reject_invalid_instrument_type(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        ("asset_id,instrument_type\nPETR4,INVALID\n"),
    )

    with pytest.raises(
        InstrumentRowError,
        match="row 2",
    ):
        load_instrument_registry(path)


def test_reject_empty_asset_id(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        ("asset_id,instrument_type\n,EQUITY\n"),
    )

    with pytest.raises(
        InstrumentRowError,
        match="row 2",
    ):
        load_instrument_registry(path)


def test_reject_duplicate_asset_id(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        ("asset_id,instrument_type\nPETR4,EQUITY\nPETR4,EQUITY\n"),
    )

    with pytest.raises(
        InstrumentRowError,
        match="duplicate instrument 'PETR4'",
    ):
        load_instrument_registry(path)


def test_reject_csv_with_headers_only(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        "asset_id,instrument_type\n",
    )

    with pytest.raises(
        InstrumentSchemaError,
        match="contains no instruments",
    ):
        load_instrument_registry(path)


def test_reject_completely_empty_file(
    tmp_path: Path,
) -> None:
    path = write_csv(tmp_path, "")

    with pytest.raises(
        InstrumentSchemaError,
        match="Could not load instrument CSV",
    ):
        load_instrument_registry(path)


def test_reject_missing_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "does-not-exist.csv"

    with pytest.raises(
        InstrumentSchemaError,
        match="Could not load instrument CSV",
    ):
        load_instrument_registry(path)
