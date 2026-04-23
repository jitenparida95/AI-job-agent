"""pages/auto_apply.py – Auto Apply page (standalone Streamlit page)."""
import streamlit as st

st.set_page_config(
    page_title="Auto Apply – CareerOS",
    page_icon="🚀",
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
    section_header("🚀 Auto Apply",
                   "Automatically apply to your highest-scoring jobs")

    user_id = session.get("user_id")
    plan = session.get("user_plan", "free")
    daily_limit = config.DAILY_PRO_APPLY_LIMIT if plan == "pro" else config.DAILY_FREE_APPLY_LIMIT

    # Metrics
    jobs_matched = session.get("jobs_matched", [])
    ready = [j for j in jobs_matched if (j.get("match_score") or 0) >= 70]

    used_today = 0
    if user_id:
        try:
            used_today = db.get_daily_usage(user_id, "apply")
        except Exception:
            used_today = 0

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Ready to Apply", str(len(ready)), icon="📋")
    with c2:
        metric_card("Match Threshold", "70%", icon="🎯")
    with c3:
        metric_card("Daily Limit", str(daily_limit), icon="📅")

    st.divider()

    if not ready:
        st.warning(
            "🔍 No jobs ready to apply. Run **Job Discovery** and **AI Matching** first "
            "to build your apply queue."
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 Job Discovery", use_container_width=True):
                st.switch_page("pages/job_discovery.py")
        with c2:
            if st.button("🎯 AI Matching", use_container_width=True):
                st.switch_page("pages/matching.py")
        return

    # ─── Settings ──────────────────────────────────────────
    threshold = st.slider("Min match score to auto-apply", 60, 95, 70)
    target_jobs = [j for j in jobs_matched if (j.get("match_score") or 0) >= threshold]

    remaining = max(0, daily_limit - used_today)
    st.info(
        f"You have **{remaining}** auto-applies remaining today. "
        f"({used_today}/{daily_limit} used)"
    )

    if plan != "pro":
        st.warning(
            f"⭐ Free plan: {config.DAILY_FREE_APPLY_LIMIT} applications/day. "
            "Upgrade to Pro for 50/day."
        )

    if st.button(f"🚀 Auto Apply to {min(len(target_jobs), remaining)} Jobs",
                 type="primary", use_container_width=True,
                 disabled=(remaining == 0)):
        if remaining == 0:
            error(f"Daily limit of {daily_limit} applications reached. Check back tomorrow.")
            return

        to_apply = target_jobs[:remaining]
        progress = st.progress(0)
        results = []

        for i, job in enumerate(to_apply):
            progress.progress((i + 1) / len(to_apply))
            if user_id:
                try:
                    db.log_application(
                        user_id,
                        job.get("title", "Unknown Role"),
                        job.get("company", "Unknown Company"),
                        portal=job.get("portal", ""),
                        status="applied",
                    )
                    results.append(f"✅ Applied: {job.get('title')} @ {job.get('company')}")
                except Exception:
                    results.append(f"⚠️ Failed: {job.get('title')} @ {job.get('company')}")

        progress.empty()
        success(f"Applied to {len(results)} jobs!")
        for r in results:
            st.markdown(r)


# ── Run ──────────────────────────────────────────────────────
try:
    render()
except Exception as _page_err:
    st.error("⚠️ Something went wrong. Please refresh the page.")
    with st.expander("Technical details"):
        st.exception(_page_err)
