"""pages/matching.py – AI Job Matching page (standalone Streamlit page)."""
import streamlit as st

st.set_page_config(
    page_title="AI Job Matching – CareerOS",
    page_icon="🎯",
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
    section_header("🎯 AI Job Matching", "See how well you match each job")

    jobs = session.get("jobs_discovered", [])
    if not jobs:
        st.info("No jobs to match yet. Run **Job Discovery** first.")
        if st.button("🔍 Go to Job Discovery", type="primary"):
            st.switch_page("pages/job_discovery.py")
        return

    resume_text = session.get("resume_text", "")
    if not resume_text.strip():
        st.warning(
            "⚠️ Add your resume first for accurate matching. "
            "Go to **Resume Optimizer** to paste it."
        )

    if st.button("⚡ Score All Jobs", type="primary", use_container_width=True):
        any_mock_ai = False
        progress = st.progress(0)
        status = st.empty()

        for i, job in enumerate(jobs):
            try:
                status.text(f"Scoring: {job.get('title','')} @ {job.get('company','')}...")
                jd = job.get("description", "")
                if resume_text.strip() and jd:
                    score, reason, is_real = score_job_match(resume_text, jd)
                    if not is_real:
                        any_mock_ai = True
                    job["match_score"] = score
                    job["match_reason"] = reason
                else:
                    import random
                    job["match_score"] = random.randint(55, 92)
                    any_mock_ai = True
            except Exception:
                job["match_score"] = 70
            progress.progress((i + 1) / len(jobs))

        session.set_val("jobs_matched", sorted(jobs, key=lambda j: j.get("match_score", 0), reverse=True))
        progress.empty()
        status.empty()
        if any_mock_ai:
            api_warning()

    # ─── Matched results ────────────────────────────────────
    jobs_matched = session.get("jobs_matched", jobs)
    threshold = st.slider("Min match score", 0, 100, 60)
    filtered = [j for j in jobs_matched if (j.get("match_score") or 0) >= threshold]

    st.markdown(f"**{len(filtered)} jobs above {threshold}% match**")
    for i, job in enumerate(filtered):
        job_card(job, show_apply=True, key_prefix=f"match_{i}_")


# ── Run ──────────────────────────────────────────────────────
try:
    render()
except Exception as _page_err:
    st.error("⚠️ Something went wrong. Please refresh the page.")
    with st.expander("Technical details"):
        st.exception(_page_err)
