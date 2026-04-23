"""components/ui.py – Reusable UI components and helpers."""
import streamlit as st
from typing import Optional
import utils.session as session


# ─── ALERTS ─────────────────────────────────────────────────

def error(msg: str) -> None:
    st.error(f"⚠️ {msg}")


def success(msg: str) -> None:
    st.success(f"✅ {msg}")


def info(msg: str) -> None:
    st.info(f"ℹ️ {msg}")


def warning(msg: str) -> None:
    st.warning(f"🔔 {msg}")


def api_warning() -> None:
    st.warning(
        "🔑 **No AI key configured.** Results below are template examples. "
        "Go to **Settings → API Keys** to enable real AI generation.",
        icon="🔑"
    )


def pro_gate(feature_name: str = "this feature") -> bool:
    """Show upgrade prompt and return False if user is not Pro."""
    if session.is_pro():
        return True
    st.warning(
        f"🚀 **{feature_name}** is available on CareerOS Pro. "
        f"Upgrade for ₹{499}/month to unlock unlimited AI features.",
        icon="⭐"
    )
    if st.button("⚡ Upgrade to Pro", type="primary", key=f"gate_{feature_name}"):
        st.switch_page("pages/settings.py")
    return False


def plan_badge() -> None:
    plan = session.get("user_plan", "free")
    if plan == "pro":
        st.markdown(
            '<span style="background:#7C3AED;color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:12px;font-weight:700;">⭐ PRO</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span style="background:#374151;color:#9CA3AF;padding:3px 10px;'
            'border-radius:12px;font-size:12px;">FREE</span>',
            unsafe_allow_html=True,
        )


def metric_card(label: str, value: str, delta: Optional[str] = None,
                icon: str = "") -> None:
    delta_html = (
        f'<div style="color:#10B981;font-size:12px;margin-top:2px;">{delta}</div>'
        if delta else ""
    )
    st.markdown(
        f"""
        <div style="background:#1F2937;border:1px solid #374151;border-radius:12px;
                    padding:20px;text-align:center;">
            <div style="font-size:28px;margin-bottom:4px;">{icon}</div>
            <div style="font-size:28px;font-weight:700;color:#F9FAFB;">{value}</div>
            <div style="font-size:13px;color:#9CA3AF;margin-top:4px;">{label}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"<p style='color:#9CA3AF;margin-top:-10px;'>{subtitle}</p>",
                    unsafe_allow_html=True)


def divider() -> None:
    st.markdown("<hr style='border:1px solid #374151;margin:24px 0;'>",
                unsafe_allow_html=True)


def job_card(job: dict, show_apply: bool = True, key_prefix: str = "") -> bool:
    """Render a job card. Returns True if Apply button clicked."""
    score = job.get("match_score")
    score_color = "#10B981" if (score or 0) >= 75 else "#F59E0B" if (score or 0) >= 50 else "#6B7280"
    score_html = (
        f'<span style="background:{score_color};color:#fff;padding:2px 8px;'
        f'border-radius:8px;font-size:12px;font-weight:700;">{score}% match</span>'
        if score is not None else ""
    )
    mock_badge = (
        '<span style="background:#374151;color:#9CA3AF;padding:2px 8px;'
        'border-radius:8px;font-size:11px;">Demo</span>'
        if job.get("is_mock") else ""
    )

    st.markdown(
        f"""
        <div style="background:#1F2937;border:1px solid #374151;border-radius:12px;
                    padding:16px 20px;margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <div style="font-size:16px;font-weight:700;color:#F9FAFB;">
                        {job.get('title','—')}
                    </div>
                    <div style="color:#9CA3AF;font-size:13px;margin-top:4px;">
                        {job.get('company','—')} • {job.get('location','—')} •
                        {job.get('portal','').upper()}
                    </div>
                    <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;">
                        {score_html} {mock_badge}
                        {"<span style='background:#1E3A5F;color:#60A5FA;padding:2px 8px;border-radius:8px;font-size:12px;'>" + job.get('experience','') + "</span>" if job.get('experience') else ""}
                        {"<span style='background:#1E3A5F;color:#34D399;padding:2px 8px;border-radius:8px;font-size:12px;'>" + job.get('salary','') + "</span>" if job.get('salary') else ""}
                    </div>
                </div>
                <div style="color:#6B7280;font-size:12px;">{job.get('posted','')}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    clicked = False
    if show_apply:
        c1, c2 = st.columns([1, 4])
        with c1:
            clicked = st.button("Apply →", key=f"{key_prefix}apply_{job.get('id','')}")
        with c2:
            if job.get("url"):
                st.markdown(
                    f"[🔗 View Job]({job['url']})",
                    unsafe_allow_html=True,
                )
    return clicked
