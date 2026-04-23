"""pages/tracker.py – Tracker & Analytics page (standalone Streamlit page)."""
import streamlit as st

st.set_page_config(
    page_title="Tracker & Analytics – CareerOS",
    page_icon="📊",
    layout="wide",
)

# ── Global styles ────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #111827; color: #F9FAFB; }
section[data-testid="stSidebar"] { background-color: #0F172A; }
#MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
.stButton > button { border-radius: 8px; font-weight: 600; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background-color: #1F2937; color: #F9FAFB; border-color: #374151; border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

import utils.session as session
session.init_session()

if not session.get("authenticated"):
    st.warning("Please sign in to continue.")
    st.stop()

from components.sidebar import render_sidebar
render_sidebar()

# ── Page content ─────────────────────────────────────────────
def render() -> None:
    session.init_session()
    section_header("📊 Tracker & Analytics", "Monitor your job search progress")

    user_id = session.get("user_id")
    if not user_id:
        st.warning("Please sign in to view your applications.")
        return

    try:
        applications = db.get_applications(user_id) or []
    except Exception:
        applications = []
        error("Could not load applications.")

    # ─── Metrics ────────────────────────────────────────────
    total = len(applications)
    by_status = {}
    for app in applications:
        s = app.get("status", "applied")
        by_status[s] = by_status.get(s, 0) + 1

    c1, c2, c3, c4, c5 = st.columns(5)
    cols = [c1, c2, c3, c4, c5]
    statuses = ["applied", "interview", "offer", "rejected"]
    icons = ["📨", "🎯", "🏆", "❌"]
    cols[0].markdown("")
    metric_card("Total Applied", str(total), icon="📋")
    for col, st_key, icon in zip(cols[1:], statuses, icons):
        with col:
            metric_card(st_key.title(), str(by_status.get(st_key, 0)), icon=icon)

    st.divider()

    # ─── Add manual application ──────────────────────────────
    with st.expander("➕ Log a New Application"):
        with st.form("add_app_form"):
            c1, c2 = st.columns(2)
            with c1:
                jt = st.text_input("Job Title", placeholder="Business Analyst")
            with c2:
                co = st.text_input("Company", placeholder="Razorpay")
            c3, c4 = st.columns(2)
            with c3:
                portal = st.selectbox("Portal", ["linkedin", "naukri", "foundit",
                                                  "instahyre", "other"])
            with c4:
                status = st.selectbox("Status", STATUS_OPTIONS)
            notes = st.text_input("Notes (optional)")
            submitted = st.form_submit_button("Log Application", type="primary")

        if submitted:
            if jt and co:
                try:
                    db.log_application(user_id, jt, co, portal, status, notes)
                    success("Application logged!")
                    st.rerun()
                except Exception:
                    error("Could not save. Please try again.")
            else:
                error("Job title and company are required.")

    # ─── Application list ────────────────────────────────────
    if not applications:
        st.info("No applications tracked yet. Log your first one above or use Auto Apply.")
        return

    # Filter
    filter_status = st.selectbox("Filter by status", ["All"] + STATUS_OPTIONS)
    filtered = applications if filter_status == "All" else [
        a for a in applications if a.get("status") == filter_status
    ]

    st.markdown(f"**Showing {len(filtered)} applications**")

    for app in filtered:
        color = STATUS_COLORS.get(app.get("status", "applied"), "#6B7280")
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(
                f"""
                <div style="background:#1F2937;border-left:3px solid {color};
                            border-radius:8px;padding:10px 14px;margin-bottom:6px;">
                    <strong style="color:#F9FAFB;">{app.get('job_title','—')}</strong>
                    <span style="color:#9CA3AF;"> · {app.get('company','—')}</span>
                    <span style="color:#6B7280;font-size:12px;margin-left:8px;">
                        {app.get('portal','')} · {app.get('applied_at','')[:10]}
                    </span>
                    <br>
                    <span style="background:{color}22;color:{color};
                                 padding:1px 8px;border-radius:8px;font-size:12px;">
                        {app.get('status','').title()}
                    </span>
                    {"<span style='color:#9CA3AF;font-size:12px;margin-left:8px;'>" + app.get('notes','') + "</span>" if app.get('notes') else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            new_status = st.selectbox(
                "Update",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(app.get("status", "applied")),
                key=f"update_{app['id']}",
                label_visibility="collapsed",
            )
            if new_status != app.get("status"):
                try:
                    db.update_application_status(app["id"], user_id, new_status)
                    st.rerun()
                except Exception:
                    error("Could not update status.")


# ── Run ──────────────────────────────────────────────────────
try:
    render()
except Exception as _page_err:
    st.error("⚠️ Something went wrong. Please refresh the page.")
    with st.expander("Technical details"):
        st.exception(_page_err)
