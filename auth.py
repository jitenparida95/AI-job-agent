"""
Authentication & Subscription layer for CareerOS.
Works in 3 modes:
  1. Full Supabase (SUPABASE_URL + SUPABASE_ANON_KEY configured)
  2. Demo mode (no Supabase — simple email gate, local session)
  3. Degraded mode (any error — falls back to demo)
"""

import streamlit as st
import requests
from datetime import datetime, timezone, date, timedelta


# ── Config helpers ────────────────────────────────────────────

def _cfg():
    try:
        return {
            "url": st.secrets.get("SUPABASE_URL", ""),
            "key": st.secrets.get("SUPABASE_ANON_KEY", ""),
        }
    except Exception:
        return {"url": "", "key": ""}

def _supabase_configured():
    cfg = _cfg()
    return bool(cfg["url"] and cfg["key"])

def _headers(token=None):
    cfg = _cfg()
    h = {"apikey": cfg["key"], "Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

def _base():
    return _cfg()["url"]


# ── Auth API calls ─────────────────────────────────────────────

def sign_up(email: str, password: str) -> dict:
    try:
        r = requests.post(
            f"{_base()}/auth/v1/signup",
            headers=_headers(),
            json={"email": email, "password": password},
            timeout=10,
        )
        data = r.json()
        if r.status_code in (200, 201) and data.get("user"):
            try:
                _create_subscription(data["user"]["id"], data.get("access_token", ""))
            except Exception:
                pass
            return {"success": True, "user": data["user"], "session": data}
        return {"success": False, "error": data.get("error_description") or data.get("msg") or "Signup failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_in(email: str, password: str) -> dict:
    try:
        r = requests.post(
            f"{_base()}/auth/v1/token?grant_type=password",
            headers=_headers(),
            json={"email": email, "password": password},
            timeout=10,
        )
        data = r.json()
        if r.status_code == 200 and data.get("access_token"):
            return {"success": True, "user": data["user"], "session": data}
        return {"success": False, "error": data.get("error_description") or "Invalid credentials"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_out():
    for key in ["auth_user", "auth_session", "subscription", "demo_user"]:
        st.session_state.pop(key, None)
    st.rerun()


def reset_password(email: str) -> dict:
    try:
        r = requests.post(
            f"{_base()}/auth/v1/recover",
            headers=_headers(),
            json={"email": email},
            timeout=10,
        )
        return {"success": r.status_code == 200}
    except Exception:
        return {"success": False}


# ── Subscription ──────────────────────────────────────────────

def _create_subscription(user_id: str, token: str):
    try:
        requests.post(
            f"{_base()}/rest/v1/subscriptions",
            headers={**_headers(token), "Prefer": "return=minimal"},
            json={"user_id": user_id, "status": "trial", "plan": "pro"},
            timeout=10,
        )
    except Exception:
        pass


def get_subscription(token: str) -> dict:
    try:
        r = requests.get(
            f"{_base()}/rest/v1/subscriptions?select=*&order=created_at.desc&limit=1",
            headers=_headers(token),
            timeout=10,
        )
        if r.status_code == 200 and r.json():
            return r.json()[0]
    except Exception:
        pass
    return None


def is_subscribed(sub: dict) -> bool:
    if not sub:
        return True  # default allow in demo mode
    status = sub.get("status", "")
    if status == "active":
        end = sub.get("current_period_end")
        if end:
            try:
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                return end_dt > datetime.now(timezone.utc)
            except Exception:
                pass
        return True
    if status == "trial":
        end = sub.get("trial_ends_at")
        if end:
            try:
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                return end_dt > datetime.now(timezone.utc)
            except Exception:
                pass
        return True  # assume active if can't parse
    return True  # default allow


def days_left(sub: dict) -> int:
    if not sub:
        return 7
    end_key = "trial_ends_at" if sub.get("status") == "trial" else "current_period_end"
    end = sub.get(end_key)
    if end:
        try:
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            delta = end_dt - datetime.now(timezone.utc)
            return max(0, delta.days)
        except Exception:
            pass
    return 7


# ── Demo mode auth ─────────────────────────────────────────────

def _demo_user(email: str, name: str = "") -> dict:
    return {
        "id": f"demo_{email.split('@')[0]}",
        "email": email,
        "user_metadata": {"name": name or email.split("@")[0]},
    }

def _demo_sub() -> dict:
    trial_end = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    return {"status": "trial", "plan": "pro", "trial_ends_at": trial_end}


# ── Streamlit gate ─────────────────────────────────────────────

def require_auth():
    """
    Returns (user, subscription). Never crashes.
    Falls back to demo mode if Supabase not configured.
    """
    # Already authenticated via Supabase
    if "auth_user" in st.session_state and "auth_session" in st.session_state:
        user = st.session_state["auth_user"]
        sub = st.session_state.get("subscription")
        if sub is None and _supabase_configured():
            try:
                token = st.session_state["auth_session"].get("access_token", "")
                sub = get_subscription(token)
            except Exception:
                sub = _demo_sub()
            st.session_state["subscription"] = sub or _demo_sub()
        return user, st.session_state.get("subscription", _demo_sub())

    # Already in demo mode
    if "demo_user" in st.session_state:
        return st.session_state["demo_user"], _demo_sub()

    # Show auth page
    _render_auth_page()
    st.stop()


def _render_auth_page():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #080c18; color: #e2e8f0; }
    .stTextInput input { background: #0d1120 !important; border: 1px solid #1e2d4a !important; color: #e8eaf0 !important; border-radius: 6px !important; }
    .stButton > button { background: linear-gradient(135deg,#6366f1,#4f46e5) !important; color: #fff !important; border: none !important; border-radius: 6px !important; font-weight: 600 !important; font-size: 14px !important; padding: 10px 0 !important; }
    .stButton > button:hover { background: linear-gradient(135deg,#4f46e5,#4338ca) !important; }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown("""
        <div style='text-align:center; padding: 40px 0 24px;'>
            <div style='font-size:36px; margin-bottom:8px;'>🚀</div>
            <div style='font-size:24px; font-weight:800; color:#e2e8f0;'><span style='color:#6366f1;'>Career</span>OS</div>
            <div style='font-size:10px; color:#334155; font-family:JetBrains Mono,monospace; letter-spacing:.1em; margin-top:4px;'>AI CAREER OPERATING SYSTEM</div>
        </div>
        <div style='background:linear-gradient(135deg,#1e1b4b,#312e81); border:1px solid #4338ca; border-radius:10px; padding:14px 18px; margin-bottom:20px; text-align:center;'>
            <div style='font-size:13px; color:#a5b4fc;'>✨ Pro Plan — ₹49/month · 7-day free trial</div>
            <div style='font-size:12px; color:#6366f1; margin-top:4px;'>✓ Career Intelligence  ✓ Resume Optimizer  ✓ AI Coach  ✓ Auto Apply</div>
        </div>
        """, unsafe_allow_html=True)

        if _supabase_configured():
            tab_login, tab_signup = st.tabs(["🔑  Sign In", "✨  Create Account"])

            with tab_login:
                st.markdown("<br>", unsafe_allow_html=True)
                email = st.text_input("Email", key="login_email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
                if st.button("Sign In →", key="btn_login", use_container_width=True):
                    if not email or not password:
                        st.error("Please fill in all fields")
                    else:
                        with st.spinner("Signing in..."):
                            res = sign_in(email, password)
                        if res["success"]:
                            st.session_state["auth_user"] = res["user"]
                            st.session_state["auth_session"] = res["session"]
                            st.rerun()
                        else:
                            st.error(f"❌ {res['error']}")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Forgot password?", key="btn_forgot"):
                    if email:
                        reset_password(email)
                        st.info("Password reset email sent!")
                    else:
                        st.warning("Enter your email first")

            with tab_signup:
                st.markdown("<br>", unsafe_allow_html=True)
                s_email = st.text_input("Email", key="signup_email", placeholder="you@example.com")
                s_pass = st.text_input("Password", type="password", key="signup_pass", placeholder="Min 6 characters")
                s_pass2 = st.text_input("Confirm Password", type="password", key="signup_pass2")
                st.caption("🎁 Start with a 7-day free trial. No credit card needed.")
                if st.button("Create Account & Start Free Trial →", key="btn_signup", use_container_width=True):
                    if not s_email or not s_pass:
                        st.error("Please fill in all fields")
                    elif s_pass != s_pass2:
                        st.error("Passwords don't match")
                    elif len(s_pass) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        with st.spinner("Creating your account..."):
                            res = sign_up(s_email, s_pass)
                        if res["success"]:
                            st.session_state["auth_user"] = res["user"]
                            st.session_state["auth_session"] = res["session"]
                            st.success("🎉 Account created! Welcome to CareerOS")
                            st.rerun()
                        else:
                            st.error(f"❌ {res['error']}")
        else:
            # Demo mode — simple email gate
            st.markdown("""
            <div style='background:#111827; border:1px solid #1e2d4a; border-radius:8px; padding:12px 16px; margin-bottom:16px; font-size:12px; color:#475569;'>
                ℹ️ Running in demo mode (Supabase not configured). Enter any email to continue.
            </div>
            """, unsafe_allow_html=True)
            demo_email = st.text_input("Email address", placeholder="your@email.com", key="demo_email")
            demo_name = st.text_input("Your name (optional)", placeholder="Jitendra Parida", key="demo_name")
            if st.button("Enter CareerOS →", key="btn_demo", use_container_width=True):
                if "@" in (demo_email or ""):
                    st.session_state["demo_user"] = _demo_user(demo_email.strip(), demo_name.strip())
                    st.rerun()
                else:
                    st.error("Please enter a valid email address")


def render_subscription_banner(sub: dict):
    """Show plan banner in sidebar. Never crashes."""
    if not sub:
        sub = _demo_sub()

    status = sub.get("status", "trial")
    d = days_left(sub)

    try:
        razorpay_link = st.secrets.get("RAZORPAY_LINK", "https://rzp.io/rzp/StnjPRq")
    except Exception:
        razorpay_link = "https://rzp.io/rzp/StnjPRq"

    if status == "active":
        st.sidebar.markdown("""
        <div style='background:#052e16; border:1px solid #166534; border-radius:8px; padding:10px 12px; margin:10px 0;'>
            <div style='font-family:JetBrains Mono,monospace; font-size:11px; color:#22c55e;'>⚡ PRO PLAN ACTIVE</div>
        </div>
        """, unsafe_allow_html=True)
    elif status == "trial":
        color = "#f59e0b" if d <= 3 else "#6366f1"
        st.sidebar.markdown(f"""
        <div style='background:#111827; border:1px solid {color}; border-radius:8px; padding:10px 12px; margin:10px 0;'>
            <div style='font-family:JetBrains Mono,monospace; font-size:11px; color:{color};'>🎁 FREE TRIAL · {d} day{"s" if d != 1 else ""} left</div>
            <div style='font-size:11px; color:#475569; margin-top:3px;'>₹49/month after trial</div>
        </div>
        """, unsafe_allow_html=True)
        st.sidebar.link_button("⚡ Upgrade to Pro", razorpay_link, use_container_width=True)
