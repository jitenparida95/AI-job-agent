import streamlit as st
from core.store import get_jobs, get_applied, get_prefs, get_settings
from datetime import datetime, timedelta


def render():
    prefs = get_prefs()
    jobs = get_jobs()
    applied = get_applied()
    settings = get_settings()

    st.markdown(f"""
    <div style='padding: 8px 0 24px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 11px; color: #3d5a80; letter-spacing: 0.1em;'>OVERVIEW · {datetime.now().strftime("%d %b %Y  %H:%M")}</div>
        <h1 style='font-size: 28px; margin: 4px 0 0; color: #e8eaf0;'>Good day, {prefs.get('name','').split()[0]} ⚡</h1>
        <p style='color: #5a7090; font-size: 14px; margin: 4px 0 0;'>Your AI job agent is ready. {len(jobs)} jobs in queue · {len(applied)} applied this session.</p>
    </div>
    """, unsafe_allow_html=True)

    # Metrics row
    matched = [j for j in jobs if j.get("match_score") and j["match_score"] >= settings.get("min_match_score", 70)]
    success = [a for a in applied if a.get("result") == "applied"]
    pending = [j for j in jobs if j.get("status") == "new"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{len(jobs)}</div>
            <div class="metric-label">Jobs discovered</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{len(matched)}</div>
            <div class="metric-label">High matches (≥{settings.get('min_match_score',70)}%)</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{len(applied)}</div>
            <div class="metric-label">Applications sent</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        rate = f"{int(len(success)/len(applied)*100)}%" if applied else "—"
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{rate}</div>
            <div class="metric-label">Success rate</div>
        </div>""", unsafe_allow_html=True)

    # Status check
    st.markdown('<div class="section-header">SYSTEM STATUS</div>', unsafe_allow_html=True)
    s = get_settings()
    checks = {
        "Resume uploaded": bool(prefs.get("resume_text") or prefs.get("resume_path")),
        "AI API key (Groq)": bool(s.get("groq_api_key")),
        "Naukri credentials": bool(s.get("naukri_email") and s.get("naukri_password")),
        "LinkedIn credentials": bool(s.get("linkedin_email") and s.get("linkedin_password")),
        "Auto-apply enabled": bool(s.get("auto_apply_enabled")),
    }
    cols = st.columns(5)
    for col, (label, ok) in zip(cols, checks.items()):
        icon = "✓" if ok else "✗"
        color = "#22d3a5" if ok else "#f87171"
        col.markdown(f"""<div style='text-align:center; padding: 12px 8px; background: #111827; border: 1px solid #1e2d4a; border-radius: 8px;'>
            <div style='font-size: 20px; color: {color}; font-family: JetBrains Mono, monospace;'>{icon}</div>
            <div style='font-size: 11px; color: #5a7090; margin-top: 6px;'>{label}</div>
        </div>""", unsafe_allow_html=True)

    # Quick actions
    st.markdown('<div class="section-header">QUICK ACTIONS</div>', unsafe_allow_html=True)
    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("🔍  Discover Jobs Now"):
            st.switch_page("pages/discovery.py") if hasattr(st, 'switch_page') else st.info("Go to Job Discovery →")
    with q2:
        if st.button("🤖  Run AI Matching"):
            st.switch_page("pages/matching.py") if hasattr(st, 'switch_page') else st.info("Go to AI Matching →")
    with q3:
        if st.button("🚀  Start Auto Apply"):
            st.switch_page("pages/apply.py") if hasattr(st, 'switch_page') else st.info("Go to Auto Apply →")

    # Recent applications
    if applied:
        st.markdown('<div class="section-header">RECENT APPLICATIONS</div>', unsafe_allow_html=True)
        for app in reversed(applied[-5:]):
            score = app.get("match_score", 0) or 0
            score_cls = "score-high" if score >= 70 else ("score-mid" if score >= 50 else "score-low")
            badge_cls = "badge-applied" if app.get("result") == "applied" else "badge-error"
            badge_txt = app.get("result", "unknown").upper()
            applied_at = app.get("applied_at", "")[:10]
            st.markdown(f"""<div class="job-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div class="job-title">{app.get('title','')} <span style='color:#5a7090; font-size:13px;'>@ {app.get('company','')}</span></div>
                        <div class="job-meta">{app.get('portal','').upper()} · {applied_at}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="match-score {score_cls}">{score}%</div>
                        <span class="status-badge {badge_cls}">{badge_txt}</span>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style='text-align:center; padding: 48px; color: #3d5a80;'>
            <div style='font-size: 32px;'>⚡</div>
            <div style='font-family: JetBrains Mono, monospace; font-size: 13px; margin-top: 8px;'>No applications yet. Start by discovering jobs.</div>
        </div>""", unsafe_allow_html=True)
