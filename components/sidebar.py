"""components/sidebar.py – Sidebar navigation."""
import streamlit as st
import utils.session as session
from components.ui import plan_badge


NAV_ITEMS = [
    ("🏠", "Dashboard",          "pages/dashboard.py"),
    ("🧠", "Career Intelligence", "pages/career_intelligence.py"),
    ("📄", "Resume Optimizer",   "pages/resume_optimizer.py"),
    ("✨", "Resume Rewriter",    "pages/resume_rewriter.py"),
    ("🔍", "Job Discovery",      "pages/job_discovery.py"),
    ("🎯", "AI Job Matching",    "pages/matching.py"),
    ("⚙️",  "Application Engine", "pages/application_engine.py"),
    ("🚀", "Auto Apply",         "pages/auto_apply.py"),
    ("📊", "Tracker & Analytics","pages/tracker.py"),
    ("🤖", "AI Career Coach",    "pages/coach.py"),
    ("⚙️",  "Settings",           "pages/settings.py"),
]


def render_sidebar() -> None:
    with st.sidebar:
        # Logo
        st.markdown(
            """
            <div style="padding:16px 0 8px;">
                <span style="font-size:22px;font-weight:800;">🚀 CareerOS</span>
                <div style="font-size:10px;color:#6B7280;letter-spacing:2px;margin-top:2px;">
                    AI CAREER OPERATING SYSTEM
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # User info
        name = session.get_first_name()
        email = session.get("user_email", "")
        st.markdown(
            f"""
            <div style="padding:8px 0 12px;">
                <div style="font-size:13px;font-weight:600;color:#F9FAFB;">{name}</div>
                <div style="font-size:11px;color:#6B7280;">{email}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        plan_badge()
        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

        # Navigation
        for icon, label, page in NAV_ITEMS:
            st.page_link(page, label=f"{icon}  {label}")

        st.divider()

        # Upgrade CTA for free users
        if not session.is_pro():
            st.markdown(
                """
                <div style="background:#1E1B4B;border:1px solid #4C1D95;border-radius:10px;
                            padding:12px;margin-bottom:12px;">
                    <div style="font-size:13px;font-weight:700;color:#A78BFA;">⭐ Upgrade to Pro</div>
                    <div style="font-size:11px;color:#7C3AED;margin-top:4px;">
                        Unlimited AI features<br>₹499/month
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("⚡ Upgrade Now", use_container_width=True, type="primary"):
                st.switch_page("pages/settings.py")

        if st.button("🚪 Sign Out", use_container_width=True):
            session.logout_user()
            st.rerun()
