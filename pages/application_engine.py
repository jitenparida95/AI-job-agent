"""pages/application_engine.py – Application Engine page (standalone Streamlit page)."""
import streamlit as st

st.set_page_config(
    page_title="Application Engine – CareerOS",
    page_icon="⚙️",
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
    section_header("⚙️ Application Engine",
                   "Generate a complete application package for any job")

    resume_text = session.get("resume_text", "")
    if not resume_text.strip():
        st.warning("⚠️ Paste your resume in **Resume Optimizer** first for best results.")

    job_description = st.text_area(
        "Paste Job Description",
        height=120,
        placeholder="Paste the full job description here...",
    )
    company = st.text_input("Company Name", placeholder="e.g. Infosys")
    job_title = st.text_input("Job Title", placeholder="e.g. Business Analyst")

    if st.button("🚀 Generate Complete Application Package (All 4 formats)",
                 type="primary", use_container_width=True):
        if not job_description.strip() and not resume_text.strip():
            error("Please add your resume and/or job description first.")
            return

        results: dict = {}
        any_mock = False

        with st.spinner("Generating cover letter..."):
            try:
                text, is_real = generate_cover_letter(resume_text, job_description, company)
                results["cover_letter"] = text
                if not is_real:
                    any_mock = True
            except Exception:
                results["cover_letter"] = "⚠️ Could not generate. Try again."

        with st.spinner("Generating cold email..."):
            try:
                text, is_real = generate_cold_email(resume_text, job_description, company)
                results["cold_email"] = text
            except Exception:
                results["cold_email"] = "⚠️ Could not generate. Try again."

        with st.spinner("Generating referral message..."):
            try:
                text, is_real = generate_referral_message(resume_text, job_description)
                results["referral"] = text
            except Exception:
                results["referral"] = "⚠️ Could not generate. Try again."

        results["linkedin_dm"] = (
            f"Hi [Name], I noticed {company or 'your company'} is hiring for "
            f"{job_title or 'this role'} and think my background would be a great fit. "
            "Would love to connect and learn more about the team. Thanks!"
        )

        session.set_val("generated_content", results)

        if any_mock:
            api_warning()
        else:
            success("Application package generated!")

        # Log application
        user_id = session.get("user_id")
        if user_id and job_title and company:
            try:
                db.log_application(user_id, job_title, company)
            except Exception:
                pass

    # ─── Results ────────────────────────────────────────────
    content = session.get("generated_content", {})
    if content:
        st.divider()
        tabs = st.tabs(["📝 Cover Letter", "📧 Cold Email",
                         "🤝 Referral", "💼 LinkedIn DM"])
        keys = ["cover_letter", "cold_email", "referral", "linkedin_dm"]
        labels = ["cover_letter", "cold_email", "referral_message", "linkedin_dm"]
        for tab, key, lbl in zip(tabs, keys, labels):
            with tab:
                text = content.get(key, "")
                st.text_area("", value=text, height=200, key=f"ae_{key}")
                st.download_button(
                    f"⬇️ Download",
                    data=text,
                    file_name=f"{lbl}.txt",
                    mime="text/plain",
                    key=f"ae_dl_{key}",
                )


# ── Run ──────────────────────────────────────────────────────
try:
    render()
except Exception as _page_err:
    st.error("⚠️ Something went wrong. Please refresh the page.")
    with st.expander("Technical details"):
        st.exception(_page_err)
