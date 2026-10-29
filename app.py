import base64
from pathlib import Path

import streamlit as st

from departments import alliance, ghai

ROOT_DIR = Path(__file__).parent
DEPARTMENTS = {
    "Ghai": ghai,
    "Alliance": alliance,
}

st.set_page_config(
    page_title="XB | Python Integration",
    page_icon="🧩",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --xb-navy: #00162b;
        --xb-blue: #173c60;
        --xb-pale: #edf3f8;
        --xb-text: #183047;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 50% 0%, #eaf1f7 0%, #f7f9fc 38%, #ffffff 78%);
        color: var(--xb-text);
    }

    [data-testid="stMain"] {
        color: var(--xb-text);
    }

    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3,
    [data-testid="stMain"] h4,
    [data-testid="stMain"] label,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stMain"] [data-testid="stCaptionContainer"],
    [data-testid="stMain"] [data-testid="stWidgetLabel"] p {
        color: var(--xb-text) !important;
    }

    [data-testid="stMain"] [data-testid="stCaptionContainer"] {
        color: #52677b !important;
    }

    [data-testid="stMain"] button[data-testid^="stBaseButton-"] {
        background: #ffffff !important;
        border: 1px solid #71869a !important;
        box-shadow: none !important;
        color: #00162b !important;
    }

    [data-testid="stMain"] button[data-testid^="stBaseButton-"]:hover {
        background: #edf3f8 !important;
        border-color: #173c60 !important;
        color: #00162b !important;
    }

    [data-testid="stMain"] button[data-testid^="stBaseButton-"] *,
    [data-testid="stMain"] button[data-testid^="stBaseButton-"]:hover * {
        color: #00162b !important;
        -webkit-text-fill-color: #00162b !important;
    }

    [data-testid="stMain"] [data-baseweb="input"],
    [data-testid="stMain"] [data-baseweb="base-input"],
    [data-testid="stMain"] [data-baseweb="select"] > div,
    [data-testid="stMain"] [data-baseweb="datepicker"],
    [data-testid="stMain"] textarea {
        background-color: #ffffff !important;
        border-color: #9aabba !important;
        color: #183047 !important;
    }

    [data-testid="stMain"] input:not([type="checkbox"]):not([type="radio"]):not([type="file"]),
    [data-testid="stMain"] textarea {
        background-color: #ffffff !important;
        color: #183047 !important;
        -webkit-text-fill-color: #183047 !important;
    }

    [data-testid="stMain"] [data-baseweb="base-input"] input {
        background-color: #ffffff !important;
        color: #183047 !important;
        -webkit-text-fill-color: #183047 !important;
    }

    [data-testid="stMain"] [data-baseweb="select"] [data-baseweb="tag"] {
        background-color: #dce7f1 !important;
        color: #00162b !important;
        flex: 0 0 auto !important;
        max-width: 100% !important;
        overflow: visible !important;
    }

    [data-testid="stMain"] [data-baseweb="select"] [data-baseweb="tag"] *,
    [data-testid="stMain"] [data-baseweb="select"] [data-baseweb="tag"] span {
        color: #00162b !important;
        -webkit-text-fill-color: #00162b !important;
    }

    [data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="tag"] > span {
        display: block !important;
        flex: 0 1 auto !important;
        max-width: none !important;
        overflow: visible !important;
        padding-inline: 0.3rem !important;
        text-overflow: clip !important;
        white-space: nowrap !important;
    }

    [data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="tag"] button {
        flex: 0 0 auto !important;
        color: #00162b !important;
    }

    [data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="tag"] button svg {
        fill: #00162b !important;
        color: #00162b !important;
    }

    [data-testid="stMain"] [data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid #c8d3de !important;
        border-radius: 12px !important;
    }

    [data-testid="stMain"] [data-testid="stExpander"] summary,
    [data-testid="stMain"] [data-testid="stExpander"] summary:hover {
        background: #edf3f8 !important;
        color: #00162b !important;
    }

    [data-testid="stMain"] [data-testid="stExpander"] summary *,
    [data-testid="stMain"] [data-testid="stExpander"] summary:hover * {
        color: #00162b !important;
        -webkit-text-fill-color: #00162b !important;
    }

    [data-testid="stMain"] .xb-admin-help {
        color: #435a70 !important;
        margin: 0 0 0.75rem;
    }

    [data-testid="stMain"] [data-testid="stFileUploader"] {
        background: transparent;
        border: 0;
        color: #183047 !important;
    }

    [data-testid="stMain"] [data-testid="stFileUploaderDropzone"] {
        background: #ffffff !important;
        border: 1px dashed #9aabba !important;
        border-radius: 12px;
        color: #183047 !important;
        padding: 1.1rem;
    }

    [data-testid="stMain"] [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #173c60 !important;
        background: #f7fafd !important;
    }

    [data-testid="stMain"] [data-testid="stFileUploader"] p,
    [data-testid="stMain"] [data-testid="stFileUploader"] span,
    [data-testid="stMain"] [data-testid="stFileUploader"] small,
    [data-testid="stMain"] [data-testid="stFileUploader"] label {
        color: #183047 !important;
    }

    [data-testid="stMain"] [data-testid="stFileUploader"] button {
        background: #ffffff !important;
        border: 1px solid #71869a !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        color: #00162b !important;
        font-weight: 600 !important;
    }

    [data-testid="stMain"] [data-testid="stFileUploader"] button:hover {
        background: #edf3f8 !important;
        border-color: #173c60 !important;
        color: #00162b !important;
    }

    [data-testid="stMain"] [data-testid="stFileUploader"] button *,
    [data-testid="stMain"] [data-testid="stFileUploader"] button:hover * {
        color: #00162b !important;
        -webkit-text-fill-color: #00162b !important;
    }

    [data-testid="stMain"] [data-testid="stDownloadButton"] button {
        background: #ffffff !important;
        border: 1px solid #71869a !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        color: #00162b !important;
        font-weight: 600 !important;
    }

    [data-testid="stMain"] [data-testid="stDownloadButton"] button:hover {
        background: #edf3f8 !important;
        border-color: #173c60 !important;
        color: #00162b !important;
    }

    [data-testid="stMain"] [data-testid="stDownloadButton"] button *,
    [data-testid="stMain"] [data-testid="stDownloadButton"] button:hover * {
        color: #00162b !important;
        -webkit-text-fill-color: #00162b !important;
    }

    [data-testid="stMain"] [data-baseweb="input"],
    [data-testid="stMain"] [data-baseweb="select"] > div,
    [data-testid="stMain"] textarea {
        background-color: #ffffff;
        color: #183047 !important;
    }

    [data-testid="stMain"] input,
    [data-testid="stMain"] textarea,
    [data-testid="stMain"] [data-baseweb="select"] span {
        color: #183047 !important;
        -webkit-text-fill-color: #183047;
    }

    [data-testid="stMain"] input::placeholder,
    [data-testid="stMain"] textarea::placeholder {
        color: #607387 !important;
        opacity: 1;
    }

    [data-testid="stMain"] [data-baseweb="tab-list"] button {
        color: #435a70 !important;
    }

    [data-testid="stMain"] [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #00162b !important;
        border-bottom-color: #173c60 !important;
    }

    [data-testid="stMain"] [data-testid="stButtonGroup"] {
        background: #edf2f7 !important;
        border: 1px solid #c8d3de !important;
        border-radius: 12px;
        padding: 0.25rem;
    }

    [data-testid="stMain"] [data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_control"] {
        background: #ffffff !important;
        border: 1px solid #c8d3de !important;
        box-shadow: none !important;
        border-radius: 9px;
        color: #183047 !important;
        font-weight: 600;
    }

    [data-testid="stMain"] [data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"] {
        background: #dce7f1 !important;
        border: 1px solid #173c60 !important;
        box-shadow: 0 1px 3px rgba(0, 22, 43, 0.12) !important;
        color: #00162b !important;
    }

    [data-testid="stMain"] [data-testid="stButtonGroup"] button[data-testid^="stBaseButton-segmented_control"] *,
    [data-testid="stMain"] [data-testid="stButtonGroup"] button[data-testid^="stBaseButton-segmented_control"]:hover * {
        color: #183047 !important;
        -webkit-text-fill-color: #183047 !important;
    }

    [data-testid="stMain"] [data-testid="stButtonGroup"] button[data-testid^="stBaseButton-segmented_control"]:hover {
        background: #edf3f8 !important;
        border-color: #71869a !important;
        color: #00162b !important;
    }

    [data-testid="stMain"] [data-testid="stAlert"] p,
    [data-testid="stMain"] [data-testid="stAlert"] span {
        color: #183047 !important;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: var(--xb-navy);
        border-right: 1px solid #16344f;
    }

    [data-testid="stSidebar"] * {
        color: #f5f8fb;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #c7d5e2;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label {
        background: rgba(255, 255, 255, 0.045);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        margin: 0.3rem 0;
        padding: 0.65rem 0.8rem;
        transition: background 150ms ease, border-color 150ms ease;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(255, 255, 255, 0.11);
        border-color: rgba(255, 255, 255, 0.22);
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #f5f8fb;
    }

    .xb-brand {
        text-align: center;
        padding: 0.75rem 0 1.15rem;
    }

    .xb-brand img {
        width: min(100%, 430px);
        height: auto;
        border-radius: 8px;
        box-shadow: 0 12px 32px rgba(0, 22, 43, 0.12);
    }

    .xb-eyebrow {
        color: var(--xb-blue);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        margin: 0.25rem 0 0.55rem;
        text-align: center;
        text-transform: uppercase;
    }

    .xb-title {
        color: var(--xb-navy);
        font-size: clamp(2rem, 5vw, 2.8rem);
        font-weight: 750;
        letter-spacing: -0.045em;
        line-height: 1.1;
        margin: 0;
        text-align: center;
    }

    .xb-subtitle {
        color: #5a6c7d;
        font-size: 1.02rem;
        line-height: 1.65;
        margin: 0.8rem auto 1.7rem;
        max-width: 640px;
        text-align: center;
    }

    .xb-card {
        background: rgba(255, 255, 255, 0.86);
        border: 1px solid #dfe7ef;
        border-radius: 16px;
        box-shadow: 0 12px 35px rgba(0, 22, 43, 0.06);
        margin: 0.6rem 0;
        padding: 1.2rem 1.35rem;
        text-align: center;
    }

    .xb-card h3 {
        color: var(--xb-navy);
        font-size: 1.05rem;
        margin: 0 0 0.4rem;
    }

    .xb-card p {
        color: #5a6c7d;
        line-height: 1.55;
        margin: 0;
    }

    .xb-footer {
        color: #718294;
        font-size: 0.82rem;
        margin-top: 2rem;
        text-align: center;
    }

    div.stButton > button {
        background: var(--xb-navy);
        border: 1px solid var(--xb-navy);
        border-radius: 10px;
        color: #ffffff;
        font-weight: 600;
        min-height: 2.7rem;
        transition: background 150ms ease, transform 150ms ease;
    }

    div.stButton > button:hover {
        background: var(--xb-blue);
        border-color: var(--xb-blue);
        color: #ffffff;
        transform: translateY(-1px);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## XB Franchise Solutions")
    st.markdown("### Python Integration")
    st.markdown("Choose a department to open its workspace.")
    st.divider()
    selection = st.radio(
        "Department",
        options=["Home", *DEPARTMENTS],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Franchise Solutions · Your Back Office Reimagined")

brand_image = base64.b64encode((ROOT_DIR / "xb_banner.png").read_bytes()).decode(
    "ascii"
)
st.markdown(
    f'<div class="xb-brand"><img src="data:image/png;base64,{brand_image}" '
    'alt="XB Franchise Solutions"></div>',
    unsafe_allow_html=True,
)

if selection == "Home":
    st.markdown(
        '<p class="xb-eyebrow">XB · Python Integration</p>', unsafe_allow_html=True
    )
    st.markdown('<h1 class="xb-title">Workspace</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="xb-subtitle">A dedicated space for each department’s Python tools '
        "and workflows.</p>",
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        st.markdown(
            '<div class="xb-card"><h3>Ghai</h3><p>Tools and automations for the '
            "Ghai department.</p></div>",
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            '<div class="xb-card"><h3>Alliance</h3><p>Tools and automations for the '
            "Alliance department.</p></div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        '<p class="xb-footer">Choose a department from the sidebar to get started.</p>',
        unsafe_allow_html=True,
    )
else:
    DEPARTMENTS[selection].render()
