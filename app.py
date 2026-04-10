"""Shiny for Python app to explore the Git-LFS-tracked transactions dataset.

Run with:
    shiny run app.py
"""

import pathlib

import numpy as np
import pandas as pd
from shiny import App, reactive, render, ui

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

DATA_PATH = pathlib.Path(__file__).parent / "data" / "transactions.csv"


def load_data() -> pd.DataFrame:
    """Load the transactions CSV into a DataFrame."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"{DATA_PATH} not found. Run `python generate_dataset.py` first."
        )
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    df["date"] = df["timestamp"].dt.date
    return df


DF = load_data()

ALL_CATEGORIES = sorted(DF["category"].unique().tolist())
ALL_REGIONS = sorted(DF["region"].unique().tolist())
ALL_STATUSES = sorted(DF["status"].unique().tolist())
MIN_DATE = DF["date"].min()
MAX_DATE = DF["date"].max()

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h4("Filters"),
        ui.input_date_range(
            "date_range",
            "Date Range",
            start=MIN_DATE,
            end=MAX_DATE,
            min=MIN_DATE,
            max=MAX_DATE,
        ),
        ui.input_selectize(
            "categories",
            "Categories",
            choices=ALL_CATEGORIES,
            selected=ALL_CATEGORIES,
            multiple=True,
        ),
        ui.input_selectize(
            "regions",
            "Regions",
            choices=ALL_REGIONS,
            selected=ALL_REGIONS,
            multiple=True,
        ),
        ui.input_selectize(
            "statuses",
            "Order Status",
            choices=ALL_STATUSES,
            selected=ALL_STATUSES,
            multiple=True,
        ),
        ui.input_slider(
            "table_rows",
            "Table preview rows",
            min=100,
            max=5000,
            value=500,
            step=100,
        ),
        ui.hr(),
        ui.h5("Dataset Info"),
        ui.output_ui("dataset_info"),
        width=320,
    ),
    # Main content --------------------------------------------------------
    ui.navset_card_tab(
        ui.nav_panel(
            "Overview",
            ui.layout_columns(
                ui.value_box("Total Transactions", ui.output_text("n_transactions"), theme="primary"),
                ui.value_box("Total Revenue", ui.output_text("total_revenue"), theme="success"),
                ui.value_box("Avg Order Value", ui.output_text("avg_order"), theme="info"),
                ui.value_box("Unique Customers", ui.output_text("n_customers"), theme="warning"),
                col_widths=[3, 3, 3, 3],
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Daily Revenue"),
                    ui.output_table("daily_revenue_table"),
                ),
                ui.card(
                    ui.card_header("Sales by Category"),
                    ui.output_table("category_summary_table"),
                ),
                col_widths=[7, 5],
            ),
        ),
        ui.nav_panel(
            "Data Table",
            ui.card(
                ui.card_header("Transaction Records (sample)"),
                ui.output_data_frame("transactions_grid"),
            ),
        ),
        ui.nav_panel(
            "Statistics",
            ui.layout_columns(
                ui.card(
                    ui.card_header("Revenue by Region"),
                    ui.output_table("region_table"),
                ),
                ui.card(
                    ui.card_header("Payment Method Breakdown"),
                    ui.output_table("payment_table"),
                ),
                col_widths=[6, 6],
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Top 10 Days by Revenue"),
                    ui.output_table("top_days_table"),
                ),
                ui.card(
                    ui.card_header("Status Distribution"),
                    ui.output_table("status_table"),
                ),
                col_widths=[6, 6],
            ),
        ),
    ),
    title="Git LFS Dataset Explorer",
    fillable=True,
)


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------


def server(input, output, session):
    @reactive.calc
    def filtered_df() -> pd.DataFrame:
        """Return the subset of data matching the current filter selections."""
        start, end = input.date_range()
        mask = (
            (DF["date"] >= start)
            & (DF["date"] <= end)
            & (DF["category"].isin(input.categories()))
            & (DF["region"].isin(input.regions()))
            & (DF["status"].isin(input.statuses()))
        )
        return DF.loc[mask]

    # -- Value boxes -------------------------------------------------------

    @render.text
    def n_transactions():
        return f"{len(filtered_df()):,}"

    @render.text
    def total_revenue():
        return f"${filtered_df()['total'].sum():,.2f}"

    @render.text
    def avg_order():
        df = filtered_df()
        avg = df["total"].mean() if len(df) > 0 else 0
        return f"${avg:,.2f}"

    @render.text
    def n_customers():
        return f"{filtered_df()['customer_id'].nunique():,}"

    # -- Sidebar info ------------------------------------------------------

    @render.ui
    def dataset_info():
        df = filtered_df()
        mem = df.memory_usage(deep=True).sum() / (1024 * 1024)
        return ui.tags.ul(
            ui.tags.li(f"Full dataset: {len(DF):,} rows"),
            ui.tags.li(f"Filtered: {len(df):,} rows"),
            ui.tags.li(f"Columns: {len(df.columns)}"),
            ui.tags.li(f"Memory: {mem:.1f} MB"),
            ui.tags.li(f"CSV size: {DATA_PATH.stat().st_size / (1024**2):.1f} MB"),
        )

    # -- Overview tab tables -----------------------------------------------

    @render.table
    def daily_revenue_table():
        df = filtered_df()
        if df.empty:
            return pd.DataFrame()
        daily = (
            df.groupby("date")
            .agg(transactions=("transaction_id", "count"), revenue=("total", "sum"))
            .reset_index()
            .sort_values("date", ascending=False)
            .head(20)
        )
        daily["revenue"] = daily["revenue"].map("${:,.2f}".format)
        daily.columns = ["Date", "Transactions", "Revenue"]
        return daily

    @render.table
    def category_summary_table():
        df = filtered_df()
        if df.empty:
            return pd.DataFrame()
        cat = (
            df.groupby("category")
            .agg(
                transactions=("transaction_id", "count"),
                revenue=("total", "sum"),
                avg_price=("unit_price", "mean"),
            )
            .reset_index()
            .sort_values("revenue", ascending=False)
        )
        cat["revenue"] = cat["revenue"].map("${:,.2f}".format)
        cat["avg_price"] = cat["avg_price"].map("${:,.2f}".format)
        cat.columns = ["Category", "Transactions", "Revenue", "Avg Unit Price"]
        return cat

    # -- Data Table tab ----------------------------------------------------

    @render.data_frame
    def transactions_grid():
        return render.DataGrid(
            filtered_df().head(input.table_rows()),
            filters=True,
            height="600px",
        )

    # -- Statistics tab tables ---------------------------------------------

    @render.table
    def region_table():
        df = filtered_df()
        if df.empty:
            return pd.DataFrame()
        reg = (
            df.groupby("region")
            .agg(
                transactions=("transaction_id", "count"),
                revenue=("total", "sum"),
                avg_order=("total", "mean"),
            )
            .reset_index()
            .sort_values("revenue", ascending=False)
        )
        reg["revenue"] = reg["revenue"].map("${:,.2f}".format)
        reg["avg_order"] = reg["avg_order"].map("${:,.2f}".format)
        reg.columns = ["Region", "Transactions", "Revenue", "Avg Order"]
        return reg

    @render.table
    def payment_table():
        df = filtered_df()
        if df.empty:
            return pd.DataFrame()
        pay = (
            df.groupby("payment_method")
            .agg(transactions=("transaction_id", "count"), revenue=("total", "sum"))
            .reset_index()
            .sort_values("revenue", ascending=False)
        )
        pay["revenue"] = pay["revenue"].map("${:,.2f}".format)
        pay.columns = ["Payment Method", "Transactions", "Revenue"]
        return pay

    @render.table
    def top_days_table():
        df = filtered_df()
        if df.empty:
            return pd.DataFrame()
        top = (
            df.groupby("date")
            .agg(transactions=("transaction_id", "count"), revenue=("total", "sum"))
            .reset_index()
            .sort_values("revenue", ascending=False)
            .head(10)
        )
        top["revenue"] = top["revenue"].map("${:,.2f}".format)
        top.columns = ["Date", "Transactions", "Revenue"]
        return top

    @render.table
    def status_table():
        df = filtered_df()
        if df.empty:
            return pd.DataFrame()
        st = (
            df.groupby("status")
            .agg(count=("transaction_id", "count"), revenue=("total", "sum"))
            .reset_index()
            .sort_values("count", ascending=False)
        )
        total = st["count"].sum()
        st["pct"] = (st["count"] / total * 100).map("{:.1f}%".format)
        st["revenue"] = st["revenue"].map("${:,.2f}".format)
        st.columns = ["Status", "Count", "Revenue", "% of Total"]
        return st


app = App(app_ui, server)
