import streamlit as st
from core.store import get_prefs, get_settings, add_jobs, get_jobs

def render():
    prefs = get_prefs()
    settings = get_settings()
    jobs = get_jobs()

    st.markdown("""<div style='padding: 8px 0 28px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 10px; color: #2d4060; letter-spacing: 0.2em;'>MODULE 3A</div>
        <h1 style='font-size: 30px; font-weight: 800; margin: 4px 0 6px; color: #e2e8f0;'>Job Discovery</h1>
        <p style='color: #4a6080; font-size: 14px; margin: 0;'>Pull live job listings from Naukri, LinkedIn, Instahyre, and more — filtered to your profile.</p>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(jobs)}</div><div class="metric-label">Jobs in Pipeline</div></div>', unsafe_allow_html=True)
    with c2:
        new = len([j for j in jobs if j.get("status") == "new"])
        st.markdown(f'<div class="metric-card"><div class="metric-value">{new}</div><div class="metric-label">Unscored</div></div>', unsafe_allow_html=True)
    with c3:
        high = len([j for j in jobs if (j.get("match_score") or 0) >= settings.get("min_match_score", 70)])
        st.markdown(f'<div class="metric-card"><div class="metric-value">{high}</div><div class="metric-label">High Matches</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">SEARCH PARAMETERS</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        query = st.text_input("Job titles to search", value=", ".join(prefs.get("target_roles", [])[:3]),
                              placeholder="e.g. FP&A Manager, Finance Analyst")
        locations = st.text_input("Locations", value=", ".join(prefs.get("locations", [])[:3]),
                                  placeholder="e.g. Bangalore, Mumbai, Remote")
    with c2:
        portals = st.multiselect("Portals to search", ["naukri", "linkedin", "instahyre", "foundit", "wellfound", "remotive"],
                                  default=settings.get("portals", ["naukri", "linkedin"]))
        max_results = st.slider("Max results per portal", 10, 100, 25, step=5)

    exp_filter = st.text_input("Experience filter (optional)", placeholder="e.g. 5-10 years")

    if st.button("🔍 Discover Jobs Now", use_container_width=True):
        if not query:
            st.error("Enter at least one job title to search.")
            return

        from core import scrapers
        log_box = st.empty()
        bar = st.progress(0)
        log_lines = [f"[INIT] Starting discovery across {len(portals)} portals..."]
        total_added = 0

        for i, portal in enumerate(portals):
            log_lines.append(f"[{portal.upper()}] Searching: {query[:50]}...")
            log_box.markdown(f'<div class="terminal-log">{"<br>".join(log_lines[-8:])}</div>', unsafe_allow_html=True)
            bar.progress(int((i + 0.5) / len(portals) * 100))

            try:
                fn = getattr(scrapers, f"scrape_{portal}", None)
                if fn:
                    new_jobs = fn(query, locations, max_results, settings.get("jsearch_api_key", ""))
                    added = add_jobs(new_jobs)
                    total_added += added
                    log_lines.append(f"[{portal.upper()}] +{added} new jobs added")
                else:
                    log_lines.append(f"[{portal.upper()}] Scraper not available — skipped")
            except Exception as e:
                log_lines.append(f"[{portal.upper()}] Error: {str(e)[:60]}")

            bar.progress(int((i + 1) / len(portals) * 100))

        log_lines.append(f"[DONE] {total_added} new jobs added to pipeline")
        log_box.markdown(f'<div class="terminal-log">{"<br>".join(log_lines[-10:])}</div>', unsafe_allow_html=True)

        if total_added > 0:
            st.success(f"✓ {total_added} new jobs discovered. Run AI Matching to score them.")
        else:
            st.info("No new jobs found. Try different search terms or portals.")
        st.rerun()

    # Jobs table
    if jobs:
        st.markdown('<div class="section-header">CURRENT PIPELINE</div>', unsafe_allow_html=True)
        col_f, col_s = st.columns([3, 1])
        with col_f:
            portal_filter = st.multiselect("Filter by portal", list({j.get("portal", "unknown") for j in jobs}), label_visibility="collapsed", placeholder="Filter by portal...")
        with col_s:
            sort_order = st.selectbox("Sort", ["Newest First", "By Match Score"], label_visibility="collapsed")

        display_jobs = jobs if not portal_filter else [j for j in jobs if j.get("portal") in portal_filter]
        if sort_order == "By Match Score":
            display_jobs = sorted(display_jobs, key=lambda x: x.get("match_score") or 0, reverse=True)
        else:
            display_jobs = sorted(display_jobs, key=lambda x: x.get("scraped_at", ""), reverse=True)

        for job in display_jobs[:40]:
            score = job.get("match_score")
            score_cls = "score-high" if (score or 0) >= 70 else ("score-mid" if (score or 0) >= 50 else "score-low")
            score_str = f'<span class="match-score {score_cls}">{score}%</span>' if score is not None else '<span style="color:#4a6080; font-size:12px;">Unscored</span>'
            st.markdown(f"""<div class="job-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div class="job-title">{job.get('title', '')} <span class="job-company">@ {job.get('company', '')}</span></div>
                        <div class="job-meta">{job.get('portal','').upper()} · {job.get('location','—')} · {job.get('salary','Salary not listed')}</div>
                    </div>
                    <div style="text-align:right;">
                        {score_str}
                        {f'<div style="margin-top:4px;"><a href="{job["url"]}" target="_blank" style="font-size:11px; color:#6366f1;">View →</a></div>' if job.get("url") else ''}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)
