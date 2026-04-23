"""app.py – CareerOS main entry point. Global error handling. Zero crashes."""
import streamlit as st

# ─── PAGE CONFIG (must be first Streamlit call) ─────────────
st.set_page_config(
    page_title="CareerOS – AI Career Operating System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── GLOBAL STYLES ──────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Dark base */
    .stApp { background-color: #111827; color: #F9FAFB; }
    section[data-testid="stSidebar"] { background-color: #0F172A; }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button:hover { transform: translateY(-1px); }

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1F2937;
        color: #F9FAFB;
        border-color: #374151;
        border-radius: 8px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 6px 16px;
        color: #9CA3AF;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1F2937;
        color: #F9FAFB;
    }

    /* Metrics */
    [data-testid="metric-container"] {
        background-color: #1F2937;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 16px;
    }

    /* Page links in sidebar */
    [data-testid="stPageLink"] a {
        color: #9CA3AF !important;
        text-decoration: none;
        font-size: 14px;
        padding: 6px 8px;
        border-radius: 6px;
        display: block;
    }
    [data-testid="stPageLink"] a:hover {
        color: #F9FAFB !important;
        background-color: #1F2937;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── IMPORTS (after page config) ────────────────────────────
import utils.session as session
from components.auth import render_auth_page
from components.sidebar import render_sidebar

# ─── INIT SESSION ───────────────────────────────────────────
session.init_session()

# ─── AUTH GATE ──────────────────────────────────────────────
if not session.get("authenticated"):
    render_auth_page()
    st.stop()

# ─── MAIN APP ────────────────────────────────────────────────
render_sidebar()

# Route to the correct page module based on current page
# (Streamlit multi-page apps handle routing via pages/ folder)
# This file is the main entry; routing is handled by st.switch_page / page links.

# Default: show dashboard
try:
    from pages.dashboard import render
    render()
except Exception as e:
    st.error(
        "⚠️ Something went wrong loading the dashboard. "
        "Please refresh the page."
    )
    if st.checkbox("Show technical details"):
        st.exception(e)
