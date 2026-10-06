from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator

from portfolio_risk.curves.interpolation import (
    InterpolationMethod,
    log_linear_discount_factor,
)
from portfolio_risk.financial.calendars import BusinessCalendar
from portfolio_risk.financial.compounding import CompoundingConvention
from portfolio_risk.financial.day_count import (
    DayCountConvention,
    year_fraction,
)
from portfolio_risk.financial.discounting import (
    discount_factor_from_rate,
    rate_from_discount_factor,
)


class CurveNode(BaseModel):
    """Single zero-rate node of a yield curve."""

    model_config = ConfigDict(frozen=True)

    maturity_date: date
    zero_rate: float


class YieldCurve(BaseModel):
    """Immutable zero-rate yield curve definition."""

    model_config = ConfigDict(frozen=True)

    as_of: date
    nodes: tuple[CurveNode, ...]
    day_count: DayCountConvention
    compounding: CompoundingConvention
    calendar: BusinessCalendar | None = None
    interpolation_method: InterpolationMethod = (
        InterpolationMethod.LOG_LINEAR_DISCOUNT_FACTOR
    )

    def forward_rate(
        self,
        start_date: date,
        end_date: date,
    ) -> float:
        """Return the implied forward rate between two dates."""
        if start_date < self.as_of:
            raise ValueError(
                "Forward start date cannot be before the curve as-of date."
            )

        if end_date <= start_date:
            raise ValueError("Forward end date must be after the start date.")

        start_discount_factor = self.discount_factor(start_date)
        end_discount_factor = self.discount_factor(end_date)

        forward_discount_factor = end_discount_factor / start_discount_factor

        forward_year_fraction = self._year_fraction(
            start_date,
            end_date,
        )

        if forward_year_fraction <= 0:
            raise ValueError("Forward period must have a positive year fraction.")

        return rate_from_discount_factor(
            discount_factor=forward_discount_factor,
            year_fraction=forward_year_fraction,
            convention=self.compounding,
        )

    @model_validator(mode="after")
    def validate_curve(self) -> "YieldCurve":
        """Validate structural and convention requirements."""
        if len(self.nodes) < 2:
            raise ValueError("Yield curve requires at least two nodes.")

        if any(node.maturity_date <= self.as_of for node in self.nodes):
            raise ValueError(
                "All curve node maturities must be after the curve as-of date."
            )

        maturity_dates = [node.maturity_date for node in self.nodes]

        if len(maturity_dates) != len(set(maturity_dates)):
            raise ValueError("Curve node maturities must be unique.")

        if self.day_count == DayCountConvention.BUS_252 and self.calendar is None:
            raise ValueError(
                "BUS/252 yield curves require an explicit business calendar."
            )

        ordered_nodes = tuple(
            sorted(
                self.nodes,
                key=lambda node: node.maturity_date,
            )
        )

        object.__setattr__(self, "nodes", ordered_nodes)

        return self

    def discount_factor(self, target_date: date) -> float:
        """Return the discount factor for a target date."""
        if target_date < self.as_of:
            raise ValueError("Target date cannot be before the curve as-of date.")

        if target_date == self.as_of:
            return 1.0

        exact_node = self._find_exact_node(target_date)

        if exact_node is not None:
            node_time = self._year_fraction(
                self.as_of,
                exact_node.maturity_date,
            )

            return discount_factor_from_rate(
                rate=exact_node.zero_rate,
                year_fraction=node_time,
                convention=self.compounding,
            )

        self._validate_interpolation_domain(target_date)

        left_node, right_node = self._surrounding_nodes(target_date)

        target_time = self._year_fraction(
            self.as_of,
            target_date,
        )
        left_time = self._year_fraction(
            self.as_of,
            left_node.maturity_date,
        )
        right_time = self._year_fraction(
            self.as_of,
            right_node.maturity_date,
        )

        left_discount_factor = discount_factor_from_rate(
            rate=left_node.zero_rate,
            year_fraction=left_time,
            convention=self.compounding,
        )
        right_discount_factor = discount_factor_from_rate(
            rate=right_node.zero_rate,
            year_fraction=right_time,
            convention=self.compounding,
        )

        if self.interpolation_method == InterpolationMethod.LOG_LINEAR_DISCOUNT_FACTOR:
            return log_linear_discount_factor(
                target_time=target_time,
                left_time=left_time,
                left_discount_factor=left_discount_factor,
                right_time=right_time,
                right_discount_factor=right_discount_factor,
            )

        raise ValueError(
            f"Unsupported interpolation method: {self.interpolation_method!r}"
        )

    def zero_rate(self, target_date: date) -> float:
        """Return the zero rate for a target date."""
        if target_date <= self.as_of:
            raise ValueError(
                "Zero rate requires a target date after the curve as-of date."
            )

        exact_node = self._find_exact_node(target_date)

        if exact_node is not None:
            return exact_node.zero_rate

        discount_factor = self.discount_factor(target_date)
        target_time = self._year_fraction(
            self.as_of,
            target_date,
        )

        return rate_from_discount_factor(
            discount_factor=discount_factor,
            year_fraction=target_time,
            convention=self.compounding,
        )

    def _find_exact_node(self, target_date: date) -> CurveNode | None:
        """Return an exact curve node when available."""
        for node in self.nodes:
            if node.maturity_date == target_date:
                return node

        return None

    def _validate_interpolation_domain(self, target_date: date) -> None:
        """Ensure a target date lies inside the curve interpolation domain."""
        first_maturity = self.nodes[0].maturity_date
        last_maturity = self.nodes[-1].maturity_date

        if target_date < first_maturity:
            raise ValueError(
                "Target date is before the first curve node; "
                "extrapolation is not supported."
            )

        if target_date > last_maturity:
            raise ValueError(
                "Target date is after the last curve node; "
                "extrapolation is not supported."
            )

    def _surrounding_nodes(
        self,
        target_date: date,
    ) -> tuple[CurveNode, CurveNode]:
        """Return curve nodes surrounding an interpolation target."""
        for left_node, right_node in zip(
            self.nodes,
            self.nodes[1:],
            strict=True,
        ):
            if left_node.maturity_date < target_date < right_node.maturity_date:
                return left_node, right_node

        raise ValueError(
            f"Could not locate interpolation bounds for {target_date.isoformat()}."
        )

    def _year_fraction(
        self,
        start_date: date,
        end_date: date,
    ) -> float:
        """Return a year fraction using the curve conventions."""
        return year_fraction(
            start_date=start_date,
            end_date=end_date,
            convention=self.day_count,
            calendar=self.calendar,
        )
