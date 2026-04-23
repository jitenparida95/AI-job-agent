"""
Authentication & Subscription layer for JobAgent AI.
Uses Supabase for auth + a 'subscriptions' table for plan tracking.

Supabase setup:
  1. Create project at supabase.com
  2. Run this SQL in SQL editor:

     CREATE TABLE subscriptions (
       id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
       user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
       status text DEFAULT 'trial',   -- 'trial' | 'active' | 'expired'
       plan text DEFAULT 'pro',
       trial_ends_at timestamptz DEFAULT (now() + interval '7 days'),
       current_period_end timestamptz,
       created_at timestamptz DEFAULT now()
     );
     ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
     CREATE POLICY "Users can read own sub" ON subscriptions
       FOR SELECT USING (auth.uid() = user_id);

  3. Add to secrets.toml (Streamlit Cloud) or .streamlit/secrets.toml (local):
     SUPABASE_URL = "https://xxxx.supabase.co"
     SUPABASE_ANON_KEY = "eyJh..."
"""

import streamlit as st
import requests
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────

def _cfg():
    return {
        "url": st.secrets.get("SUPABASE_URL", ""),
        "key": st.secrets.get("SUPABASE_ANON_KEY", ""),
    }

def _headers(token=None):
    cfg = _cfg()
    h = {
        "apikey": cfg["key"],
        "Content-Type": "application/json",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

def _base():
    return _cfg()["url"]


# ── Auth API calls ─────────────────────────────────────────────

def sign_up(email: str, password: str) -> dict:
    """Returns {success, user, session, error}"""
    r = requests.post(
        f"{_base()}/auth/v1/signup",
        headers=_headers(),
        json={"email": email, "password": password},
        timeout=10,
    )
    data = r.json()
    if r.status_code in (200, 201) and data.get("user"):
        _create_subscription(data["user"]["id"], data.get("access_token",""))
        return {"success": True, "user": data["user"], "session": data}
    return {"success": False, "error": data.get("error_description") or data.get("msg") or "Signup failed"}


def sign_in(email: str, password: str) -> dict:
    """Returns {success, user, session, error}"""
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


def sign_out():
    st.session_state.pop("auth_user", None)
    st.session_state.pop("auth_session", None)
    st.session_state.pop("subscription", None)
    st.rerun()


def reset_password(email: str) -> dict:
    r = requests.post(
        f"{_base()}/auth/v1/recover",
        headers=_headers(),
        json={"email": email},
        timeout=10,
    )
    return {"success": r.status_code == 200}


# ── Subscription ──────────────────────────────────────────────

def _create_subscription(user_id: str, token: str):
    """Called once on signup — creates trial subscription row."""
    requests.post(
        f"{_base()}/rest/v1/subscriptions",
        headers={**_headers(token), "Prefer": "return=minimal"},
        json={"user_id": user_id, "status": "trial", "plan": "pro"},
        timeout=10,
    )


def get_subscription(token: str) -> dict:
    """Returns subscription dict or None."""
    r = requests.get(
        f"{_base()}/rest/v1/subscriptions?select=*&order=created_at.desc&limit=1",
        headers=_headers(token),
        timeout=10,
    )
    if r.status_code == 200 and r.json():
        return r.json()[0]
    return None


def is_subscribed(sub: dict) -> bool:
    """Check if user has active access (trial or paid)."""
    if not sub:
        return False
    if sub["status"] == "active":
        # Check period end
        end = sub.get("current_period_end")
        if end:
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            return end_dt > datetime.now(timezone.utc)
        return True
    if sub["status"] == "trial":
        end = sub.get("trial_ends_at")
        if end:
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            return end_dt > datetime.now(timezone.utc)
    return False


def days_left(sub: dict) -> int:
    """Days remaining in trial/subscription."""
    if not sub:
        return 0
    end = sub.get("trial_ends_at") if sub["status"] == "trial" else sub.get("current_period_end")
    if end:
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        delta = end_dt - datetime.now(timezone.utc)
        return max(0, delta.days)
    return 0


# ── Streamlit gate ─────────────────────────────────────────────

def require_auth():
    """
    Call at the top of app.py. Shows login/signup if not authenticated.
    Returns (user, subscription) if authenticated, else stops the page.
    """
    # Check if Supabase is configured
    cfg = _cfg()
    if not cfg["url"] or not cfg["key"]:
        st.warning("⚠️ Supabase not configured — running in demo mode (no auth)")
        return None, {"status": "active"}

    # Already logged in?
    if "auth_user" in st.session_state and "auth_session" in st.session_state:
        user = st.session_state["auth_user"]
        sub = st.session_state.get("subscription")
        if not sub:
            sub = get_subscription(st.session_state["auth_session"]["access_token"])
            st.session_state["subscription"] = sub
        return user, sub

    # Show auth UI
    _render_auth_page()
    st.stop()


def _render_auth_page():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Sora:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
    .stApp { background: #0a0e1a; color: #e8eaf0; }
    .auth-box {
        max-width: 440px;
        margin: 60px auto 0;
        background: #111827;
        border: 1px solid #1e2d4a;
        border-radius: 12px;
        padding: 40px 36px;
    }
    .auth-logo {
        font-family: 'JetBrains Mono', monospace;
        font-size: 22px;
        font-weight: 700;
        color: #22d3a5;
        margin-bottom: 6px;
    }
    .auth-tagline {
        font-size: 13px;
        color: #5a7090;
        margin-bottom: 28px;
        font-family: 'JetBrains Mono', monospace;
    }
    .price-badge {
        background: #0f3a2a;
        border: 1px solid #22d3a5;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 12px;
        color: #22d3a5;
        font-family: 'JetBrains Mono', monospace;
        display: inline-block;
        margin-bottom: 20px;
    }
    .feature-list {
        font-size: 13px;
        color: #8a9bb5;
        line-height: 2;
        margin-bottom: 24px;
    }
    .stTextInput input {
        background: #0d1120 !important;
        border: 1px solid #1e2d4a !important;
        color: #e8eaf0 !important;
        border-radius: 6px !important;
    }
    .stButton > button {
        background: #22d3a5 !important;
        color: #0a0e1a !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 10px 0 !important;
        width: 100%;
    }
    .stButton > button:hover { background: #1ab88e !important; }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown("""
        <div class='auth-logo'>⚡ JOB AGENT AI</div>
        <div class='auth-tagline'>AI-POWERED · FULLY AUTOMATED</div>
        <div class='price-badge'>🚀 Pro Plan — ₹49/month · 7-day free trial</div>
        <div class='feature-list'>
          ✓ Auto-apply to 30+ jobs/day on Naukri & LinkedIn<br>
          ✓ AI cover letter generation (Groq LLM)<br>
          ✓ Smart match scoring<br>
          ✓ Applications dashboard & log
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["🔑  Sign In", "✨  Create Account"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            email = st.text_input("Email", key="login_email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
            if st.button("Sign In", key="btn_login"):
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
            s_pass2 = st.text_input("Confirm Password", type="password", key="signup_pass2", placeholder="Repeat password")
            st.caption("🎁 Start with a 7-day free trial. No credit card needed.")
            if st.button("Create Account & Start Free Trial", key="btn_signup"):
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
                        st.success("🎉 Account created! Welcome to JobAgent AI")
                        st.rerun()
                    else:
                        st.error(f"❌ {res['error']}")


def render_subscription_banner(sub: dict):
    """Show banner in sidebar for trial users or expired."""
    if not sub:
        return
    if sub["status"] == "trial":
        d = days_left(sub)
        color = "#f59e0b" if d <= 3 else "#22d3a5"
        st.sidebar.markdown(f"""
        <div style='background:#111827; border:1px solid {color}; border-radius:8px; padding:12px 14px; margin:12px 0;'>
            <div style='font-family: JetBrains Mono, monospace; font-size:11px; color:{color};'>
                🎁 FREE TRIAL · {d} day{"s" if d != 1 else ""} left
            </div>
            <div style='font-size:11px; color:#5a7090; margin-top:4px;'>₹49/month after trial</div>
        </div>
        """, unsafe_allow_html=True)
        if st.sidebar.button("⚡ Upgrade to Pro", key="upgrade_btn"):
            st.sidebar.info("Add your Razorpay/Stripe link here to take payments.")
    elif sub["status"] == "expired":
        st.sidebar.error("⚠️ Subscription expired. Please renew.")
        if st.sidebar.button("🔄 Renew Plan"):
            st.sidebar.info("Add your payment link here.")
