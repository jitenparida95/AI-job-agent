"""pages/dashboard.py – Dashboard page."""
import streamlit as st

st.set_page_config(
    page_title="Dashboard – CareerOS",
    page_icon="🏠",
    layout="wide",
)

st.markdown("""
<style>
.stApp { background-color: #111827; color: #F9FAFB; }
section[data-testid="stSidebar"] { background-color: #0F172A; }
#MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
.stButton > button { border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

import utils.session as session
session.init_session()

if not session.get("authenticated"):
    st.warning("Please sign in to continue.")
    st.stop()

from components.sidebar import render_sidebar
render_sidebar()

def render() -> None:
    session.init_session()
    first_name = session.get_first_name()   # ← safe, never IndexError
    plan = session.get("user_plan", "free")
    user_id = session.get("user_id")

    # ─── Header ─────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="padding:8px 0 24px;">
            <h1 style="font-size:28px;font-weight:800;margin:0;">
                Welcome back, {first_name}! 👋
            </h1>
            <p style="color:#9CA3AF;margin-top:4px;">
                {datetime.now().strftime('%A, %d %B %Y')} ·
                {'⭐ Pro Plan' if plan == 'pro' else '🆓 Free Plan'}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ─── Metrics ────────────────────────────────────────────
    applications = []
    if user_id:
        try:
            applications = db.get_applications(user_id) or []
        except Exception:
            applications = []

    total_apps = len(applications)
    interview_count = sum(1 for a in applications if a.get("status") == "interview")
    offer_count = sum(1 for a in applications if a.get("status") == "offer")
    this_week = sum(
        1 for a in applications
        if a.get("applied_at", "") >= (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Applied", str(total_apps), icon="📨")
    with c2:
        metric_card("Interviews", str(interview_count), icon="🎯")
    with c3:
        metric_card("Offers", str(offer_count), icon="🏆")
    with c4:
        metric_card("This Week", str(this_week), icon="📅")

    divider()

    # ─── Quick Actions ───────────────────────────────────────
    section_header("Quick Actions", "Jump right into your job search")
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("🔍 Discover Jobs", use_container_width=True, type="primary"):
            st.switch_page("pages/job_discovery.py")

    with c2:
        if st.button("📄 Optimize Resume", use_container_width=True):
            st.switch_page("pages/resume_optimizer.py")

    with c3:
        if st.button("🤖 Ask AI Coach", use_container_width=True):
            st.switch_page("pages/coach.py")

    divider()

    # ─── Recent Applications ─────────────────────────────────
    section_header("Recent Applications", "Your latest job applications")

    if not applications:
        st.markdown(
            """
            <div style="text-align:center;padding:40px;background:#1F2937;
                        border-radius:12px;color:#6B7280;">
                <div style="font-size:40px;margin-bottom:12px;">📭</div>
                <p>No applications yet. Start by discovering jobs!</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🔍 Find Jobs Now", type="primary"):
            st.switch_page("pages/job_discovery.py")
    else:
        status_colors = {
            "applied":   "#3B82F6",
            "interview": "#10B981",
            "offer":     "#F59E0B",
            "rejected":  "#EF4444",
        }
        for app in applications[:10]:
            status = app.get("status", "applied")
            color = status_colors.get(status, "#6B7280")
            st.markdown(
                f"""
                <div style="background:#1F2937;border-left:3px solid {color};
                            border-radius:8px;padding:12px 16px;margin-bottom:8px;
                            display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:600;color:#F9FAFB;">
                            {app.get('job_title','—')}
                        </span>
                        <span style="color:#9CA3AF;"> · {app.get('company','—')}</span>
                    </div>
                    <div>
                        <span style="background:{color}22;color:{color};
                                     padding:2px 10px;border-radius:10px;font-size:12px;">
                            {status.title()}
                        </span>
                        <span style="color:#6B7280;font-size:12px;margin-left:12px;">
                            {app.get('applied_at','')[:10]}
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ─── Daily Checklist ────────────────────────────────────
    divider()
    section_header("Daily Checklist", "Suggested actions for today")
    tasks = [
        ("Apply to 3 new jobs", False),
        ("Optimize your resume", False),
        ("Follow up on pending applications", False),
        ("Send 3 cold emails to target companies", False),
    ]
    for label, done in tasks:
        st.checkbox(label, value=done, disabled=False)

    # ─── Upgrade nudge for free users ───────────────────────
    if plan != "pro":
        divider()
        st.info(
            "💡 **Track more applications for deeper insights.** "
            "The AI Career Coach becomes significantly more accurate once you've "
            "logged at least 10 applications."
        )


try:
    render()
except Exception as _e:
    st.error("⚠️ Something went wrong. Please refresh.")
    with st.expander("Details"):
        st.exception(_e)
