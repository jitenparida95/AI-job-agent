"""components/auth.py – Login and signup UI."""
import streamlit as st
import utils.session as session
import database as db
from components.ui import error, success


def render_auth_page() -> None:
    st.markdown(
        """
        <div style="text-align:center;padding:40px 0 20px;">
            <div style="font-size:40px;">🚀</div>
            <h1 style="font-size:32px;font-weight:800;margin:8px 0;">CareerOS</h1>
            <p style="color:#9CA3AF;">AI Career Operating System</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

    with tab_login:
        _login_form()

    with tab_signup:
        _signup_form()


def _login_form() -> None:
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

    if submitted:
        if not email or not password:
            error("Please fill in all fields.")
            return
        user = db.authenticate_user(email.strip(), password)
        if user:
            session.login_user(user)
            st.rerun()
        else:
            error("Invalid email or password.")


def _signup_form() -> None:
    with st.form("signup_form", clear_on_submit=False):
        name = st.text_input("Full Name", placeholder="Priya Sharma")
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password",
                                  placeholder="Min 6 characters")
        confirm = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button(
            "Create Free Account", type="primary", use_container_width=True
        )

    if submitted:
        if not all([name, email, password, confirm]):
            error("Please fill in all fields.")
            return
        if len(password) < 6:
            error("Password must be at least 6 characters.")
            return
        if password != confirm:
            error("Passwords do not match.")
            return

        user = db.create_user(email.strip(), password, name.strip())
        if user:
            session.login_user(user)
            success("Account created! Welcome to CareerOS 🎉")
            st.rerun()
        else:
            error("An account with this email already exists.")

    st.markdown(
        "<p style='text-align:center;color:#6B7280;font-size:12px;margin-top:12px;'>"
        "Free trial includes 7 days of Pro features.</p>",
        unsafe_allow_html=True,
    )
