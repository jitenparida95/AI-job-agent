import streamlit as st
from core.store import get_prefs, get_settings, get_jobs, add_jobs, save_jobs
from core.scrapers import scrape_all
import time


def render():
    prefs = get_prefs()
    settings = get_settings()
    existing = get_jobs()

    st.markdown("""<div style='padding: 8px 0 24px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 11px; color: #3d5a80; letter-spacing: 0.1em;'>SCRAPING ENGINE</div>
        <h1 style='font-size: 28px; margin: 4px 0 0; color: #e8eaf0;'>Job Discovery</h1>
        <p style='color: #5a7090; font-size: 14px; margin: 4px 0 0;'>Scan all portals for matching roles and pull them into your queue.</p>
    </div>""", unsafe_allow_html=True)

    # Portal selector
    st.markdown('<div class="section-header">SELECT PORTALS</div>', unsafe_allow_html=True)
    portal_info = {
        "naukri": ("Naukri.com", "India's largest · API-based · fast"),
        "linkedin": ("LinkedIn", "Easy Apply only · requires login"),
        "instahyre": ("Instahyre", "Mid-senior roles · good for GCCs"),
        "foundit": ("Foundit (Monster)", "Large volume · India focus"),
        "wellfound": ("Wellfound", "Startups · remote-friendly"),
        "remotive": ("Remotive", "100% remote roles · global"),
    }
    selected_portals = []
    cols = st.columns(3)
    for i, (pid, (name, desc)) in enumerate(portal_info.items()):
        default = pid in settings.get("portals", [])
        with cols[i % 3]:
            checked = st.checkbox(f"**{name}**\n\n{desc}", value=default, key=f"portal_{pid}")
            if checked:
                selected_portals.append(pid)

    # Search config
    st.markdown('<div class="section-header">SEARCH PARAMETERS</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        kw_str = st.text_area("Search keywords",
            value="\n".join(prefs.get("target_roles", []) + prefs.get("keywords", [])[:3]),
            height=100)
        keywords = [k.strip() for k in kw_str.splitlines() if k.strip()]
    with c2:
        loc_str = st.text_area("Locations",
            value="\n".join(prefs.get("locations", [])), height=100)
        locations = [l.strip() for l in loc_str.splitlines() if l.strip()]

    st.markdown(f"""<div style='background:#111827; border:1px solid #1e2d4a; border-radius:8px; padding:12px 16px; margin-bottom:16px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size:12px; color:#5a7090;'>
            Currently <span style='color:#22d3a5;'>{len(existing)}</span> jobs in queue ·
            Scanning <span style='color:#22d3a5;'>{len(selected_portals)}</span> portals ·
            Limit: <span style='color:#22d3a5;'>{settings.get("daily_apply_limit",30)}</span> applications/day
        </div>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        start = st.button("🔍  Start Discovery Scan", disabled=not selected_portals)
    with col2:
        if st.button("🗑️  Clear Job Queue"):
            save_jobs([])
            st.success("Queue cleared")
            st.rerun()

    if start:
        log_container = st.empty()
        progress_bar = st.progress(0)
        status = st.empty()

        log_lines = ["[INIT] Starting discovery scan..."]

        def update_log(portal, step, total):
            log_lines.append(f"[SCAN] Scraping {portal.upper()}...")
            log_container.markdown(
                f'<div class="terminal-log">{"<br>".join(log_lines[-12:])}</div>',
                unsafe_allow_html=True
            )
            progress_bar.progress(int((step + 1) / max(total, 1) * 80))

        # Run scrapers
        tmp_prefs = prefs.copy()
        tmp_prefs["keywords"] = keywords
        tmp_prefs["locations"] = locations
        tmp_settings = settings.copy()
        tmp_settings["portals"] = selected_portals

        with st.spinner(""):
            jobs = scrape_all(tmp_prefs, tmp_settings, selected_portals, progress_callback=update_log)

        progress_bar.progress(90)
        added = add_jobs(jobs)
        progress_bar.progress(100)

        log_lines.append(f"[DONE] Found {len(jobs)} jobs · Added {added} new to queue")
        log_container.markdown(
            f'<div class="terminal-log">{"<br>".join(log_lines)}</div>',
            unsafe_allow_html=True
        )
        status.success(f"✓ Discovery complete — {added} new jobs added. Go to AI Matching to score them.")
        time.sleep(1)

    # Preview current queue
    jobs = get_jobs()
    if jobs:
        st.markdown(f'<div class="section-header">JOB QUEUE ({len(jobs)} jobs)</div>', unsafe_allow_html=True)
        for job in jobs[:15]:
            score = job.get("match_score")
            score_str = f"{score}%" if score is not None else "Not scored"
            score_cls = "score-high" if (score or 0) >= 70 else ("score-mid" if (score or 0) >= 50 else "score-low")
            portal = job.get("portal", "").upper()
            st.markdown(f"""<div class="job-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="flex:1;">
                        <div class="job-title">{job.get('title','')}
                            <span style='color:#5a7090; font-weight:400;'> @ {job.get('company','')}</span>
                        </div>
                        <div class="job-meta">
                            {portal} · {job.get('location','')} · {job.get('salary','Salary not listed')}
                        </div>
                    </div>
                    <div style='text-align:right; min-width:80px;'>
                        <div class="match-score {score_cls}" style='font-size:14px;'>{score_str}</div>
                        <span class="status-badge badge-pending">{job.get('status','new').upper()}</span>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)
        if len(jobs) > 15:
            st.markdown(f'<div style="text-align:center; color:#3d5a80; font-size:12px; font-family: JetBrains Mono, monospace; padding:8px;">... and {len(jobs)-15} more</div>', unsafe_allow_html=True)
