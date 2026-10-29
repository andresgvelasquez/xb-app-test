from __future__ import annotations

from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd


SHEETS = {
    "Earnings": ("E", 2010),
    "Deductions": ("D", 4010),
    "Taxes": ("T", 6020),
}
TEMPLATE_PATH = Path(__file__).parent / "assets" / "gl_import_template.xlsx"
OUTPUT_COLUMNS = [
    "cglrules.sequence",
    "cglrules.condition",
    "cglrules.sql",
    "cglrules.description",
]
CORE_COLUMNS = ["DET", "Code", "Description", "Type", "offset account", "General"]


def _is_empty(value: Any) -> bool:
    return pd.isna(value) or (isinstance(value, str) and not value.strip())


def _text(value: Any) -> str:
    if _is_empty(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _unique_headers(headers: list[str]) -> list[str]:
    result: list[str] = []
    counts: dict[str, int] = defaultdict(int)
    for header in headers:
        counts[header] += 1
        result.append(header if counts[header] == 1 else f"{header}_{counts[header]}")
    return result


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def clean_matrix(raw: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """Extract the DET/code fields and cost-center columns from a Matrix sheet."""
    if raw.empty or raw.shape[1] < 6:
        raise ValueError("The worksheet must contain at least the six core columns.")

    det_rows = [
        row_index
        for row_index, value in enumerate(raw.iloc[:, 0])
        if _text(value).casefold() == "det"
    ]
    if not det_rows:
        raise ValueError("Could not find the DET header in the first column.")
    header_row = det_rows[0]

    marker = None
    for row_index in range(header_row, len(raw)):
        for column_index in range(6, raw.shape[1]):
            if _text(raw.iat[row_index, column_index]).casefold() in {
                "costcenter",
                "cost center",
                "department",
            }:
                marker = (row_index, column_index)
                break
        if marker is not None:
            break

    cost_header_row = header_row
    if marker is not None:
        marker_row, marker_column = marker
        for row_index in range(marker_row + 1, len(raw)):
            if not _is_empty(raw.iat[row_index, marker_column]):
                cost_header_row = row_index
                break
        else:
            for row_index in range(marker_row + 1, len(raw)):
                if any(not _is_empty(raw.iat[row_index, col]) for col in range(6, raw.shape[1])):
                    cost_header_row = row_index
                    break

    core_headers = [_text(value) for value in raw.iloc[header_row, :6]]
    for index in range(1, len(core_headers)):
        if not core_headers[index]:
            core_headers[index] = core_headers[index - 1]

    aliases = {
        "det": "DET",
        "code": "Code",
        "description": "Description",
        "type": "Type",
        "offset account": "offset account",
        "offsetaccount": "offset account",
        "general": "General",
    }
    core_headers = [
        aliases.get(header.casefold(), header or CORE_COLUMNS[index])
        for index, header in enumerate(core_headers)
    ]
    if core_headers[0] != "DET" or core_headers[1] != "Code":
        raise ValueError("The core headers must include DET and Code.")

    cost_headers = [_text(value) for value in raw.iloc[cost_header_row, 6:]]
    if marker is None:
        cost_headers = [_text(value) for value in raw.iloc[header_row, 6:]]
    valid_cost_columns = [
        index for index, header in enumerate(cost_headers) if header
    ]
    cost_headers = [cost_headers[index] for index in valid_cost_columns]
    headers = _unique_headers(core_headers + cost_headers)

    data_start = max(header_row, cost_header_row) + 1
    data_columns = list(range(6)) + [6 + index for index in valid_cost_columns]
    cleaned = raw.iloc[data_start:, data_columns].copy()
    cleaned.columns = headers
    cleaned = cleaned.dropna(how="all")
    cleaned["DET"] = cleaned["DET"].map(_text).str.upper()
    cleaned = cleaned[cleaned["DET"].isin({"D", "E", "T"})].reset_index(drop=True)
    if cleaned.empty:
        raise ValueError("No data rows with DET D, E, or T were found.")

    has_cost_centers = bool(cost_headers)
    only_general_rules = not has_cost_centers or all(
        _is_empty(value) for value in cleaned.iloc[:, 6:].to_numpy().flat
    )
    return cleaned, bool(only_general_rules)


def _quoted_list(values: list[str]) -> str:
    escaped = [_sql_string(value) for value in values]
    if len(escaped) == 1:
        return f"= {escaped[0]}"
    return f"in ({', '.join(escaped)})"


def _make_condition(det: str, codes: list[str], cost_centers: list[str] | None = None) -> str:
    code_condition = _quoted_list(codes)
    condition = f"det = '{det}' and detcode {code_condition}"
    if cost_centers:
        cc_condition = _quoted_list(cost_centers)
        condition += f" and cc2 {cc_condition}"
    return condition


def transform_sheet(
    cleaned: pd.DataFrame,
    sheet_name: str,
    departments: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Transform one cleaned Matrix sheet into GL rules."""
    if sheet_name not in SHEETS:
        raise ValueError(f"Unsupported worksheet: {sheet_name}.")
    det, first_sequence = SHEETS[sheet_name]

    if departments is not None:
        required = {"Description", "Department"}
        if not required.issubset(departments.columns):
            raise ValueError("The CSV must include Description and Department columns.")
        mapping = {
            _text(description): _text(department)
            for description, department in zip(
                departments["Description"], departments["Department"]
            )
            if not _is_empty(description) and not _is_empty(department)
        }
        cleaned = cleaned.rename(
            columns={column: mapping.get(column, column) for column in cleaned.columns[6:]}
        )

    entries: list[tuple[str, str]] = []
    general_rows = cleaned[cleaned["General"].map(lambda value: not _is_empty(value))]
    for account, group in general_rows.groupby("General", sort=False):
        codes = sorted({_text(value) for value in group["Code"] if not _is_empty(value)})
        if codes:
            entries.append(
                (_make_condition(det, codes), f"gl1={_sql_string(_text(account))}")
            )

    account_rules: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"codes": set(), "cost_centers": set()}
    )
    for _, row in cleaned.iterrows():
        code = _text(row["Code"])
        if not code:
            continue
        for column_index in range(6, cleaned.shape[1]):
            if not _is_empty(row.iloc[column_index]):
                account = _text(row.iloc[column_index])
                account_rules[account]["codes"].add(code)
                account_rules[account]["cost_centers"].add(
                    _text(cleaned.columns[column_index])
                )

    for account, values in account_rules.items():
        entries.append(
            (
                _make_condition(
                    det,
                    sorted(values["codes"]),
                    sorted(values["cost_centers"]),
                ),
                f"gl1={_sql_string(account)}",
            )
        )

    rules = pd.DataFrame(entries, columns=["Filter", "Assignment"])
    rules = rules.sort_values("Assignment", kind="stable").reset_index(drop=True)
    rules.insert(0, "Sequence", range(first_sequence, first_sequence + 10 * len(rules), 10))
    return rules[["Sequence", "Filter", "Assignment"]]


def generate_rules(
    matrix_bytes: bytes,
    departments_bytes: bytes | None = None,
) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    """Read and transform Earnings, Deductions and Taxes from an uploaded workbook."""
    workbook = pd.ExcelFile(BytesIO(matrix_bytes))
    missing_sheets = [name for name in SHEETS if name not in workbook.sheet_names]
    if missing_sheets:
        raise ValueError(
            "The workbook is missing required worksheets: " + ", ".join(missing_sheets)
        )

    departments = None
    if departments_bytes is not None:
        departments = pd.read_csv(BytesIO(departments_bytes))
        departments.columns = [str(column).strip() for column in departments.columns]

    results: dict[str, pd.DataFrame] = {}
    general_only: dict[str, bool] = {}
    for sheet_name in SHEETS:
        raw_sheet = pd.read_excel(workbook, sheet_name=sheet_name, header=None)
        cleaned, general_only[sheet_name] = clean_matrix(raw_sheet)
        results[sheet_name] = transform_sheet(cleaned, sheet_name, departments)
    return results, general_only


def build_offset_sql(offsets: pd.DataFrame) -> str | None:
    entries = []
    for _, row in offsets.iterrows():
        account = _text(row.get("Account", ""))[:20]
        if not account:
            continue
        when = _text(row.get("When", "detcode")) or "detcode"
        if when not in {"detcode", "cc1", "cc2", "cc3", "cc4", "cc5"}:
            raise ValueError(f"Unsupported When field: {when}.")
        action = _text(row.get("Action", "Then")) or "Then"
        if action not in {"Then", "Else"}:
            raise ValueError(f"Unsupported offset action: {action}.")
        entries.append(
            {
                "account": account,
                "when": when,
                "equals": _text(row.get("Equals", "")),
                "action": action,
            }
        )

    if not entries:
        return None
    if len(entries) == 1:
        return entries[0]["account"]

    clauses = []
    else_accounts = []
    for entry in entries:
        if entry["action"] == "Else":
            else_accounts.append(entry["account"])
            continue
        if not entry["equals"]:
            raise ValueError("Enter an Equals value for each Then condition.")
        clauses.append(
            f"When {entry['when']} = {_sql_string(entry['equals'])} "
            f"Then {_sql_string(entry['account'])}"
        )
    if len(else_accounts) > 1:
        raise ValueError("Only one Else row is allowed.")
    if not clauses:
        raise ValueError("Add at least one Then condition to create the CASE rule.")
    if else_accounts:
        clauses.append(f"Else {_sql_string(else_accounts[0])}")
    return "Case " + " ".join(clauses) + " end"


def build_export(rules: pd.DataFrame, offsets: pd.DataFrame) -> pd.DataFrame:
    """Combine the standard GL template with generated rules and offset settings."""
    template = pd.read_excel(TEMPLATE_PATH)
    offset_sql = build_offset_sql(offsets)
    if offset_sql:
        account_count = sum(
            bool(_text(account))
            for account in offsets.get("Account", pd.Series(dtype=str))
        )
        is_case = account_count > 1
        replacement = offset_sql
        for column in ("cglrules.condition", "cglrules.sql"):
            template[column] = template[column].map(
                lambda value: value.replace("'CASH'", replacement)
                if isinstance(value, str) and is_case
                else value.replace("CASH", replacement)
                if isinstance(value, str)
                else value
            )

    generated = rules.rename(
        columns={
            "Sequence": "cglrules.sequence",
            "Filter": "cglrules.condition",
            "Assignment": "cglrules.sql",
        }
    )
    generated["cglrules.description"] = ""
    return (
        pd.concat([template[OUTPUT_COLUMNS], generated[OUTPUT_COLUMNS]], ignore_index=True)
        .sort_values("cglrules.sequence", kind="stable")
        .reset_index(drop=True)
    )


def export_xlsx(frame: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame[OUTPUT_COLUMNS].to_excel(writer, index=False, sheet_name="GL Rules")
    return output.getvalue()
