"""pages/job_discovery.py – Job Discovery page (standalone Streamlit page)."""
import streamlit as st

st.set_page_config(
    page_title="Job Discovery – CareerOS",
    page_icon="🔍",
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
    section_header("🔍 Job Discovery", "Find your next opportunity across top portals")

    # ─── Search Parameters ───────────────────────────────────
    st.markdown("**Search Parameters**")

    job_titles_raw = st.text_input(
        "Job titles to search",
        value=", ".join(session.get("prefs", {}).get("job_titles", [])) or
              "Financial Analyst, Business Analyst",
        placeholder="e.g. Software Engineer, Product Manager",
    )

    locations_raw = st.text_input(
        "Locations",
        value=", ".join(session.get("prefs", {}).get("locations", [])) or
              "Bangalore, Remote, India",
        placeholder="e.g. Mumbai, Bangalore, Remote",
    )

    portals = st.multiselect(
        "Portals to search",
        options=config.SUPPORTED_PORTALS,
        default=config.DEFAULT_PORTALS,
    )

    c1, c2 = st.columns([1, 2])
    with c1:
        max_results = st.slider("Max results per portal", 5, 50, 25)
    with c2:
        experience_filter = st.text_input(
            "Experience filter (optional)", placeholder="e.g. 3-6 years"
        )

    if st.button("🔍 Discover Jobs Now", type="primary", use_container_width=True):
        titles = [t.strip() for t in job_titles_raw.split(",") if t.strip()]
        locations = [loc.strip() for loc in locations_raw.split(",") if loc.strip()]

        if not titles:
            st.warning("Please enter at least one job title.")
            return
        if not portals:
            st.warning("Please select at least one portal.")
            return

        # Live log container
        log_placeholder = st.empty()
        logs: list[str] = []

        def update_log(msg: str) -> None:
            logs.append(msg)
            log_placeholder.markdown(
                "\n".join(f"`{line}`" for line in logs[-8:])
            )

        update_log("[INIT] Starting discovery...")

        with st.spinner("Searching across portals..."):
            try:
                jobs, log_text = discover_jobs(
                    titles, locations, portals, max_results, experience_filter
                )
                for line in log_text.split("\n"):
                    if line.strip():
                        update_log(line)
            except Exception as e:
                update_log(f"[ERROR] {e} – using fallback data")
                from services.job_scraper import _generate_mock_jobs
                jobs = _generate_mock_jobs(titles, locations, portals, 15)

        session.set_val("jobs_discovered", jobs)
        update_log(f"[DONE] {len(jobs)} total jobs found ✓")

    # ─── Results ────────────────────────────────────────────
    jobs = session.get("jobs_discovered", [])
    if jobs:
        st.divider()
        st.markdown(f"**{len(jobs)} jobs found**")
        mock_count = sum(1 for j in jobs if j.get("is_mock"))
        if mock_count:
            info(
                f"{mock_count} jobs are demo entries (API/scraping unavailable). "
                "Real results will appear when portals are accessible."
            )

        for i, job in enumerate(jobs):
            job_card(job, show_apply=True, key_prefix=f"disc_{i}_")


# ── Run ──────────────────────────────────────────────────────
try:
    render()
except Exception as _page_err:
    st.error("⚠️ Something went wrong. Please refresh the page.")
    with st.expander("Technical details"):
        st.exception(_page_err)
