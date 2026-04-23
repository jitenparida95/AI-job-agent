"""pages/resume_rewriter.py – Resume Rewriter page (standalone Streamlit page)."""
import streamlit as st

st.set_page_config(
    page_title="Resume Rewriter – CareerOS",
    page_icon="✨",
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
    section_header("✨ Application Content Generator",
                   "Cover letters, cold emails, referral messages & more")

    # ─── Inputs ─────────────────────────────────────────────
    resume_text = st.text_area(
        "Your Resume / Background",
        value=session.get("resume_text", ""),
        height=160,
        placeholder="Paste your resume or a brief summary of your background...",
    )

    job_description = st.text_area(
        "Job Description (optional)",
        height=100,
        placeholder="Paste the job description for better personalization...",
    )
    company = st.text_input("Company Name (optional)", placeholder="e.g. Razorpay")

    # ─── Content type selector ──────────────────────────────
    st.markdown("**Select content to generate:**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        do_cover = st.button("📝 Cover Letter", use_container_width=True)
    with c2:
        do_email = st.button("📧 Cold Email", use_container_width=True)
    with c3:
        do_referral = st.button("🤝 Referral Message", use_container_width=True)
    with c4:
        do_all = st.button("🚀 Generate All", use_container_width=True, type="primary")

    if not resume_text.strip():
        st.info("ℹ️ Paste your resume above to generate personalized content.")
        return

    session.set_val("resume_text", resume_text)

    # ─── Generate ───────────────────────────────────────────
    def _show_result(label: str, text: str, is_real: bool, key: str) -> None:
        if not is_real:
            api_warning()
        st.markdown(f"**{label}**")
        st.text_area("", value=text, height=220, key=key)
        st.download_button(
            f"⬇️ Download {label}",
            data=text,
            file_name=f"{label.lower().replace(' ', '_')}.txt",
            mime="text/plain",
            key=f"dl_{key}",
        )
        divider()

    if do_cover or do_all:
        with st.spinner("Writing your cover letter..."):
            try:
                text, is_real = generate_cover_letter(resume_text, job_description, company)
                _show_result("Cover Letter", text, is_real, "cover_letter_out")
            except Exception:
                error("Could not generate cover letter. Please try again.")

    if do_email or do_all:
        with st.spinner("Writing cold email..."):
            try:
                text, is_real = generate_cold_email(resume_text, job_description, company)
                _show_result("Cold Email", text, is_real, "cold_email_out")
            except Exception:
                error("Could not generate cold email. Please try again.")

    if do_referral or do_all:
        with st.spinner("Writing referral message..."):
            try:
                text, is_real = generate_referral_message(resume_text, job_description)
                _show_result("Referral Message", text, is_real, "referral_out")
            except Exception:
                error("Could not generate referral message. Please try again.")


# ── Run ──────────────────────────────────────────────────────
try:
    render()
except Exception as _page_err:
    st.error("⚠️ Something went wrong. Please refresh the page.")
    with st.expander("Technical details"):
        st.exception(_page_err)
