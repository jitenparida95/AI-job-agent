import streamlit as st
from core.store import get_jobs, get_applied, get_prefs, get_settings, get_tracker
from datetime import datetime


def render():
    prefs = get_prefs()
    jobs = get_jobs()
    applied = get_applied()
    tracker = get_tracker()
    settings = get_settings()
    all_tracked = applied + tracker
    _name_parts = prefs.get("name", "").strip().split()
    name = _name_parts[0] if _name_parts else "there"

    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")

    st.markdown(f"""
    <div style='padding: 8px 0 28px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 10px; color: #2d4060; letter-spacing: 0.2em; margin-bottom: 4px;'>COMMAND CENTER · {datetime.now().strftime("%d %b %Y  %H:%M")}</div>
        <h1 style='font-size: 30px; font-weight: 800; margin: 0 0 6px; color: #e2e8f0;'>{greeting}, {name} 🚀</h1>
        <p style='color: #4a6080; font-size: 14px; margin: 0;'>Your AI Career Operating System is active. {len(jobs)} jobs in pipeline · {len(all_tracked)} applications tracked.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Setup progress ──────────────────────────────────────
    setup_score = _setup_score(prefs, settings)
    if setup_score < 100:
        done = int(setup_score / 100 * 5)
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #0f1629, #111827); border: 1px solid #1a2540; border-left: 3px solid #6366f1; border-radius: 12px; padding: 18px 22px; margin-bottom: 20px;'>
            <div style='font-size: 12px; color: #6366f1; font-family: JetBrains Mono, monospace; font-weight: 600; margin-bottom: 8px;'>SETUP PROGRESS — {setup_score}% COMPLETE</div>
            <div style='font-size: 14px; color: #e2e8f0; font-weight: 500; margin-bottom: 12px;'>Complete your profile to unlock full CareerOS intelligence</div>
            <div style='background: #1a2540; border-radius: 6px; height: 8px; overflow: hidden;'>
                <div style='width: {setup_score}%; height: 100%; border-radius: 6px; background: linear-gradient(90deg, #6366f1, #22d3a5);'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Core metrics ─────────────────────────────────────────
    scored = [j for j in jobs if j.get("match_score") is not None]
    high_match = [j for j in scored if j.get("match_score", 0) >= settings.get("min_match_score", 70)]
    interviews = len([t for t in all_tracked if t.get("status") in ["Interview", "Interview Scheduled", "Technical Round"]])
    offers = len([t for t in all_tracked if t.get("status") in ["Offer", "Offer Received"]])
    response_rate = f"{int(interviews/max(len(all_tracked),1)*100)}%" if all_tracked else "—"

    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        (c1, len(jobs), "Jobs in Pipeline", None),
        (c2, len(high_match), "High-Match Roles", None),
        (c3, len(all_tracked), "Applications Tracked", None),
        (c4, interviews, "Interviews", "🎯"),
        (c5, response_rate, "Response Rate", None),
    ]
    for col, val, label, icon in metrics:
        prefix = icon + " " if icon else ""
        with col:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{prefix}{val}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    # ── System readiness ──────────────────────────────────────
    st.markdown('<div class="section-header">SYSTEM READINESS</div>', unsafe_allow_html=True)
    checks = {
        "Resume Uploaded": bool(prefs.get("resume_text") or prefs.get("resume_path")),
        "Profile Complete": bool(prefs.get("name") and prefs.get("target_roles")),
        "AI Engine (Groq)": bool(settings.get("groq_api_key")),
        "Job Pipeline": len(jobs) > 0,
        "Applications Active": len(all_tracked) > 0,
    }
    cols = st.columns(5)
    for col, (label, ok) in zip(cols, checks.items()):
        icon = "✓" if ok else "○"
        color = "#22d3a5" if ok else "#2d4060"
        bg = "#052e16" if ok else "#0c1020"
        border = "#166534" if ok else "#1a2540"
        col.markdown(f"""<div style='text-align:center; padding: 14px 8px; background: {bg}; border: 1px solid {border}; border-radius: 10px;'>
            <div style='font-size: 18px; color: {color}; font-family: JetBrains Mono, monospace;'>{icon}</div>
            <div style='font-size: 10px; color: {"#22d3a5" if ok else "#4a6080"}; margin-top: 6px; font-weight: 500;'>{label}</div>
        </div>""", unsafe_allow_html=True)

    # ── Quick actions ─────────────────────────────────────────
    st.markdown('<div class="section-header">YOUR NEXT MOVE</div>', unsafe_allow_html=True)

    if not prefs.get("resume_text"):
        st.markdown("""<div class="insight-card warning">
            <div style='font-size: 13px; font-weight: 600; color: #fbbf24; margin-bottom: 4px;'>⚡ Start here: Upload your resume</div>
            <div style='font-size: 13px; color: #7a8faa;'>CareerOS needs your resume to generate career paths, ATS scores, and personalized job matches.</div>
        </div>""", unsafe_allow_html=True)
    elif not settings.get("groq_api_key"):
        st.markdown("""<div class="insight-card info">
            <div style='font-size: 13px; font-weight: 600; color: #a5b4fc; margin-bottom: 4px;'>🧠 Add your Groq API key to unlock AI intelligence</div>
            <div style='font-size: 13px; color: #7a8faa;'>Free at console.groq.com — enables Career Intelligence, Resume Optimization, and Application generation.</div>
        </div>""", unsafe_allow_html=True)
    elif len(jobs) == 0:
        st.markdown("""<div class="insight-card info">
            <div style='font-size: 13px; font-weight: 600; color: #a5b4fc; margin-bottom: 4px;'>🔍 Discover your first jobs</div>
            <div style='font-size: 13px; color: #7a8faa;'>Run Job Discovery to populate your pipeline with matching roles.</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="insight-card success">
            <div style='font-size: 13px; font-weight: 600; color: #22d3a5; margin-bottom: 4px;'>✓ System ready — execute today's job search</div>
            <div style='font-size: 13px; color: #7a8faa;'>Score your job matches, generate applications, and track your pipeline.</div>
        </div>""", unsafe_allow_html=True)

    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("🧠 Career Intelligence", use_container_width=True):
            st.info("→ Navigate to Career Intelligence")
    with q2:
        if st.button("📊 Resume Optimizer", use_container_width=True):
            st.info("→ Navigate to Resume Optimizer")
    with q3:
        if st.button("🔍 Discover Jobs", use_container_width=True):
            st.info("→ Navigate to Job Discovery")
    with q4:
        if st.button("📋 View Tracker", use_container_width=True):
            st.info("→ Navigate to Tracker & Analytics")

    # ── Recent pipeline ───────────────────────────────────────
    if all_tracked:
        st.markdown('<div class="section-header">RECENT APPLICATIONS</div>', unsafe_allow_html=True)
        for app in reversed(all_tracked[-5:]):
            score = app.get("match_score", 0) or 0
            score_cls = "score-high" if score >= 70 else ("score-mid" if score >= 50 else "score-low")
            status = app.get("status", app.get("result", "Applied"))
            status_map = {
                "Applied": "badge-applied", "Interview": "badge-interview",
                "Interview Scheduled": "badge-interview", "Technical Round": "badge-interview",
                "Offer": "badge-offer", "Offer Received": "badge-offer",
                "Rejected": "badge-rejected", "applied": "badge-applied",
            }
            badge_cls = status_map.get(status, "badge-pending")
            date_str = (app.get("applied_at") or app.get("created_at", ""))[:10]
            st.markdown(f"""<div class="job-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div class="job-title">{app.get('title', 'Unknown Role')}</div>
                        <div class="job-company">{app.get('company', '')} · {app.get('portal', 'Manual').upper()}</div>
                        <div class="job-meta">{date_str}</div>
                    </div>
                    <div style="text-align:right;">
                        {f'<div class="match-score {score_cls}">{score}%</div>' if score else ''}
                        <span class="status-badge {badge_cls}">{status.upper()}</span>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style='text-align:center; padding: 48px; color: #2d4060; background: #0c1020; border: 1px solid #1a2540; border-radius: 12px; margin-top: 20px;'>
            <div style='font-size: 28px; margin-bottom: 12px;'>🚀</div>
            <div style='font-family: JetBrains Mono, monospace; font-size: 12px;'>No applications yet.</div>
            <div style='font-size: 13px; margin-top: 6px; color: #4a6080;'>Discover jobs and start tracking your pipeline.</div>
        </div>""", unsafe_allow_html=True)


def _setup_score(prefs, settings):
    checks = [
        bool(prefs.get("name")),
        bool(prefs.get("resume_text") or prefs.get("resume_path")),
        bool(prefs.get("target_roles")),
        bool(settings.get("groq_api_key")),
        bool(prefs.get("min_salary_lpa")),
    ]
    return int(sum(checks) / len(checks) * 100)
