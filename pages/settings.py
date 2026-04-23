"""pages/settings.py – Settings page (standalone Streamlit page)."""
import streamlit as st

st.set_page_config(
    page_title="Settings – CareerOS",
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
    section_header("⚙️ Settings", "Configure your API keys and account")

    tab_api, tab_portals, tab_plan, tab_account = st.tabs(
        ["🔑 API Keys", "🌐 Job Portals", "💳 Plan", "👤 Account"]
    )

    # ─── API Keys ────────────────────────────────────────────
    with tab_api:
        st.markdown("Add your AI API keys to enable real AI generation.")
        st.info(
            "Keys are stored in your `.env` file locally and never sent to any third party. "
            "The app works in demo mode without keys."
        )

        with st.form("api_key_form"):
            openai_key = st.text_input(
                "OpenAI API Key",
                value="*" * 10 if config.OPENAI_API_KEY else "",
                type="password",
                placeholder="sk-...",
                help="Get at platform.openai.com",
            )
            groq_key = st.text_input(
                "Groq API Key (free, fast)",
                value="*" * 10 if config.GROQ_API_KEY else "",
                type="password",
                placeholder="gsk_...",
                help="Free at console.groq.com",
            )
            submitted = st.form_submit_button("Save Keys", type="primary")

        if submitted:
            # Write to .env file
            try:
                env_path = __import__("pathlib").Path(__file__).parent.parent / ".env"
                lines = []
                if env_path.exists():
                    with open(env_path) as f:
                        lines = f.readlines()

                def _set_env(lines, key, value):
                    if not value or value.startswith("*"):
                        return lines
                    new_line = f"{key}={value}\n"
                    for i, line in enumerate(lines):
                        if line.startswith(f"{key}="):
                            lines[i] = new_line
                            return lines
                    lines.append(new_line)
                    return lines

                if openai_key and not openai_key.startswith("*"):
                    lines = _set_env(lines, "OPENAI_API_KEY", openai_key)
                if groq_key and not groq_key.startswith("*"):
                    lines = _set_env(lines, "GROQ_API_KEY", groq_key)

                with open(env_path, "w") as f:
                    f.writelines(lines)
                success("Keys saved! Restart the app to apply changes.")
            except Exception as e:
                error(f"Could not save keys: {e}. Set them manually in .env file.")

        # Status
        st.markdown("**Current Status:**")
        provider = config.get_active_ai_provider()
        if provider != "mock":
            st.success(f"✅ AI enabled via **{provider.title()}**")
        else:
            st.warning("⚠️ Running in demo mode (no API key). Template responses only.")

    # ─── Job Portals ─────────────────────────────────────────
    with tab_portals:
        st.markdown("Configure which portals to search by default.")
        prefs = session.get("prefs", {})
        current_portals = prefs.get("portals", config.DEFAULT_PORTALS)

        new_portals = st.multiselect(
            "Default Portals",
            options=config.SUPPORTED_PORTALS,
            default=current_portals,
        )
        if st.button("Save Portal Settings", type="primary"):
            prefs["portals"] = new_portals
            session.set_val("prefs", prefs)
            user_id = session.get("user_id")
            if user_id:
                try:
                    db.save_user_prefs(user_id, prefs)
                except Exception:
                    pass
            success("Portal settings saved!")

    # ─── Plan ────────────────────────────────────────────────
    with tab_plan:
        plan = session.get("user_plan", "free")

        if plan == "pro":
            st.success("⭐ You're on **CareerOS Pro**. Enjoy unlimited access!")
        else:
            st.markdown("### Upgrade to CareerOS Pro")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(
                    """
                    **Free Plan**
                    - ✅ Job Discovery
                    - ✅ 5 Auto-applies/day
                    - ✅ Template content
                    - ❌ AI Content Generation
                    - ❌ Career Intelligence
                    - ❌ AI Coach Chat
                    """
                )
            with c2:
                st.markdown(
                    f"""
                    **Pro Plan – ₹{config.PRO_PRICE_INR}/month**
                    - ✅ Everything in Free
                    - ✅ 50 Auto-applies/day
                    - ✅ Real AI generation
                    - ✅ Career Intelligence
                    - ✅ Unlimited AI Coach
                    - ✅ Priority support
                    """
                )

            st.divider()

            if is_demo_mode():
                st.info(
                    "💳 **Demo Mode:** Payment gateway not configured. "
                    "Click below to simulate a Pro upgrade (for testing)."
                )
                if st.button("🚀 Simulate Pro Upgrade (Demo)", type="primary",
                             use_container_width=True):
                    _process_upgrade()
            else:
                st.markdown(
                    f"[💳 Upgrade to Pro – ₹{config.PRO_PRICE_INR}/month]"
                    f"(https://razorpay.com/payment-link/careeros)",
                    unsafe_allow_html=False,
                )

                # Manual verification for Razorpay
                with st.expander("Already paid? Verify payment"):
                    payment_id = st.text_input("Payment ID", placeholder="pay_...")
                    if st.button("Verify & Unlock Pro", type="primary"):
                        if payment_id.startswith("pay_"):
                            _process_upgrade()
                        else:
                            error("Invalid payment ID. Contact support.")

    # ─── Account ─────────────────────────────────────────────
    with tab_account:
        name = session.get("user_name", "")
        email = session.get("user_email", "")
        user_id = session.get("user_id")

        with st.form("account_form"):
            new_name = st.text_input("Full Name", value=name)
            st.text_input("Email", value=email, disabled=True,
                           help="Email cannot be changed.")
            titles = st.text_input(
                "Target Job Titles",
                value=", ".join(session.get("prefs", {}).get("job_titles", [])),
                placeholder="Financial Analyst, Business Analyst",
            )
            locations = st.text_input(
                "Preferred Locations",
                value=", ".join(session.get("prefs", {}).get("locations", [])),
                placeholder="Bangalore, Mumbai, Remote",
            )
            submitted = st.form_submit_button("Save Profile", type="primary")

        if submitted:
            try:
                if user_id:
                    db.update_user(user_id, name=new_name)
                session.set_val("user_name", new_name)
                prefs = session.get("prefs", {})
                prefs["job_titles"] = [t.strip() for t in titles.split(",") if t.strip()]
                prefs["locations"] = [loc.strip() for loc in locations.split(",") if loc.strip()]
                session.set_val("prefs", prefs)
                if user_id:
                    db.save_user_prefs(user_id, prefs)
                success("Profile saved!")
            except Exception:
                error("Could not save profile. Please try again.")


def _process_upgrade() -> None:
    user_id = session.get("user_id")
    if user_id:
        try:
            db.upgrade_user_to_pro(user_id)
        except Exception:
            pass
    session.upgrade_to_pro()
    success("🎉 You're now on CareerOS Pro! Enjoy unlimited access.")
    st.balloons()
    st.rerun()


# ── Run ──────────────────────────────────────────────────────
try:
    render()
except Exception as _page_err:
    st.error("⚠️ Something went wrong. Please refresh the page.")
    with st.expander("Technical details"):
        st.exception(_page_err)
