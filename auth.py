"""
CareerOS Authentication — Supabase + demo fallback.
Never crashes. Works with or without Supabase configured.
"""
import streamlit as st
import requests
from datetime import datetime, timezone, timedelta


def _secrets_get(key, default=""):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def _supabase_ok():
    return bool(_secrets_get("SUPABASE_URL") and _secrets_get("SUPABASE_ANON_KEY"))


def _base():
    return _secrets_get("SUPABASE_URL")


def _headers(token=None):
    h = {"apikey": _secrets_get("SUPABASE_ANON_KEY"), "Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


# ── Auth calls ────────────────────────────────────────────────

def sign_up(email, password):
    try:
        r = requests.post(f"{_base()}/auth/v1/signup", headers=_headers(),
                          json={"email": email, "password": password}, timeout=10)
        d = r.json()
        if r.status_code in (200, 201) and d.get("user"):
            try:
                requests.post(f"{_base()}/rest/v1/subscriptions",
                              headers={**_headers(d.get("access_token","")), "Prefer":"return=minimal"},
                              json={"user_id": d["user"]["id"], "status":"trial","plan":"pro"}, timeout=8)
            except Exception:
                pass
            return {"success": True, "user": d["user"], "session": d}
        return {"success": False, "error": d.get("error_description") or d.get("msg") or "Signup failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_in(email, password):
    try:
        r = requests.post(f"{_base()}/auth/v1/token?grant_type=password", headers=_headers(),
                          json={"email": email, "password": password}, timeout=10)
        d = r.json()
        if r.status_code == 200 and d.get("access_token"):
            return {"success": True, "user": d["user"], "session": d}
        return {"success": False, "error": d.get("error_description") or "Invalid credentials"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_out():
    for k in ["auth_user", "auth_session", "subscription", "demo_email"]:
        st.session_state.pop(k, None)
    st.rerun()


def reset_password(email):
    try:
        r = requests.post(f"{_base()}/auth/v1/recover", headers=_headers(), json={"email": email}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def get_subscription(token):
    try:
        r = requests.get(f"{_base()}/rest/v1/subscriptions?select=*&order=created_at.desc&limit=1",
                         headers=_headers(token), timeout=10)
        if r.status_code == 200 and r.json():
            return r.json()[0]
    except Exception:
        pass
    return None


def is_subscribed(sub):
    """Always returns True in demo mode. Checks dates in Supabase mode."""
    if not sub:
        return True
    status = sub.get("status", "trial")
    if status == "active":
        end = sub.get("current_period_end")
        if end:
            try:
                return datetime.fromisoformat(end.replace("Z","+00:00")) > datetime.now(timezone.utc)
            except Exception:
                pass
        return True
    if status == "trial":
        end = sub.get("trial_ends_at")
        if end:
            try:
                return datetime.fromisoformat(end.replace("Z","+00:00")) > datetime.now(timezone.utc)
            except Exception:
                pass
    return True  # default allow


def days_left(sub):
    if not sub:
        return 7
    key = "trial_ends_at" if sub.get("status") == "trial" else "current_period_end"
    end = sub.get(key)
    if end:
        try:
            delta = datetime.fromisoformat(end.replace("Z","+00:00")) - datetime.now(timezone.utc)
            return max(0, delta.days)
        except Exception:
            pass
    return 7


# ── Main gate ─────────────────────────────────────────────────

def require_auth():
    """Returns (user, sub). Never crashes. Falls back to demo mode."""
    # Supabase session
    if "auth_user" in st.session_state and "auth_session" in st.session_state:
        user = st.session_state["auth_user"]
        sub = st.session_state.get("subscription")
        if sub is None:
            try:
                sub = get_subscription(st.session_state["auth_session"].get("access_token",""))
            except Exception:
                sub = None
            st.session_state["subscription"] = sub or _demo_sub()
        return user, st.session_state.get("subscription", _demo_sub())

    # Demo session
    if "demo_email" in st.session_state:
        email = st.session_state["demo_email"]
        user = {"id": f"demo_{email.split('@')[0]}", "email": email,
                "user_metadata": {"name": email.split("@")[0].replace(".", " ").title()}}
        return user, _demo_sub()

    # Show login UI
    _render_login()
    st.stop()


def _demo_sub():
    end = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    return {"status": "trial", "plan": "pro", "trial_ends_at": end}


def _render_login():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#080c18;color:#e2e8f0;}
.stTextInput input{background:#0d1120!important;border:1px solid #1e2d4a!important;color:#e8eaf0!important;border-radius:6px!important;}
.stButton>button{background:linear-gradient(135deg,#6366f1,#4f46e5)!important;color:#fff!important;border:none!important;border-radius:6px!important;font-weight:600!important;font-size:14px!important;width:100%;}
</style>""", unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1,2,1])
    with col_m:
        st.markdown("""
<div style='text-align:center;padding:40px 0 24px;'>
  <div style='font-size:40px;margin-bottom:8px;'>🚀</div>
  <div style='font-size:26px;font-weight:800;color:#e2e8f0;'><span style='color:#6366f1;'>Career</span>OS</div>
  <div style='font-size:10px;color:#334155;font-family:JetBrains Mono,monospace;letter-spacing:.12em;margin-top:4px;'>AI CAREER OPERATING SYSTEM</div>
</div>
<div style='background:linear-gradient(135deg,#1e1b4b,#312e81);border:1px solid #4338ca;border-radius:10px;padding:14px 18px;margin-bottom:20px;text-align:center;'>
  <div style='font-size:13px;color:#a5b4fc;'>✨ Pro Plan — ₹49/month · 7-day free trial</div>
  <div style='font-size:11px;color:#6366f1;margin-top:4px;'>✓ Career Intelligence  ✓ Resume Optimizer  ✓ AI Coach  ✓ Auto Apply</div>
</div>
""", unsafe_allow_html=True)

        if _supabase_ok():
            tab_in, tab_up = st.tabs(["🔑  Sign In", "✨  Create Account"])
            with tab_in:
                st.markdown("<br>", unsafe_allow_html=True)
                em = st.text_input("Email", key="li_em", placeholder="you@example.com")
                pw = st.text_input("Password", type="password", key="li_pw", placeholder="••••••••")
                if st.button("Sign In →", key="btn_li"):
                    if not em or not pw:
                        st.error("Fill in all fields")
                    else:
                        with st.spinner("Signing in..."):
                            res = sign_in(em, pw)
                        if res["success"]:
                            st.session_state["auth_user"] = res["user"]
                            st.session_state["auth_session"] = res["session"]
                            st.rerun()
                        else:
                            st.error(f"❌ {res['error']}")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Forgot password?", key="btn_forgot"):
                    if em:
                        reset_password(em)
                        st.info("Reset email sent!")
                    else:
                        st.warning("Enter email first")
            with tab_up:
                st.markdown("<br>", unsafe_allow_html=True)
                se = st.text_input("Email", key="su_em", placeholder="you@example.com")
                sp = st.text_input("Password", type="password", key="su_pw", placeholder="Min 6 chars")
                sp2 = st.text_input("Confirm", type="password", key="su_pw2")
                st.caption("🎁 7-day free trial. No credit card needed.")
                if st.button("Create Account →", key="btn_su"):
                    if not se or not sp:
                        st.error("Fill in all fields")
                    elif sp != sp2:
                        st.error("Passwords don't match")
                    elif len(sp) < 6:
                        st.error("Min 6 characters")
                    else:
                        with st.spinner("Creating account..."):
                            res = sign_up(se, sp)
                        if res["success"]:
                            st.session_state["auth_user"] = res["user"]
                            st.session_state["auth_session"] = res["session"]
                            st.success("🎉 Welcome to CareerOS!")
                            st.rerun()
                        else:
                            st.error(f"❌ {res['error']}")
        else:
            # Demo mode — email gate only
            st.markdown("""<div style='background:#111827;border:1px solid #1e2d4a;border-radius:8px;padding:10px 14px;margin-bottom:14px;font-size:12px;color:#475569;'>
Running in demo mode. Enter any email to access CareerOS.</div>""", unsafe_allow_html=True)
            demo_em = st.text_input("Email", placeholder="your@email.com", key="d_em")
            if st.button("Enter CareerOS →", key="btn_demo"):
                if "@" in (demo_em or ""):
                    st.session_state["demo_email"] = demo_em.strip()
                    st.rerun()
                else:
                    st.error("Enter a valid email")


def render_subscription_banner(sub):
    """Sidebar plan banner. Never crashes."""
    try:
        sub = sub or _demo_sub()
        status = sub.get("status", "trial")
        d = days_left(sub)
        razorpay = _secrets_get("RAZORPAY_LINK", "https://rzp.io/rzp/StnjPRq")

        if status == "active":
            st.sidebar.markdown("""<div style='background:#052e16;border:1px solid #166534;border-radius:8px;padding:8px 12px;margin:8px 0;'>
<div style='font-family:JetBrains Mono,monospace;font-size:11px;color:#22c55e;'>⚡ PRO ACTIVE</div></div>""", unsafe_allow_html=True)
        else:
            color = "#f59e0b" if d <= 3 else "#6366f1"
            st.sidebar.markdown(f"""<div style='background:#111827;border:1px solid {color};border-radius:8px;padding:8px 12px;margin:8px 0;'>
<div style='font-family:JetBrains Mono,monospace;font-size:11px;color:{color};'>🎁 FREE TRIAL · {d} day{"s" if d!=1 else ""} left</div>
<div style='font-size:11px;color:#475569;margin-top:2px;'>₹49/month after trial</div></div>""", unsafe_allow_html=True)
            st.sidebar.link_button("⚡ Upgrade to Pro", razorpay, use_container_width=True)
    except Exception:
        pass
