import streamlit as st
from core.store import get_applied, save_applied

def render():
    applied = get_applied()

    st.markdown("""<div style='padding: 8px 0 28px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 10px; color: #2d4060; letter-spacing: 0.2em;'>LOG</div>
        <h1 style='font-size: 30px; font-weight: 800; margin: 4px 0 6px; color: #e2e8f0;'>Auto-Apply Log</h1>
        <p style='color: #4a6080; font-size: 14px; margin: 0;'>Record of all automated application submissions.</p>
    </div>""", unsafe_allow_html=True)

    if not applied:
        st.markdown("""<div style='text-align:center; padding: 60px; background: #0c1020; border: 1px dashed #1a2540; border-radius: 12px;'>
            <div style='font-size: 28px; margin-bottom: 12px;'>📋</div>
            <div style='font-size: 13px; color: #4a6080;'>No auto-apply submissions yet. Use Auto Apply to submit applications.</div>
        </div>""", unsafe_allow_html=True)
        return

    success = [a for a in applied if a.get("result") == "applied"]
    errors = [a for a in applied if a.get("result") != "applied"]
    rate = f"{int(len(success)/len(applied)*100)}%" if applied else "—"

    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in [(c1, len(applied), "Total Submitted"), (c2, len(success), "Successful"),
                             (c3, len(errors), "Errors"), (c4, rate, "Success Rate")]:
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">SUBMISSION LOG</div>', unsafe_allow_html=True)
    for app in reversed(applied[-50:]):
        score = app.get("match_score", 0) or 0
        score_cls = "score-high" if score >= 70 else ("score-mid" if score >= 50 else "score-low")
        result = app.get("result", "unknown")
        badge_cls = "badge-applied" if result == "applied" else "badge-rejected"
        date_str = app.get("applied_at", "")[:10]
        st.markdown(f"""<div class="job-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div class="job-title">{app.get('title','')} <span class="job-company">@ {app.get('company','')}</span></div>
                    <div class="job-meta">{app.get('portal','').upper()} · {date_str}</div>
                </div>
                <div style="text-align:right;">
                    {f'<div class="match-score {score_cls}">{score}%</div>' if score else ''}
                    <span class="status-badge {badge_cls}">{result.upper()}</span>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
