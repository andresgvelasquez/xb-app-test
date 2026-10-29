from __future__ import annotations

import hmac
import os
import tempfile
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
from openpyxl.styles import Alignment, Font, PatternFill
from streamlit.errors import StreamlitSecretNotFoundError


DATA_COLUMNS = [
    "Date",
    "Region",
    "Location",
    "Revenue (USD)",
    "Labor Cost (USD)",
    "Transactions",
    "Guests",
]
REQUIRED_COLUMNS = set(DATA_COLUMNS)
DATA_DIR = Path(
    os.environ.get(
        "XB_SHARED_DATA_DIR",
        str(Path(__file__).resolve().parents[1] / "data"),
    )
).expanduser()
SHARED_WORKBOOK = DATA_DIR / "ghai_dashboard.xlsx"


def _admin_password() -> str | None:
    password = os.environ.get("GHAI_ADMIN_PASSWORD")
    if password:
        return password
    try:
        return st.secrets.get("GHAI_ADMIN_PASSWORD")
    except StreamlitSecretNotFoundError:
        return None


def _read_workbook(file_bytes: bytes) -> pd.DataFrame:
    try:
        workbook = pd.ExcelFile(BytesIO(file_bytes))
    except (ValueError, OSError, zipfile.BadZipFile) as error:
        raise ValueError("The uploaded file is not a valid Excel workbook.") from error

    if "Performance" not in workbook.sheet_names:
        raise ValueError("The workbook must contain a worksheet named 'Performance'.")

    data = pd.read_excel(workbook, sheet_name="Performance")
    data.columns = [str(column).strip() for column in data.columns]
    missing_columns = sorted(REQUIRED_COLUMNS.difference(data.columns))
    if missing_columns:
        raise ValueError("Missing required columns: " + ", ".join(missing_columns))
    if data.empty:
        raise ValueError("The Performance worksheet does not contain any data rows.")

    data = data[DATA_COLUMNS].copy()
    for column in ("Region", "Location"):
        data[column] = data[column].astype("string").str.strip()
        if data[column].isna().any() or data[column].eq("").any():
            raise ValueError(f"Every row must have a value in the {column} column.")

    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    if data["Date"].isna().any():
        raise ValueError("Every row must contain a valid Excel date in the Date column.")

    for column in DATA_COLUMNS[3:]:
        original = data[column]
        converted = pd.to_numeric(original, errors="coerce")
        invalid = original.notna() & converted.isna()
        if invalid.any():
            raise ValueError(f"The {column} column contains non-numeric values.")
        if converted.isna().any():
            raise ValueError(f"Every row must have a value in the {column} column.")
        if (converted < 0).any():
            raise ValueError(f"The {column} column cannot contain negative values.")
        if column in {"Transactions", "Guests"} and (converted % 1 != 0).any():
            raise ValueError(f"The {column} column must contain whole numbers.")
        data[column] = converted

    return data.sort_values("Date").reset_index(drop=True)


def _make_template() -> bytes:
    instructions = pd.DataFrame(
        [
            ("Date", "Required", "Business date for this location's results."),
            ("Region", "Required", "Region or operating area."),
            ("Location", "Required", "Store, office, or operating location."),
            ("Revenue (USD)", "Required", "Total revenue for the date, in USD."),
            ("Labor Cost (USD)", "Required", "Total labor cost for the date, in USD."),
            ("Transactions", "Required", "Number of completed transactions."),
            ("Guests", "Required", "Number of guests served."),
        ],
        columns=["Column", "Requirement", "Description"],
    )
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(columns=DATA_COLUMNS).to_excel(
            writer, index=False, sheet_name="Performance"
        )
        instructions.to_excel(writer, index=False, sheet_name="Instructions")
        for worksheet in writer.book.worksheets:
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            worksheet.row_dimensions[1].height = 24
            for cell in worksheet[1]:
                cell.fill = PatternFill("solid", fgColor="00162B")
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(vertical="center")
            for column_cells in worksheet.columns:
                column_letter = column_cells[0].column_letter
                width = max(
                    len(str(cell.value)) if cell.value is not None else 0
                    for cell in column_cells
                )
                worksheet.column_dimensions[column_letter].width = min(
                    max(width + 3, 14), 52
                )
    return output.getvalue()


def _save_shared_workbook(file_bytes: bytes) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=DATA_DIR,
            prefix=".ghai-dashboard-",
            suffix=".xlsx",
            delete=False,
        ) as temporary_file:
            temporary_file.write(file_bytes)
            temporary_path = temporary_file.name
        os.replace(temporary_path, SHARED_WORKBOOK)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def _sign_in() -> bool:
    password = _admin_password()
    if not password:
        st.error(
            "Ghai dashboard access is disabled until GHAI_ADMIN_PASSWORD is "
            "configured in the server environment or Streamlit secrets."
        )
        return False

    if st.session_state.get("ghai_authenticated", False):
        return True

    st.markdown('<h1 class="xb-title">Ghai Dashboard Sign In</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="xb-subtitle">Sign in to view the shared dashboard and manage '
        "its data.</p>",
        unsafe_allow_html=True,
    )
    with st.form("ghai_dashboard_login"):
        entered_password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        if hmac.compare_digest(entered_password, password):
            st.session_state.ghai_authenticated = True
            st.rerun()
        st.error("Incorrect password.")
    return False


