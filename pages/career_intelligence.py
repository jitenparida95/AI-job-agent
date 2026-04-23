"""pages/career_intelligence.py – Career Intelligence page (standalone Streamlit page)."""
import streamlit as st

st.set_page_config(
    page_title="Career Intelligence – CareerOS",
    page_icon="🧠",
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
    section_header("🧠 Career Intelligence",
                   "Market insights and personalised career strategy")

    resume_text = session.get("resume_text", "")
    if not resume_text.strip():
        st.info("ℹ️ Add your resume in **Resume Optimizer** for personalised insights.")

    role = st.text_input("Target Role", placeholder="e.g. Senior Business Analyst")
    industry = st.text_input("Industry", placeholder="e.g. Fintech, E-commerce")

    if st.button("🧠 Generate Career Intelligence Report", type="primary",
                 use_container_width=True):
        if not role:
            st.warning("Please enter a target role.")
            return

        with st.spinner("Analysing market and generating insights..."):
            system = (
                "You are a career intelligence expert focused on the Indian job market. "
                "Provide concise, actionable intelligence. Structure your response with "
                "clear sections: Market Demand, Required Skills, Salary Range, "
                "Top Companies Hiring, and Quick Action Plan."
            )
            user = (
                f"Target Role: {role}\n"
                f"Industry: {industry or 'General'}\n"
                f"My Background: {resume_text[:600] or 'Not provided'}"
            )
            fallback = (
                f"## Career Intelligence: {role}\n\n"
                "**Market Demand:** High demand in Bangalore, Mumbai, Hyderabad. "
                "Remote roles increasing.\n\n"
                "**Required Skills:** Analytical thinking, Excel/SQL, stakeholder management, "
                "communication, data visualization (Power BI/Tableau).\n\n"
                "**Salary Range (India):** ₹8–25 LPA depending on experience level.\n\n"
                "**Top Companies Hiring:** Deloitte, EY, KPMG, Razorpay, Flipkart, "
                "Amazon, Goldman Sachs.\n\n"
                "**Quick Action Plan:**\n"
                "1. Update resume with quantified achievements\n"
                "2. Apply to 10–15 roles/week\n"
                "3. Network on LinkedIn actively\n"
                "4. Prepare 3 STAR-format stories\n\n"
                "_Add an API key in Settings for AI-personalized intelligence._"
            )

            try:
                result, is_real = call_ai(system, user, max_tokens=800, fallback=fallback)
                st.markdown(result)
                if not is_real:
                    api_warning()
            except Exception:
                st.markdown(fallback)


# ── Run ──────────────────────────────────────────────────────
try:
    render()
except Exception as _page_err:
    st.error("⚠️ Something went wrong. Please refresh the page.")
    with st.expander("Technical details"):
        st.exception(_page_err)
