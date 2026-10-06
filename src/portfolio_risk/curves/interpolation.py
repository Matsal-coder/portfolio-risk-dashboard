import math
from enum import StrEnum


class InterpolationMethod(StrEnum):
    """Supported yield-curve interpolation methods."""

    LOG_LINEAR_DISCOUNT_FACTOR = "LOG_LINEAR_DISCOUNT_FACTOR"


def log_linear_discount_factor(
    target_time: float,
    left_time: float,
    left_discount_factor: float,
    right_time: float,
    right_discount_factor: float,
) -> float:
    """Interpolate a discount factor linearly in log-discount-factor space."""
    if left_time >= right_time:
        raise ValueError("Left time must be strictly less than right time.")

    if target_time < left_time or target_time > right_time:
        raise ValueError("Target time must lie between interpolation bounds.")

    if left_discount_factor <= 0 or right_discount_factor <= 0:
        raise ValueError("Discount factors must be greater than zero.")

    if target_time == left_time:
        return left_discount_factor

    if target_time == right_time:
        return right_discount_factor

    weight = (target_time - left_time) / (right_time - left_time)

    left_log_df = math.log(left_discount_factor)
    right_log_df = math.log(right_discount_factor)

    interpolated_log_df = left_log_df + weight * (right_log_df - left_log_df)

    return math.exp(interpolated_log_df)
