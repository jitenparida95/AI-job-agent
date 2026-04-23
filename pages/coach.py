"""pages/coach.py – AI Career Coach page (standalone Streamlit page)."""
import streamlit as st

st.set_page_config(
    page_title="AI Career Coach – CareerOS",
    page_icon="🤖",
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
    section_header("🤖 AI Career Coach", "Get personalised career guidance")

    # Init chat history in session
    if "coach_history" not in st.session_state:
        st.session_state["coach_history"] = []

    # ─── Chat History ────────────────────────────────────────
    for msg in st.session_state["coach_history"]:
        role = msg["role"]
        with st.chat_message(role):
            st.markdown(msg["content"])

    # ─── Input ───────────────────────────────────────────────
    prompt = st.chat_input("Ask your career coach anything...")

    if prompt:
        # Show user message
        st.session_state["coach_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Build context from session
        context_parts = []
        name = session.get_first_name()
        plan = session.get("user_plan", "free")
        resume = session.get("resume_text", "")
        apps = st.session_state.get("coach_history", [])
        if name != "there":
            context_parts.append(f"User's name: {name}")
        if plan:
            context_parts.append(f"Plan: {plan}")
        if resume:
            context_parts.append(f"Resume snippet: {resume[:400]}")
        context = "\n".join(context_parts)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response, is_real = ask_career_coach(prompt, context)
                    st.markdown(response)
                    if not is_real:
                        api_warning()
                    st.session_state["coach_history"].append(
                        {"role": "assistant", "content": response}
                    )
                except Exception:
                    err = "Something went wrong. Please try again."
                    st.error(err)
                    st.session_state["coach_history"].append(
                        {"role": "assistant", "content": err}
                    )

    # ─── Clear chat ──────────────────────────────────────────
    if st.session_state["coach_history"]:
        if st.button("🗑️ Clear Chat"):
            st.session_state["coach_history"] = []
            st.rerun()

    # ─── Suggested questions ─────────────────────────────────
    if not st.session_state["coach_history"]:
        st.markdown("**Suggested questions:**")
        suggestions = [
            "How do I get more interview callbacks?",
            "What skills should I learn for my next role?",
            "How should I negotiate my salary?",
            "How do I explain a gap in employment?",
        ]
        cols = st.columns(2)
        for i, q in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(q, key=f"sug_{i}", use_container_width=True):
                    st.session_state["coach_history"].append({"role": "user", "content": q})
                    st.rerun()


# ── Run ──────────────────────────────────────────────────────
try:
    render()
except Exception as _page_err:
    st.error("⚠️ Something went wrong. Please refresh the page.")
    with st.expander("Technical details"):
        st.exception(_page_err)
