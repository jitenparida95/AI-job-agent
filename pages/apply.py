import streamlit as st
from core.store import get_jobs, get_prefs, get_settings, save_settings, log_application
from core.ai_engine import generate_cover_letter
import time


def render():
    prefs = get_prefs()
    settings = get_settings()
    jobs = get_jobs()

    st.markdown("""<div style='padding: 8px 0 24px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 11px; color: #3d5a80; letter-spacing: 0.1em;'>AUTOMATION ENGINE</div>
        <h1 style='font-size: 28px; margin: 4px 0 0; color: #e8eaf0;'>Auto Apply</h1>
        <p style='color: #5a7090; font-size: 14px; margin: 4px 0 0;'>Let the agent apply to all matched jobs automatically.</p>
    </div>""", unsafe_allow_html=True)

    min_score = settings.get("min_match_score", 70)
    apply_candidates = [j for j in jobs if (j.get("match_score") or 0) >= min_score and j.get("status") != "applied"]

    # Requirements check
    st.markdown('<div class="section-header">PRE-FLIGHT CHECK</div>', unsafe_allow_html=True)
    checks = [
        ("Resume loaded", bool(prefs.get("resume_text") or prefs.get("resume_path"))),
        ("Jobs scored", len(apply_candidates) > 0),
        ("Naukri login", bool(settings.get("naukri_email") and settings.get("naukri_password"))),
        ("LinkedIn login", bool(settings.get("linkedin_email") and settings.get("linkedin_password"))),
        ("Browser (Selenium)", _check_selenium()),
        ("Groq AI key", bool(settings.get("groq_api_key"))),
    ]
    cols = st.columns(6)
    all_ok = all(ok for _, ok in checks)
    for col, (label, ok) in zip(cols, checks):
        icon = "✓" if ok else "✗"
        color = "#22d3a5" if ok else "#f87171"
        col.markdown(f"""<div style='text-align:center; padding:12px 6px; background:#111827; border:1px solid #1e2d4a; border-radius:8px;'>
            <div style='font-size:18px; color:{color}; font-family: JetBrains Mono, monospace;'>{icon}</div>
            <div style='font-size:10px; color:#5a7090; margin-top:4px;'>{label}</div>
        </div>""", unsafe_allow_html=True)

    # Stats
    st.markdown('<div class="section-header">APPLY QUEUE</div>', unsafe_allow_html=True)
    portal_counts = {}
    for j in apply_candidates:
        portal_counts[j.get("portal","")] = portal_counts.get(j.get("portal",""), 0) + 1

    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="metric-value">{len(apply_candidates)}</div><div class="metric-label">Ready to apply</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-value">{settings.get("daily_apply_limit", 30)}</div><div class="metric-label">Daily limit</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-value">{len(portal_counts)}</div><div class="metric-label">Portals</div></div>', unsafe_allow_html=True)

    # Portal breakdown
    if portal_counts:
        pc_str = " · ".join(f"{p.upper()}: {n}" for p, n in portal_counts.items())
        st.markdown(f'<div style="font-family: JetBrains Mono, monospace; font-size:12px; color:#5a7090; margin-bottom:16px;">{pc_str}</div>', unsafe_allow_html=True)

    # Preview jobs to apply
    st.markdown('<div class="section-header">JOBS IN THIS RUN</div>', unsafe_allow_html=True)
    selected = []
    for job in apply_candidates[:settings.get("daily_apply_limit", 30)]:
        score = job.get("match_score", 0)
        score_cls = "score-high" if score >= 70 else "score-mid"
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"""<div class="job-card" style="margin-bottom:6px;">
                <div class="job-title">{job.get('title','')} <span style='color:#5a7090; font-weight:400;'>@ {job.get('company','')}</span></div>
                <div class="job-meta">{job.get('portal','').upper()} · {job.get('location','')}</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div style="text-align:right; padding:8px 0;"><span class="match-score {score_cls}">{score}%</span></div>', unsafe_allow_html=True)
        selected.append(job)

    # Warning for full auto
    st.markdown("""<div style='background:#1a0f00; border:1px solid #f59e0b; border-radius:8px; padding:14px 16px; margin:16px 0;'>
        <div style='color:#f59e0b; font-family: JetBrains Mono, monospace; font-size:12px; font-weight:500;'>⚠ FULLY AUTOMATED MODE</div>
        <div style='color:#8a6a30; font-size:13px; margin-top:6px;'>The bot will log in to your accounts and submit applications automatically. 
        Make sure your resume is updated and credentials are correct in Settings. 
        Naukri/LinkedIn may show CAPTCHA on first run — run once with headless=OFF to solve it.</div>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        go = st.button(
            f"🚀  Apply to {min(len(selected), settings.get('daily_apply_limit',30))} Jobs Now",
            disabled=(len(selected) == 0)
        )
    with col2:
        preview_cl = st.button("👁  Preview Cover Letter")

    if preview_cl and selected:
        job = selected[0]
        cl = generate_cover_letter(job, prefs, prefs.get("cover_letter_template",""),
                                   settings.get("groq_api_key",""))
        with st.expander(f"Cover letter preview: {job.get('title')} @ {job.get('company')}", expanded=True):
            st.text_area("", value=cl, height=300, label_visibility="collapsed")

    if go:
        if not _check_selenium():
            st.error("Selenium not installed. Run: pip install selenium")
            st.code("pip install selenium\n# Also install ChromeDriver matching your Chrome version")
            return

        log_area = st.empty()
        bar = st.progress(0)
        log_lines = ["[INIT] Starting bulk apply engine..."]

        results = {"success": 0, "failed": 0, "skipped": 0}

        for i, job in enumerate(selected):
            log_lines.append(f"[{i+1}/{len(selected)}] Applying → {job.get('title','')} @ {job.get('company','')}")
            log_area.markdown(f'<div class="terminal-log">{"<br>".join(log_lines[-12:])}</div>', unsafe_allow_html=True)
            bar.progress(int((i + 1) / len(selected) * 100))

            # Generate cover letter
            cl = generate_cover_letter(job, prefs, prefs.get("cover_letter_template",""),
                                       settings.get("groq_api_key",""))

            # Apply via bot
            try:
                from core.apply_bot import auto_apply_job
                result = auto_apply_job(job, prefs, settings, cl)
                if result.get("success"):
                    results["success"] += 1
                    job["status"] = "applied"
                    log_application(job, cl, "applied")
                    log_lines.append(f"    ✓ SUCCESS: {result.get('reason','')}")
                else:
                    results["failed"] += 1
                    log_lines.append(f"    ✗ FAILED: {result.get('reason','')}")
                    log_application(job, cl, f"failed: {result.get('reason','')}")
            except Exception as e:
                results["failed"] += 1
                log_lines.append(f"    ✗ ERROR: {str(e)[:60]}")

            time.sleep(1.5)

        log_lines.append(f"[DONE] ✓ {results['success']} applied · ✗ {results['failed']} failed")
        log_area.markdown(f'<div class="terminal-log">{"<br>".join(log_lines)}</div>', unsafe_allow_html=True)
        bar.progress(100)
        st.success(f"Run complete — {results['success']} applications submitted successfully!")


def _check_selenium() -> bool:
    try:
        import selenium
        return True
    except ImportError:
        return False
