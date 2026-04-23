"""utils/session.py – Safe session state helpers. Prevents IndexError / KeyError crashes."""
import streamlit as st
from typing import Any, Optional


# ─── DEFAULTS ───────────────────────────────────────────────
_DEFAULTS: dict = {
    "authenticated": False,
    "user": None,          # Full user dict from DB
    "user_id": None,
    "user_email": "",
    "user_name": "",
    "user_plan": "free",
    "prefs": {},
    "resume_text": "",
    "resume_optimized": "",
    "jobs_discovered": [],
    "jobs_matched": [],
    "applications": [],
    "generated_content": {},
    "page": "dashboard",
    "error": None,
    "success": None,
    "loading": False,
}


def init_session() -> None:
    """Ensure all required keys exist with safe defaults."""
    for key, default in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def get(key: str, fallback: Any = None) -> Any:
    """Safely get a session value."""
    init_session()
    return st.session_state.get(key, fallback)


def set_val(key: str, value: Any) -> None:
    """Set a session value."""
    st.session_state[key] = value


def login_user(user: dict) -> None:
    """Populate session after successful login/signup."""
    st.session_state["authenticated"] = True
    st.session_state["user"] = user
    st.session_state["user_id"] = user.get("id")
    st.session_state["user_email"] = user.get("email", "")
    st.session_state["user_name"] = user.get("name", "")
    st.session_state["user_plan"] = user.get("plan", "free")
    st.session_state["prefs"] = {}
    try:
        import json
        prefs = json.loads(user.get("prefs") or "{}")
        st.session_state["prefs"] = prefs
    except Exception:
        pass


def logout_user() -> None:
    """Clear all session state."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session()


def is_pro() -> bool:
    return get("user_plan") == "pro"


def get_first_name() -> str:
    """Return first name safely – never raises IndexError."""
    name = get("user_name", "").strip()
    if not name:
        return "there"
    parts = name.split()
    return parts[0] if parts else "there"


def upgrade_to_pro() -> None:
    st.session_state["user_plan"] = "pro"
    if st.session_state.get("user"):
        st.session_state["user"]["plan"] = "pro"
