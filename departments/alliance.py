import zipfile

import pandas as pd
import streamlit as st

from departments import matrix_rules


def _show_matrix_rules() -> None:
    st.markdown('<h2 class="xb-title">Matrix → Rules</h2>', unsafe_allow_html=True)
    st.markdown(
        '<p class="xb-subtitle">Convert a payroll matrix into GL rules, review the '
        "results, and download an import-ready workbook.</p>",
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        matrix_file = st.file_uploader(
            "Matrix Excel file",
            type=["xlsx"],
            help="Include the Earnings, Deductions, and Taxes worksheets.",
            key="alliance_matrix_file",
        )
    with right:
        departments_file = st.file_uploader(
            "Department mapping (CSV, optional)",
            type=["csv"],
            help="Map cost center names using Description and Department columns.",
            key="alliance_departments_file",
        )

    st.markdown("#### Offset accounts")
    st.caption(
        "Set the template’s CASH account. For multiple accounts, add Then conditions "
        "and optionally one Else row."
    )
    offsets = st.data_editor(
        pd.DataFrame(
            [{"Account": "CASH", "When": "detcode", "Equals": "", "Action": "Then"}]
        ),
        num_rows="dynamic",
        hide_index=True,
        key="alliance_matrix_offsets",
        column_config={
            "Account": st.column_config.TextColumn("Offset account"),
            "When": st.column_config.SelectboxColumn(
                "When",
                options=["detcode", "cc1", "cc2", "cc3", "cc4", "cc5"],
            ),
            "Equals": st.column_config.TextColumn("Equals"),
            "Action": st.column_config.SelectboxColumn(
                "Action",
                options=["Then", "Else"],
            ),
        },
    )
    long_offsets = [
        str(account).strip()
        for account in offsets["Account"]
        if isinstance(account, str) and len(account.strip()) > 20
    ]
    if long_offsets:
        st.warning(
            "Offset accounts will be limited to 20 characters in the rules: "
            + ", ".join(long_offsets)
        )

    if matrix_file is None:
        st.info("Upload a Matrix Excel file to generate and review rules.")
        return

    try:
        results, general_only = matrix_rules.generate_rules(
            matrix_file.getvalue(),
            departments_file.getvalue() if departments_file is not None else None,
        )
    except (
        ValueError,
        KeyError,
        OSError,
        ImportError,
        UnicodeDecodeError,
        zipfile.BadZipFile,
        pd.errors.ParserError,
    ) as error:
        st.error(f"Could not process the Matrix file: {error}")
        return

    st.success("Matrix processed successfully.")
    for sheet_name, is_general_only in general_only.items():
        if is_general_only:
            st.warning(f"{sheet_name}: only general rules were detected.")

    all_rules = pd.concat(
        [frame.assign(Category=sheet_name) for sheet_name, frame in results.items()],
        ignore_index=True,
    )
    rules_tab, accounts_tab, export_tab = st.tabs(
        ["Rules", "Long accounts", "Download"]
    )

    with rules_tab:
        st.dataframe(
            all_rules[["Category", "Sequence", "Filter", "Assignment"]],
            hide_index=True,
        )

    with accounts_tab:
        long_accounts = []
        for _, row in all_rules.iterrows():
            assignment = row["Assignment"]
            account = assignment[5:-1] if assignment.startswith("gl1='") else ""
            if len(account) > 20:
                long_accounts.append(
                    {
                        "Category": row["Category"],
                        "Account": account,
                        "GL account (20 chars)": account[:20],
                    }
                )
        if long_accounts:
            st.warning(
                "Offset and GL accounts support up to 20 characters. "
                "Review long accounts before importing."
            )
            st.dataframe(pd.DataFrame(long_accounts), hide_index=True)
        else:
            st.info("No GL accounts longer than 20 characters were found.")

    with export_tab:
        try:
            export_frame = matrix_rules.build_export(all_rules, offsets)
            export_bytes = matrix_rules.export_xlsx(export_frame)
            st.markdown("#### General CASH rule")
            st.caption(
                "This standard template rule is always included in the export, "
                "even when no offset account is configured."
            )
            st.dataframe(
                export_frame[export_frame["cglrules.sequence"] == 100],
                hide_index=True,
            )
            st.dataframe(export_frame, hide_index=True)
            st.download_button(
                "Download GL rules (.xlsx)",
                data=export_bytes,
                file_name="gl_rules.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except ValueError as error:
            st.warning(f"Review the offset accounts: {error}")
        except (OSError, ImportError) as error:
            st.error(f"Could not create the download file: {error}")


def render() -> None:
    """Render the Alliance department and its tools."""
    st.markdown('<p class="xb-eyebrow">Department</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="xb-title">Alliance</h1>', unsafe_allow_html=True)

    tool = st.segmented_control(
        "Alliance tools",
        ["Overview", "Matrix → Rules"],
        default="Overview",
        selection_mode="single",
        label_visibility="collapsed",
    )
    if tool == "Matrix → Rules":
        _show_matrix_rules()
        return

    st.markdown(
        '<p class="xb-subtitle">Python tools and workflows for Alliance.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="xb-card"><h3>Matrix → Rules</h3>'
        "<p>Convert Earnings, Deductions, and Taxes matrices into GL rules "
        "and prepare an import-ready workbook.</p></div>",
        unsafe_allow_html=True,
    )
