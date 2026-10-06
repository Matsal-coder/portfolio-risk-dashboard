import math

import pytest

from portfolio_risk.curves.interpolation import (
    log_linear_discount_factor,
)


def test_log_linear_discount_factor_returns_left_boundary() -> None:
    result = log_linear_discount_factor(
        target_time=1.0,
        left_time=1.0,
        left_discount_factor=0.95,
        right_time=2.0,
        right_discount_factor=0.85,
    )

    assert result == pytest.approx(0.95)


def test_log_linear_discount_factor_returns_right_boundary() -> None:
    result = log_linear_discount_factor(
        target_time=2.0,
        left_time=1.0,
        left_discount_factor=0.95,
        right_time=2.0,
        right_discount_factor=0.85,
    )

    assert result == pytest.approx(0.85)


def test_log_linear_discount_factor_midpoint() -> None:
    result = log_linear_discount_factor(
        target_time=1.5,
        left_time=1.0,
        left_discount_factor=0.95,
        right_time=2.0,
        right_discount_factor=0.85,
    )

    expected = math.sqrt(0.95 * 0.85)

    assert result == pytest.approx(expected)


def test_log_linear_discount_factor_rejects_invalid_bounds() -> None:
    with pytest.raises(
        ValueError,
        match="strictly less",
    ):
        log_linear_discount_factor(
            target_time=1.0,
            left_time=2.0,
            left_discount_factor=0.95,
            right_time=1.0,
            right_discount_factor=0.85,
        )


def test_log_linear_discount_factor_rejects_target_before_bounds() -> None:
    with pytest.raises(
        ValueError,
        match="between interpolation bounds",
    ):
        log_linear_discount_factor(
            target_time=0.5,
            left_time=1.0,
            left_discount_factor=0.95,
            right_time=2.0,
            right_discount_factor=0.85,
        )


def test_log_linear_discount_factor_rejects_target_after_bounds() -> None:
    with pytest.raises(
        ValueError,
        match="between interpolation bounds",
    ):
        log_linear_discount_factor(
            target_time=2.5,
            left_time=1.0,
            left_discount_factor=0.95,
            right_time=2.0,
            right_discount_factor=0.85,
        )


@pytest.mark.parametrize(
    ("left_df", "right_df"),
    [
        (0.0, 0.90),
        (-0.01, 0.90),
        (0.95, 0.0),
        (0.95, -0.01),
    ],
)
def test_log_linear_discount_factor_rejects_non_positive_discount_factors(
    left_df: float,
    right_df: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        log_linear_discount_factor(
            target_time=1.5,
            left_time=1.0,
            left_discount_factor=left_df,
            right_time=2.0,
            right_discount_factor=right_df,
        )
