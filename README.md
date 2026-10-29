# XB Python Integration

A Streamlit application with XB branding and separate workspaces for the Ghai
and Alliance departments.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Project structure

- `app.py`: branding, navigation, and shared styling.
- `departments/ghai.py`: shared Ghai performance dashboard and Excel upload.
- `departments/alliance.py`: Alliance workspace and tools.
- `departments/matrix_rules.py`: Excel Matrix-to-GL-rules conversion.
- `departments/assets/gl_import_template.xlsx`: base template for GL exports.

Add department-specific tools to the corresponding module and expose their
interface from its `render()` function. The application does not execute
arbitrary Python code supplied by users.

## Alliance: Matrix → Rules

Open **Alliance** and select **Matrix → Rules**. Upload a Matrix workbook with
`Earnings`, `Deductions`, and `Taxes` worksheets. Optionally upload a department
mapping CSV with `Description` and `Department` columns. Review the generated
rules, configure offset accounts, and download the result as `gl_rules.xlsx`.

## Ghai shared dashboard

The Ghai dashboard and its upload controls require sign-in. Configure
`GHAI_ADMIN_PASSWORD` as a server environment variable or in Streamlit secrets.
Signed-in users can view the shared dashboard and publish data from the
**Administrator: update the shared dashboard** panel. Do not commit the
password or a populated secrets file.

For local PowerShell testing, set the password before starting Streamlit:

```powershell
$env:GHAI_ADMIN_PASSWORD = "Ghai!Happy!2026!"
python -m streamlit run app.py
```

For a deployed app, add `GHAI_ADMIN_PASSWORD = "replace-with-a-strong-password"`
to the deployment's Streamlit secrets instead.

The application stores the latest workbook in the server's `data` directory by
default. Set `XB_SHARED_DATA_DIR` to a persistent shared directory when the
deployment requires a different location. If Streamlit runs on multiple
instances, that location must be a shared filesystem mounted by every instance.
Users see updated data on their next app interaction or page refresh.

Download the dashboard template from Ghai and fill the `Performance` worksheet
with one row per location and date. The required columns are `Date`, `Region`,
`Location`, `Revenue (USD)`, `Labor Cost (USD)`, `Transactions`, and `Guests`.
The workbook must retain the `Performance` worksheet name; the `Instructions`
worksheet describes each field.
