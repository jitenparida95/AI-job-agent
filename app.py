import streamlit as st
from auth import require_auth, render_subscription_banner, sign_out, is_subscribed

st.set_page_config(
    page_title="JobAgent AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Auth gate — must come before any other st.* calls ─────────
user, sub = require_auth()

# Block access if subscription expired
if user and sub and not is_subscribed(sub):
    st.error("⚠️ Your subscription has expired.")
    st.markdown("### ₹49/month — Renew your Pro Plan")
    st.info("💳 Add your Razorpay / Stripe payment link in `auth.py` upgrade buttons.")
    if st.button("Sign Out"):
        sign_out()
    st.stop()

# Custom CSS — Bloomberg Terminal meets FP&A precision
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Sora:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
}
.stApp {
    background: #0a0e1a;
    color: #e8eaf0;
}
section[data-testid="stSidebar"] {
    background: #0d1120;
    border-right: 1px solid #1e2d4a;
}
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    color: #8a9bb5 !important;
    font-size: 13px;
    font-family: 'JetBrains Mono', monospace;
}
section[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] label {
    padding: 10px 14px;
    border-radius: 6px;
    transition: background 0.15s;
}
section[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] label:hover {
    background: #1a2540;
}
h1, h2, h3 {
    font-family: 'Sora', sans-serif;
    color: #e8eaf0;
}
.metric-card {
    background: #111827;
    border: 1px solid #1e2d4a;
    border-radius: 8px;
    padding: 20px 24px;
    margin-bottom: 12px;
}
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 32px;
    font-weight: 700;
    color: #22d3a5;
}
.metric-label {
    font-size: 11px;
    color: #5a7090;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 4px;
}
.status-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
}
.badge-applied { background: #0f3a2a; color: #22d3a5; border: 1px solid #22d3a5; }
.badge-viewed  { background: #1a2a40; color: #60a5fa; border: 1px solid #3b82f6; }
.badge-pending { background: #2a1f10; color: #f59e0b; border: 1px solid #f59e0b; }
.badge-error   { background: #2a1010; color: #f87171; border: 1px solid #ef4444; }
.job-card {
    background: #111827;
    border: 1px solid #1e2d4a;
    border-left: 3px solid #22d3a5;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 10px;
    transition: border-color 0.15s;
}
.job-card:hover { border-left-color: #60a5fa; }
.job-title {
    font-size: 15px;
    font-weight: 600;
    color: #e8eaf0;
}
.job-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #5a7090;
    margin-top: 4px;
}
.match-score {
    font-family: 'JetBrains Mono', monospace;
    font-size: 18px;
    font-weight: 700;
}
.score-high { color: #22d3a5; }
.score-mid  { color: #f59e0b; }
.score-low  { color: #f87171; }
.stButton > button {
    background: #22d3a5;
    color: #0a0e1a;
    border: none;
    border-radius: 6px;
    font-family: 'Sora', sans-serif;
    font-weight: 600;
    font-size: 13px;
    padding: 10px 22px;
    transition: all 0.15s;
}
.stButton > button:hover {
    background: #1ab88e;
    transform: translateY(-1px);
}
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: #111827 !important;
    border: 1px solid #1e2d4a !important;
    color: #e8eaf0 !important;
    border-radius: 6px !important;
    font-family: 'Sora', sans-serif !important;
}
.terminal-log {
    background: #06080f;
    border: 1px solid #1e2d4a;
    border-radius: 8px;
    padding: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #22d3a5;
    max-height: 280px;
    overflow-y: auto;
    line-height: 1.8;
}
.section-header {
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    color: #3d5a80;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    border-bottom: 1px solid #1e2d4a;
    padding-bottom: 8px;
    margin: 24px 0 16px;
}
.stProgress > div > div { background: #22d3a5 !important; }
div[data-testid="stExpander"] {
    background: #111827;
    border: 1px solid #1e2d4a;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("""
    <div style='padding: 16px 0 24px; border-bottom: 1px solid #1e2d4a; margin-bottom: 20px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 18px; font-weight: 700; color: #22d3a5;'>⚡ JOB AGENT</div>
        <div style='font-size: 11px; color: #3d5a80; margin-top: 4px; font-family: JetBrains Mono, monospace;'>AI-POWERED · FULLY AUTOMATED</div>
    </div>
    """, unsafe_allow_html=True)

    # Show user email if logged in
    if user:
        email_display = user.get("email", "")
        st.markdown(f"""
        <div style='font-family: JetBrains Mono, monospace; font-size: 11px; color: #5a7090;
             background:#0d1120; border:1px solid #1e2d4a; border-radius:6px;
             padding: 8px 10px; margin-bottom:12px; overflow:hidden; text-overflow:ellipsis;'>
            👤 {email_display}
        </div>
        """, unsafe_allow_html=True)
        # Subscription banner
        render_subscription_banner(sub)

    page = st.radio("", [
        "🏠  Dashboard",
        "📄  Resume & Prefs",
        "🔍  Job Discovery",
        "🤖  AI Matching",
        "🚀  Auto Apply",
        "📊  Applications Log",
        "⚙️  Settings"
    ], label_visibility="collapsed")

    if user:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Sign Out", key="signout_btn"):
            sign_out()

# Route pages
page_key = page.split("  ")[-1].strip()

if page_key == "Dashboard":
    from pages import dashboard; dashboard.render()
elif page_key == "Resume & Prefs":
    from pages import resume; resume.render()
elif page_key == "Job Discovery":
    from pages import discovery; discovery.render()
elif page_key == "AI Matching":
    from pages import matching; matching.render()
elif page_key == "Auto Apply":
    from pages import apply; apply.render()
elif page_key == "Applications Log":
    from pages import log; log.render()
elif page_key == "Settings":
    from pages import settings; settings.render()
