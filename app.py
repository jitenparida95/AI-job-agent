import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="CareerOS — AI Career Operating System",
    page_icon="🚀", layout="wide",
    initial_sidebar_state="expanded"
)

# ── Auth ───────────────────────────────────────────────────────
try:
    from auth import require_auth, render_subscription_banner, sign_out, is_subscribed
    user, sub = require_auth()
except Exception as e:
    st.error(f"Startup error: {e}")
    st.stop()

# ── Safe name helper ───────────────────────────────────────────
def _first(u):
    try:
        n = (u.get("user_metadata",{}).get("name") or
             u.get("name") or
             u.get("email","").split("@")[0] or "there")
        parts = str(n).strip().split()
        return parts[0] if parts else "there"
    except Exception:
        return "there"

# ── Subscription gate ──────────────────────────────────────────
try:
    if user and sub and not is_subscribed(sub):
        try:
            from auth import _secrets_get
            rp = _secrets_get("RAZORPAY_LINK","https://rzp.io/rzp/StnjPRq")
        except Exception:
            rp = "https://rzp.io/rzp/StnjPRq"
        st.error("⚠️ Your trial has expired.")
        st.link_button("🚀 Reactivate — ₹49/month", rp)
        if st.button("Sign Out"):
            sign_out()
        st.stop()
except Exception:
    pass

# ── Load secrets into settings ─────────────────────────────────
try:
    from core.store import get_settings, save_settings
    s = get_settings()
    changed = False
    for key in ["GROQ_API_KEY","JSEARCH_API_KEY"]:
        store_key = key.lower()
        try:
            val = st.secrets.get(key,"")
        except Exception:
            val = ""
        if val and not s.get(store_key):
            s[store_key] = val
            changed = True
    if changed:
        save_settings(s)
except Exception:
    pass

# ── CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#080c18;color:#e2e8f0;}
section[data-testid="stSidebar"]{background:#0c1020;border-right:1px solid #1a2540;}
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span{color:#7a8faa!important;font-size:13px;}
h1,h2,h3{color:#e2e8f0;}
.metric-card{background:linear-gradient(135deg,#0f1629,#111827);border:1px solid #1e2d4a;border-radius:12px;padding:20px 22px;margin-bottom:12px;position:relative;overflow:hidden;}
.metric-card::before{content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:linear-gradient(180deg,#6366f1,#22d3a5);}
.metric-value{font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:700;color:#e2e8f0;line-height:1;}
.metric-label{font-size:11px;color:#4a6080;text-transform:uppercase;letter-spacing:.1em;margin-top:6px;font-weight:500;}
.status-badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:10px;font-family:'JetBrains Mono',monospace;font-weight:600;}
.badge-applied{background:#052e16;color:#22d3a5;border:1px solid #166534;}
.badge-interview{background:#1e1b4b;color:#a5b4fc;border:1px solid #3730a3;}
.badge-offer{background:#451a03;color:#fbbf24;border:1px solid #d97706;}
.badge-rejected{background:#1c0a0a;color:#f87171;border:1px solid #7f1d1d;}
.badge-pending{background:#1c1300;color:#fbbf24;border:1px solid #92400e;}
.job-card{background:#0f1629;border:1px solid #1a2540;border-left:3px solid #6366f1;border-radius:10px;padding:16px 20px;margin-bottom:10px;transition:all .2s;}
.job-card:hover{border-left-color:#22d3a5;background:#111827;}
.job-title{font-size:15px;font-weight:600;color:#e2e8f0;}
.job-company{color:#7a8faa;font-size:13px;}
.job-meta{font-family:'JetBrains Mono',monospace;font-size:11px;color:#4a6080;margin-top:6px;}
.score-high{color:#22d3a5;font-family:'JetBrains Mono',monospace;font-weight:700;}
.score-mid{color:#f59e0b;font-family:'JetBrains Mono',monospace;font-weight:700;}
.score-low{color:#f87171;font-family:'JetBrains Mono',monospace;font-weight:700;}
.stButton>button{background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff;border:none;border-radius:8px;font-family:'Inter',sans-serif;font-weight:600;font-size:13px;padding:10px 22px;transition:all .2s;}
.stButton>button:hover{background:linear-gradient(135deg,#4f46e5,#4338ca);transform:translateY(-1px);box-shadow:0 4px 20px rgba(99,102,241,.4);}
.stTextInput input,.stTextArea textarea{background:#0f1629!important;border:1px solid #1e2d4a!important;color:#e2e8f0!important;border-radius:8px!important;font-family:'Inter',sans-serif!important;}
.terminal-log{background:#060912;border:1px solid #1a2540;border-radius:10px;padding:16px;font-family:'JetBrains Mono',monospace;font-size:12px;color:#22d3a5;max-height:260px;overflow-y:auto;line-height:1.9;}
.section-header{font-size:10px;font-family:'JetBrains Mono',monospace;color:#2d4060;text-transform:uppercase;letter-spacing:.2em;border-bottom:1px solid #1a2540;padding-bottom:8px;margin:28px 0 16px;font-weight:600;}
.insight-card{background:#0f1629;border:1px solid #1a2540;border-radius:10px;padding:16px 20px;margin-bottom:10px;}
.insight-card.warning{border-left:3px solid #f59e0b;}
.insight-card.success{border-left:3px solid #22d3a5;}
.insight-card.info{border-left:3px solid #6366f1;}
.insight-card.danger{border-left:3px solid #f87171;}
.upgrade-banner{background:linear-gradient(135deg,#1e1b4b,#312e81);border:1px solid #4338ca;border-radius:12px;padding:20px 24px;margin:16px 0;text-align:center;}
.prob-bar-wrap{background:#1a2540;border-radius:6px;height:8px;overflow:hidden;margin-top:6px;}
.prob-bar-fill{height:100%;border-radius:6px;background:linear-gradient(90deg,#6366f1,#22d3a5);}
.stProgress>div>div{background:linear-gradient(90deg,#6366f1,#22d3a5)!important;border-radius:4px;}
div[data-testid="stExpander"]{background:#0f1629;border:1px solid #1a2540;border-radius:10px;}
.stTabs [data-baseweb="tab-list"]{background:#0c1020;border-radius:8px;padding:4px;}
.stTabs [data-baseweb="tab"]{color:#7a8faa;font-size:13px;}
.stTabs [aria-selected="true"]{background:#1a2540;color:#e2e8f0;border-radius:6px;}
.step-number{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;background:linear-gradient(135deg,#6366f1,#4f46e5);border-radius:50%;font-size:12px;font-weight:700;color:white;margin-right:10px;flex-shrink:0;}
</style>
""", unsafe_allow_html=True)

# ── Page state init ────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Command Center"

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
<div style='padding:16px 0 20px;border-bottom:1px solid #1a2540;margin-bottom:16px;'>
  <div style='font-size:17px;font-weight:800;color:#e2e8f0;'>🚀 <span style='color:#6366f1;'>Career</span>OS</div>
  <div style='font-size:10px;color:#2d4060;margin-top:3px;font-family:JetBrains Mono,monospace;letter-spacing:.1em;'>AI CAREER OPERATING SYSTEM</div>
</div>
<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#4a6080;background:#0c1020;border:1px solid #1a2540;border-radius:6px;padding:8px 10px;margin-bottom:12px;overflow:hidden;text-overflow:ellipsis;'>
  👤 {user.get("email","") if user else ""}
</div>
""", unsafe_allow_html=True)

    try:
        render_subscription_banner(sub)
    except Exception:
        pass

    pages = [
        ("🏠","Command Center"),
        ("🧠","Career Intelligence"),
        ("📄","Resume Optimizer"),
        ("✨","Resume Rewriter"),
        ("🔍","Job Discovery"),
        ("🎯","AI Job Matching"),
        ("✉️","Application Engine"),
        ("🚀","Auto Apply"),
        ("📊","Tracker & Analytics"),
        ("🤖","AI Career Coach"),
        ("⚙️","Settings"),
    ]

    for icon, label in pages:
        active = st.session_state.page == label
        style = "font-weight:600;color:#a5b4fc!important;" if active else ""
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
            st.session_state.page = label
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        sign_out()

# ── Page routing ───────────────────────────────────────────────
_MAP = {
    "Command Center":      "dashboard",
    "Career Intelligence": "career_intelligence",
    "Resume Optimizer":    "resume_optimizer",
    "Resume Rewriter":     "resume_rewriter",
    "Job Discovery":       "discovery",
    "AI Job Matching":     "matching",
    "Application Engine":  "application_engine",
    "Auto Apply":          "apply",
    "Tracker & Analytics": "tracker",
    "AI Career Coach":     "coach",
    "Settings":            "settings",
}

def _nav(label):
    st.session_state.page = label
    st.rerun()

# Expose nav function to pages via session state
st.session_state._nav = _nav

module = _MAP.get(st.session_state.page, "dashboard")
try:
    import importlib
    mod = importlib.import_module(f"pages.{module}")
    mod.render()
except Exception as e:
    st.markdown(f"""
<div style='background:#1c0a0a;border:1px solid #7f1d1d;border-radius:8px;padding:16px 20px;margin:20px 0;'>
  <div style='color:#f87171;font-weight:600;margin-bottom:6px;'>Something went wrong loading this page.</div>
  <div style='color:#7a8faa;font-size:13px;'>Try refreshing or switching to another section.</div>
</div>""", unsafe_allow_html=True)
    with st.expander("Technical details"):
        st.exception(e)