def _show_admin_controls() -> None:
    with st.expander("Administrator: update the shared dashboard"):
        st.markdown(
            '<p class="xb-admin-help">Upload a completed dashboard workbook to '
            "publish the latest data for all signed-in users.</p>",
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Upload the completed Ghai dashboard workbook",
            type=["xlsx"],
            help="The workbook must follow the downloadable template.",
            key="ghai_dashboard_upload",
        )
        if uploaded_file is not None and st.button(
            "Publish dashboard data",
            type="primary",
            key="publish_ghai_dashboard",
        ):
            try:
                _read_workbook(uploaded_file.getvalue())
            except ValueError as error:
                st.error(f"Workbook validation failed: {error}")
                return
            try:
                _save_shared_workbook(uploaded_file.getvalue())
            except OSError as error:
                st.error(f"Could not publish the shared workbook: {error}")
                return
            st.success("The shared Ghai dashboard has been updated.")
            st.rerun()

    if st.button("Sign out", key="ghai_dashboard_signout"):
        st.session_state.ghai_authenticated = False
        st.rerun()


def _format_currency(value: float) -> str:
    return f"${value:,.0f}"


def _show_dashboard(data: pd.DataFrame) -> None:
    st.markdown(
        '<p class="xb-eyebrow">Ghai · Performance Overview</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<h1 class="xb-title">Business Dashboard</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="xb-subtitle">A shared view of revenue, labor, and operating '
        "performance across Ghai locations.</p>",
        unsafe_allow_html=True,
    )

    minimum_date = data["Date"].min().date()
    maximum_date = data["Date"].max().date()
    selected_dates = st.date_input(
        "Date range",
        value=(minimum_date, maximum_date),
        min_value=minimum_date,
        max_value=maximum_date,
        key="ghai_dashboard_dates",
    )

    if isinstance(selected_dates, (tuple, list)):
        if len(selected_dates) == 1:
            date_start = date_end = selected_dates[0]
        elif len(selected_dates) == 2:
            date_start, date_end = selected_dates
        else:
            date_start, date_end = minimum_date, maximum_date
    else:
        date_start = date_end = selected_dates

    filter_left, filter_right = st.columns(2)
    with filter_left:
        selected_regions = st.multiselect(
            "Region",
            sorted(data["Region"].dropna().unique().tolist()),
            default=sorted(data["Region"].dropna().unique().tolist()),
            key="ghai_dashboard_regions",
        )
    with filter_right:
        available_locations = sorted(
            data.loc[data["Region"].isin(selected_regions), "Location"]
            .dropna()
            .unique()
            .tolist()
        )
        selected_locations = st.multiselect(
            "Location",
            available_locations,
            default=available_locations,
            key="ghai_dashboard_locations",
        )

    filtered = data[
        data["Date"].dt.date.between(date_start, date_end)
        & data["Region"].isin(selected_regions)
        & data["Location"].isin(selected_locations)
    ].copy()
    if filtered.empty:
        st.info("No results match the selected filters.")
        return

    revenue = float(filtered["Revenue (USD)"].sum())
    labor_cost = float(filtered["Labor Cost (USD)"].sum())
    transactions = float(filtered["Transactions"].sum())
    guests = float(filtered["Guests"].sum())
    labor_percentage = labor_cost / revenue * 100 if revenue else 0.0
    average_transaction = revenue / transactions if transactions else 0.0
    revenue_per_guest = revenue / guests if guests else 0.0

    st.markdown("### Key performance indicators")
    kpi_columns = st.columns(4)
    kpi_columns[0].metric("Revenue", _format_currency(revenue))
    kpi_columns[1].metric("Labor cost", _format_currency(labor_cost))
    kpi_columns[2].metric("Labor %", f"{labor_percentage:.1f}%")
    kpi_columns[3].metric("Transactions", f"{transactions:,.0f}")

    secondary_columns = st.columns(3)
    secondary_columns[0].metric("Average transaction", _format_currency(average_transaction))
    secondary_columns[1].metric("Revenue per guest", _format_currency(revenue_per_guest))
    secondary_columns[2].metric("Guests", f"{guests:,.0f}")

    st.markdown("### Revenue and labor trends")
    daily = (
        filtered.groupby("Date")[["Revenue (USD)", "Labor Cost (USD)"]]
        .sum()
        .sort_index()
    )
    st.line_chart(daily, y=["Revenue (USD)", "Labor Cost (USD)"], x_label="Date")

    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.markdown("### Revenue by region")
        region_revenue = (
            filtered.groupby("Region")["Revenue (USD)"].sum().sort_values(ascending=False)
        )
        st.bar_chart(region_revenue, horizontal=True)
    with chart_right:
        st.markdown("### Revenue by location")
        location_revenue = (
            filtered.groupby("Location")["Revenue (USD)"]
            .sum()
            .sort_values(ascending=False)
        )
        st.bar_chart(location_revenue, horizontal=True)

    st.markdown("### Filtered data")
    display_data = filtered.copy()
    display_data["Date"] = display_data["Date"].dt.date
    st.dataframe(display_data, hide_index=True)


def render() -> None:
    """Render the Ghai shared performance dashboard."""
    st.markdown('<p class="xb-eyebrow">Department</p>', unsafe_allow_html=True)
    if not _sign_in():
        return
    _show_admin_controls()

    if not SHARED_WORKBOOK.exists():
        st.markdown('<h1 class="xb-title">Ghai Business Dashboard</h1>', unsafe_allow_html=True)
        st.markdown(
            '<p class="xb-subtitle">The shared dashboard will appear here after an '
            "administrator uploads the first data workbook.</p>",
            unsafe_allow_html=True,
        )
        st.download_button(
            "Download Excel template",
            data=_make_template(),
            file_name="ghai_dashboard_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        return

    try:
        data = _read_workbook(SHARED_WORKBOOK.read_bytes())
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        st.error(f"Could not load the shared dashboard workbook: {error}")
        return

    modified = date.fromtimestamp(SHARED_WORKBOOK.stat().st_mtime)
    st.caption(f"Shared data · Last updated {modified:%B %d, %Y}")
    _show_dashboard(data)
