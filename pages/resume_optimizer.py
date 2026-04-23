"""pages/resume_optimizer.py – Resume Optimizer page (standalone Streamlit page)."""
import streamlit as st

st.set_page_config(
    page_title="Resume Optimizer – CareerOS",
    page_icon="📄",
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
    section_header("📄 Resume Optimizer", "ATS-optimized resume in seconds")

    # ─── Input ──────────────────────────────────────────────
    resume_text = st.text_area(
        "Paste your current resume",
        value=session.get("resume_text", ""),
        height=280,
        placeholder="Paste your resume text here...",
    )

    job_description = st.text_area(
        "Target Job Description (optional)",
        height=120,
        placeholder="Paste the job description to tailor the optimization...",
    )

    mode = st.radio(
        "Rewrite Mode",
        ["Full Rewrite", "Targeted (Summary & Skills only)"],
        horizontal=True,
    )
    mode_key = "full" if "Full" in mode else "targeted"

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    if st.button("✨ Optimize My Resume", type="primary", use_container_width=True,
                 disabled=not resume_text.strip()):
        if not resume_text.strip():
            error("Please paste your resume first.")
            return

        session.set_val("resume_text", resume_text)

        with st.spinner("Analyzing and optimizing your resume..."):
            try:
                result, is_real = optimize_resume(resume_text, job_description, mode_key)
                session.set_val("resume_optimized", result)

                user_id = session.get("user_id")
                if user_id:
                    try:
                        db.save_resume(user_id, resume_text, result)
                    except Exception:
                        pass  # Non-critical

                if not is_real:
                    api_warning()

                success("Resume optimized successfully!")

            except Exception:
                error("Something went wrong. Please try again.")
                return

    # ─── Output ─────────────────────────────────────────────
    optimized = session.get("resume_optimized", "")
    if optimized:
        st.divider()
        section_header("✅ Optimized Resume", "Ready to use")

        st.text_area("Optimized Resume", value=optimized, height=400)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "⬇️ Download as TXT",
                data=optimized,
                file_name="optimized_resume.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with c2:
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.write("📋 Use Ctrl+A, Ctrl+C in the text area above.")


# ── Run ──────────────────────────────────────────────────────
try:
    render()
except Exception as _page_err:
    st.error("⚠️ Something went wrong. Please refresh the page.")
    with st.expander("Technical details"):
        st.exception(_page_err)
