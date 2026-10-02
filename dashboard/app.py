from pathlib import Path

import pandas as pd
import streamlit as st

from portfolio_risk.application.bootstrap import (
    ProjectState,
    load_project_state,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INSTRUMENT_PATH = PROJECT_ROOT / "data" / "instruments" / "instruments.csv"
PORTFOLIO_PATH = PROJECT_ROOT / "data" / "portfolio" / "portfolio.csv"
MARKET_PATH = PROJECT_ROOT / "data" / "market" / "market_snapshot.csv"


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

    st.title("Portfolio Risk Dashboard")
    st.caption("Block 0 — Portfolio / Market Data")

    try:
        state = load_project_state(
            instrument_path=INSTRUMENT_PATH,
            portfolio_path=PORTFOLIO_PATH,
            market_path=MARKET_PATH,
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


if __name__ == "__main__":
    render_dashboard()
