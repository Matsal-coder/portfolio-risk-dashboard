from datetime import timedelta

import pandas as pd
import streamlit as st

from portfolio_risk.application.bootstrap import (
    ProjectState,
    load_project_state,
)
from portfolio_risk.config.logging import configure_logging
from portfolio_risk.config.settings import settings
from portfolio_risk.curves.models import YieldCurve


def build_positions_dataframe(state: ProjectState) -> pd.DataFrame:
    """Build a presentation table from portfolio positions."""
    portfolio = state.portfolio

    return pd.DataFrame(
        [
            {
                "Asset ID": position.asset_id,
                "Instrument Type": position.instrument_type.value,
                "Book": position.book,
                "Quantity": position.quantity,
                "Input Price": position.input_price,
            }
            for position in portfolio.positions
        ]
    )


def build_market_dataframe(state: ProjectState) -> pd.DataFrame:
    """Build a presentation table from normalized market data."""
    market = state.market

    return pd.DataFrame(
        [
            {
                "Key": point.key,
                "Value": point.value,
            }
            for point in market.points
        ]
    )


def render_dashboard() -> None:
    """Render the Portfolio / Market Data dashboard page."""
    st.set_page_config(
        page_title="Portfolio Risk Dashboard",
        page_icon="📊",
        layout="wide",
    )

    configure_logging()

    st.title("Portfolio Risk Dashboard")
    st.caption("Block 1 — Financial Conventions / Yield Curves")

    try:
        state = load_project_state(
            instrument_path=settings.instrument_path,
            portfolio_path=settings.portfolio_path,
            market_path=settings.market_path,
            curve_path=settings.curve_path,
        )
    except Exception as exc:
        st.error(f"Could not load project state: {exc}")
        st.stop()

    st.header("Portfolio")

    portfolio_col_1, portfolio_col_2, portfolio_col_3 = st.columns(3)

    portfolio_col_1.metric(
        "Positions",
        len(state.portfolio),
    )
    portfolio_col_2.metric(
        "Books",
        len(state.portfolio.books()),
    )
    portfolio_col_3.metric(
        "Instrument Types",
        len(state.portfolio.instrument_types()),
    )

    st.dataframe(
        build_positions_dataframe(state),
        use_container_width=True,
        hide_index=True,
    )

    st.header("Simple Valuation")

    coverage_percent = state.valuation.coverage_ratio * 100

    valuation_col_1, valuation_col_2, valuation_col_3, valuation_col_4 = st.columns(4)

    valuation_col_1.metric(
        "Valued Positions",
        state.valuation.valued_positions,
    )
    valuation_col_2.metric(
        "Unsupported Positions",
        state.valuation.unsupported_positions,
    )
    valuation_col_3.metric(
        "Coverage",
        f"{coverage_percent:.1f}%",
    )
    valuation_col_4.metric(
        "Supported Simple Value",
        f"{state.valuation.total_value:,.2f}",
    )

    if state.valuation.coverage_ratio < 1.0:
        st.warning(
            "Simple valuation does not cover the entire portfolio. "
            "The displayed value is only the sum of explicitly supported "
            "instrument conventions."
        )

    if state.valuation.value_by_book:
        value_by_book = pd.DataFrame(
            [
                {
                    "Book": book,
                    "Supported Simple Value": value,
                }
                for book, value in state.valuation.value_by_book.items()
            ]
        )

        st.subheader("Supported value by book")
        st.dataframe(
            value_by_book,
            use_container_width=True,
            hide_index=True,
        )

    st.header("Market Data")

    market_col_1, market_col_2 = st.columns(2)

    market_col_1.metric(
        "As Of",
        state.market.as_of.isoformat(),
    )
    market_col_2.metric(
        "Observations",
        len(state.market.points),
    )

    st.dataframe(
        build_market_dataframe(state),
        use_container_width=True,
        hide_index=True,
    )

    st.header("Curve Explorer")

    if not state.market.curves:
        st.info("No yield curves are available in the market snapshot.")
        return

    curve_keys = [curve_data.key for curve_data in state.market.curves]

    selected_curve_key = st.selectbox(
        "Curve",
        options=curve_keys,
    )

    curve = state.market.get_curve(selected_curve_key)

    curve_col_1, curve_col_2, curve_col_3 = st.columns(3)

    curve_col_1.metric(
        "As Of",
        curve.as_of.isoformat(),
    )

    curve_col_2.metric(
        "Day Count",
        curve.day_count.value,
    )

    compounding_label = curve.compounding.compounding_type.value

    if curve.compounding.frequency is not None:
        compounding_label += f" ({curve.compounding.frequency}x/year)"

    curve_col_3.metric(
        "Compounding",
        compounding_label,
    )

    st.subheader("Curve Nodes")

    node_dataframe = build_curve_nodes_dataframe(curve)

    st.dataframe(
        node_dataframe[
            [
                "Maturity",
                "Zero Rate (%)",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Maturity": st.column_config.DateColumn(
                "Maturity",
                format="DD/MM/YYYY",
            ),
            "Zero Rate (%)": st.column_config.NumberColumn(
                "Zero Rate (%)",
                format="%.4f",
            ),
        },
    )

    parallel_shift_bps = st.number_input(
        "Parallel Shift (bps)",
        min_value=-1000,
        max_value=1000,
        value=0,
        step=25,
    )

    shifted_curve = curve.parallel_shift_bps(float(parallel_shift_bps))

    chart_dataframe = build_curve_chart_dataframe(
        curve,
        shifted_curve=shifted_curve,
    )

    chart_dataframe = chart_dataframe.set_index("Date")

    st.subheader("Base vs Shifted Curve")

    st.line_chart(
        chart_dataframe,
        use_container_width=True,
    )


def build_curve_nodes_dataframe(curve: YieldCurve) -> pd.DataFrame:
    """Build a presentation table from yield-curve nodes."""
    return pd.DataFrame(
        [
            {
                "Maturity": node.maturity_date,
                "Zero Rate": node.zero_rate,
                "Zero Rate (%)": node.zero_rate * 100,
            }
            for node in curve.nodes
        ]
    )


def build_curve_chart_dataframe(
    curve: YieldCurve,
    *,
    shifted_curve: YieldCurve | None = None,
    number_of_points: int = 50,
) -> pd.DataFrame:
    """Build presentation data for base and optionally shifted curves."""
    first_date = curve.nodes[0].maturity_date
    last_date = curve.nodes[-1].maturity_date

    total_days = (last_date - first_date).days

    if number_of_points < 2:
        raise ValueError("Curve chart requires at least two points.")

    dates = sorted(
        {
            first_date
            + timedelta(days=round(total_days * index / (number_of_points - 1)))
            for index in range(number_of_points)
        }
    )

    data = []

    for target_date in dates:
        row = {
            "Date": target_date,
            "Base Curve": curve.zero_rate(target_date) * 100,
        }

        if shifted_curve is not None:
            row["Shifted Curve"] = shifted_curve.zero_rate(target_date) * 100

        data.append(row)

    return pd.DataFrame(data)


if __name__ == "__main__":
    render_dashboard()
