from datetime import date
from pathlib import Path

import pytest

from portfolio_risk.market_data.curves import (
    CurveSnapshotProvider,
    CurveSnapshotRowError,
    CurveSnapshotSchemaError,
)


def write_curve_csv(
    tmp_path: Path,
    content: str,
) -> Path:
    path = tmp_path / "curve_snapshot.csv"
    path.write_text(content, encoding="utf-8")
    return path


def valid_curve_csv() -> str:
    return (
        "as_of,curve_key,maturity_date,zero_rate,"
        "day_count,compounding,frequency\n"
        "2026-09-30,BRL_NOMINAL,2027-09-30,0.1200,"
        "ACT/365,COMPOUNDED,1\n"
        "2026-09-30,BRL_NOMINAL,2028-09-30,0.1180,"
        "ACT/365,COMPOUNDED,1\n"
    )


def test_load_valid_curve_snapshot(
    tmp_path: Path,
) -> None:
    path = write_curve_csv(
        tmp_path,
        valid_curve_csv(),
    )

    curves = CurveSnapshotProvider(path).load()

    assert len(curves) == 1
    assert curves[0].key == "BRL_NOMINAL"
    assert curves[0].curve.as_of == date(2026, 9, 30)
    assert len(curves[0].curve.nodes) == 2


def test_load_multiple_curves(
    tmp_path: Path,
) -> None:
    path = write_curve_csv(
        tmp_path,
        (
            "as_of,curve_key,maturity_date,zero_rate,"
            "day_count,compounding,frequency\n"
            "2026-09-30,BRL_NOMINAL,2027-09-30,0.1200,"
            "ACT/365,COMPOUNDED,1\n"
            "2026-09-30,BRL_NOMINAL,2028-09-30,0.1180,"
            "ACT/365,COMPOUNDED,1\n"
            "2026-09-30,BRL_REAL,2027-09-30,0.0600,"
            "ACT/365,COMPOUNDED,1\n"
            "2026-09-30,BRL_REAL,2028-09-30,0.0580,"
            "ACT/365,COMPOUNDED,1\n"
        ),
    )

    curves = CurveSnapshotProvider(path).load()

    assert [curve.key for curve in curves] == [
        "BRL_NOMINAL",
        "BRL_REAL",
    ]


def test_reject_missing_curve_column(
    tmp_path: Path,
) -> None:
    path = write_curve_csv(
        tmp_path,
        (
            "as_of,curve_key,maturity_date,zero_rate,"
            "day_count,compounding\n"
            "2026-09-30,BRL_NOMINAL,2027-09-30,0.12,"
            "ACT/365,COMPOUNDED\n"
        ),
    )

    with pytest.raises(
        CurveSnapshotSchemaError,
        match="missing columns",
    ):
        CurveSnapshotProvider(path).load()


def test_reject_multiple_curve_as_of_dates(
    tmp_path: Path,
) -> None:
    path = write_curve_csv(
        tmp_path,
        (
            "as_of,curve_key,maturity_date,zero_rate,"
            "day_count,compounding,frequency\n"
            "2026-09-30,BRL_NOMINAL,2027-09-30,0.12,"
            "ACT/365,COMPOUNDED,1\n"
            "2026-10-01,BRL_NOMINAL,2028-09-30,0.11,"
            "ACT/365,COMPOUNDED,1\n"
        ),
    )

    with pytest.raises(
        CurveSnapshotSchemaError,
        match="exactly one as_of date",
    ):
        CurveSnapshotProvider(path).load()


def test_reject_invalid_maturity_date(
    tmp_path: Path,
) -> None:
    path = write_curve_csv(
        tmp_path,
        (
            "as_of,curve_key,maturity_date,zero_rate,"
            "day_count,compounding,frequency\n"
            "2026-09-30,BRL_NOMINAL,INVALID,0.12,"
            "ACT/365,COMPOUNDED,1\n"
            "2026-09-30,BRL_NOMINAL,2028-09-30,0.11,"
            "ACT/365,COMPOUNDED,1\n"
        ),
    )

    with pytest.raises(
        CurveSnapshotRowError,
        match="row 2",
    ):
        CurveSnapshotProvider(path).load()


def test_reject_invalid_zero_rate(
    tmp_path: Path,
) -> None:
    path = write_curve_csv(
        tmp_path,
        (
            "as_of,curve_key,maturity_date,zero_rate,"
            "day_count,compounding,frequency\n"
            "2026-09-30,BRL_NOMINAL,2027-09-30,INVALID,"
            "ACT/365,COMPOUNDED,1\n"
            "2026-09-30,BRL_NOMINAL,2028-09-30,0.11,"
            "ACT/365,COMPOUNDED,1\n"
        ),
    )

    with pytest.raises(
        CurveSnapshotRowError,
        match="row 2",
    ):
        CurveSnapshotProvider(path).load()


def test_reject_inconsistent_day_count(
    tmp_path: Path,
) -> None:
    path = write_curve_csv(
        tmp_path,
        (
            "as_of,curve_key,maturity_date,zero_rate,"
            "day_count,compounding,frequency\n"
            "2026-09-30,BRL_NOMINAL,2027-09-30,0.12,"
            "ACT/365,COMPOUNDED,1\n"
            "2026-09-30,BRL_NOMINAL,2028-09-30,0.11,"
            "ACT/360,COMPOUNDED,1\n"
        ),
    )

    with pytest.raises(
        CurveSnapshotSchemaError,
        match="exactly one day-count convention",
    ):
        CurveSnapshotProvider(path).load()


def test_reject_inconsistent_compounding(
    tmp_path: Path,
) -> None:
    path = write_curve_csv(
        tmp_path,
        (
            "as_of,curve_key,maturity_date,zero_rate,"
            "day_count,compounding,frequency\n"
            "2026-09-30,BRL_NOMINAL,2027-09-30,0.12,"
            "ACT/365,COMPOUNDED,1\n"
            "2026-09-30,BRL_NOMINAL,2028-09-30,0.11,"
            "ACT/365,CONTINUOUS,\n"
        ),
    )

    with pytest.raises(
        CurveSnapshotSchemaError,
        match="exactly one compounding convention",
    ):
        CurveSnapshotProvider(path).load()


def test_reject_curve_with_single_node(
    tmp_path: Path,
) -> None:
    path = write_curve_csv(
        tmp_path,
        (
            "as_of,curve_key,maturity_date,zero_rate,"
            "day_count,compounding,frequency\n"
            "2026-09-30,BRL_NOMINAL,2027-09-30,0.12,"
            "ACT/365,COMPOUNDED,1\n"
        ),
    )

    with pytest.raises(
        CurveSnapshotSchemaError,
        match="at least two nodes",
    ):
        CurveSnapshotProvider(path).load()


def test_reject_missing_curve_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "does-not-exist.csv"

    with pytest.raises(
        CurveSnapshotSchemaError,
        match="Could not load curve snapshot CSV",
    ):
        CurveSnapshotProvider(path).load()
