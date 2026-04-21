import streamlit as st
from core.store import get_applied, get_settings, save_settings


def render():
    applied = get_applied()
    settings = get_settings()

    st.markdown("""<div style='padding: 8px 0 24px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 11px; color: #3d5a80; letter-spacing: 0.1em;'>TRACKER</div>
        <h1 style='font-size: 28px; margin: 4px 0 0; color: #e8eaf0;'>Applications Log</h1>
        <p style='color: #5a7090; font-size: 14px; margin: 4px 0 0;'>Full history of every application the agent has submitted.</p>
    </div>""", unsafe_allow_html=True)

    if not applied:
        st.markdown("""<div style='text-align:center; padding:64px; color:#3d5a80;'>
            <div style='font-size:40px;'>📭</div>
            <div style='font-family: JetBrains Mono, monospace; font-size:13px; margin-top:12px;'>No applications yet</div>
        </div>""", unsafe_allow_html=True)
        return

    success = [a for a in applied if a.get("result") == "applied"]
    failed  = [a for a in applied if "failed" in str(a.get("result",""))]
    by_portal = {}
    for a in applied:
        p = a.get("portal","unknown")
        by_portal[p] = by_portal.get(p, 0) + 1

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-value">{len(applied)}</div><div class="metric-label">Total sent</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-value">{len(success)}</div><div class="metric-label">Successful</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-value">{len(failed)}</div><div class="metric-label">Failed</div></div>', unsafe_allow_html=True)
    rate = f"{int(len(success)/len(applied)*100)}%" if applied else "—"
    c4.markdown(f'<div class="metric-card"><div class="metric-value">{rate}</div><div class="metric-label">Success rate</div></div>', unsafe_allow_html=True)

    # Portal breakdown
    if by_portal:
        portal_str = " · ".join(f"{p.upper()}: {n}" for p, n in sorted(by_portal.items(), key=lambda x: -x[1]))
        st.markdown(f'<div style="font-family: JetBrains Mono, monospace; font-size:12px; color:#5a7090; margin: 0 0 16px;">{portal_str}</div>', unsafe_allow_html=True)

    # Filter
    filter_opt = st.radio("Filter", ["All", "Successful", "Failed"], horizontal=True, label_visibility="collapsed")
    if filter_opt == "Successful":
        display = success
    elif filter_opt == "Failed":
        display = failed
    else:
        display = applied

    st.markdown(f'<div class="section-header">{len(display)} APPLICATIONS</div>', unsafe_allow_html=True)

    for app in reversed(display):
        score = app.get("match_score", 0) or 0
        score_cls = "score-high" if score >= 70 else ("score-mid" if score >= 50 else "score-low")
        ok = app.get("result") == "applied"
        badge_cls = "badge-applied" if ok else "badge-error"
        badge_txt = "APPLIED" if ok else "FAILED"
        applied_at = app.get("applied_at", "")[:16].replace("T", " ")

        with st.expander(f"{app.get('title','')} @ {app.get('company','')} · {applied_at}"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"""
**Portal:** {app.get('portal','').upper()}  
**Applied:** {applied_at}  
**Result:** <span class="status-badge {badge_cls}">{badge_txt}</span>  
**URL:** [{app.get('url','')}]({app.get('url','')})
""", unsafe_allow_html=True)
                if app.get("cover_letter"):
                    st.text_area("Cover letter sent", value=app["cover_letter"][:800], height=180, disabled=True, label_visibility="visible")
            with c2:
                st.markdown(f'<div style="text-align:center; padding:16px;"><div class="match-score {score_cls}" style="font-size:36px;">{score}%</div><div style="color:#5a7090; font-size:11px; margin-top:4px;">MATCH SCORE</div></div>', unsafe_allow_html=True)
