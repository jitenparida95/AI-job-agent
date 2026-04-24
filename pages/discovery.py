import streamlit as st
from core.store import get_prefs, get_settings, add_jobs, get_jobs, save_jobs


DEMO_JOBS = [
    {"title": "Senior FP&A Analyst", "company": "Unilever GCC", "location": "Bangalore", "salary": "18-24 LPA",
     "description": "FP&A, budgeting, forecasting, variance analysis, SAP, Power BI. Support Supply Chain P&L. 5+ years finance experience.",
     "url": "https://www.naukri.com", "portal": "naukri", "match_score": None, "status": "new"},
    {"title": "Finance Manager - Supply Chain", "company": "Reckitt GCC", "location": "Bangalore", "salary": "22-28 LPA",
     "description": "Lead supply chain finance. FP&A, IFRS, working capital, DIO/DSO analysis. FMCG experience required.",
     "url": "https://www.linkedin.com", "portal": "linkedin", "match_score": None, "status": "new"},
    {"title": "Business Analyst - Finance", "company": "Capgemini", "location": "Bangalore", "salary": "16-22 LPA",
     "description": "Finance BA role. Requirements gathering, SAP FI, stakeholder management, Power BI dashboards.",
     "url": "https://www.naukri.com", "portal": "naukri", "match_score": None, "status": "new"},
    {"title": "FP&A Lead", "company": "Marico Ltd", "location": "Mumbai", "salary": "20-26 LPA",
     "description": "Lead FP&A function. Monthly MIS, annual budgeting, 3-year LRP, EBITDA tracking.",
     "url": "https://www.foundit.in", "portal": "foundit", "match_score": None, "status": "new"},
    {"title": "Senior Financial Analyst", "company": "ITC Limited", "location": "Bangalore", "salary": "15-20 LPA",
     "description": "Financial planning and analysis, variance reporting, management reporting. CA/MBA preferred.",
     "url": "https://www.naukri.com", "portal": "naukri", "match_score": None, "status": "new"},
    {"title": "Finance Business Partner", "company": "Hindustan Unilever", "location": "Mumbai", "salary": "24-32 LPA",
     "description": "Strategic finance partner to business units. P&L ownership, forecasting, investment appraisals.",
     "url": "https://www.linkedin.com", "portal": "linkedin", "match_score": None, "status": "new"},
]


def render():
    prefs    = get_prefs()
    settings = get_settings()
    jobs     = get_jobs()

    st.markdown("""<div style='padding: 8px 0 28px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 10px; color: #2d4060; letter-spacing: 0.2em;'>MODULE 3A</div>
        <h1 style='font-size: 30px; font-weight: 800; margin: 4px 0 6px; color: #e2e8f0;'>Job Discovery</h1>
        <p style='color: #4a6080; font-size: 14px; margin: 0;'>Pull live job listings from Naukri, LinkedIn, Instahyre, and more — filtered to your profile.</p>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    new = len([j for j in jobs if j.get("status") == "new"])
    high = len([j for j in jobs if (j.get("match_score") or 0) >= settings.get("min_match_score", 70)])
    c1.markdown(f'<div class="metric-card"><div class="metric-value">{len(jobs)}</div><div class="metric-label">Jobs in Pipeline</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-value">{new}</div><div class="metric-label">Unscored</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-value">{high}</div><div class="metric-label">High Matches</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">SEARCH PARAMETERS</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        query = st.text_input("Job titles to search",
            value=", ".join((prefs.get("target_roles") or [])[:3]) or "FP&A Analyst, Finance Manager",
            placeholder="e.g. FP&A Manager, Finance Analyst")
        locations = st.text_input("Locations",
            value=", ".join((prefs.get("locations") or [])[:3]) or "Bangalore, Remote, India",
            placeholder="e.g. Bangalore, Mumbai, Remote")
    with c2:
        portals = st.multiselect("Portals to search",
            ["naukri","linkedin","instahyre","foundit","jsearch"],
            default=["naukri","linkedin"])
        max_results = st.slider("Max results per portal", 10, 100, 25, step=5)

    jsearch_key = settings.get("jsearch_api_key","")
    if not jsearch_key:
        st.markdown('<div class="insight-card info"><div style="font-size:13px;color:#a5b4fc;">ℹ️ Add JSearch API key in Settings for live job results from LinkedIn, Naukri, Indeed. Without it, demo jobs will be shown.</div></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3,1])
    with col1:
        discover = st.button("🔍 Discover Jobs Now", use_container_width=True, disabled=not portals)
    with col2:
        if st.button("🗑️ Clear Queue", use_container_width=True):
            save_jobs([])
            st.rerun()

    if discover:
        log_box = st.empty()
        bar = st.progress(0)
        log_lines = [f"[INIT] Starting discovery across {len(portals)} portals..."]
        total_added = 0

        # Try real scrapers first
        keywords = [q.strip() for q in query.split(",") if q.strip()]
        loc_list = [l.strip() for l in locations.split(",") if l.strip()]

        for i, portal in enumerate(portals):
            log_lines.append(f"[{portal.upper()}] Searching: {query[:50]}...")
            log_box.markdown(f'<div class="terminal-log">{"<br>".join(log_lines[-8:])}</div>', unsafe_allow_html=True)
            bar.progress(int((i + 0.5) / len(portals) * 100))

            new_jobs = []
            try:
                from core import scrapers
                if portal == "jsearch" and jsearch_key:
                    new_jobs = scrapers.scrape_jsearch(jsearch_key, keywords, loc_list, max_results)
                elif portal == "naukri":
                    new_jobs = scrapers.scrape_naukri(keywords, loc_list, prefs.get("experience_years", 6))
                elif portal == "linkedin":
                    new_jobs = scrapers.scrape_linkedin(keywords, loc_list,
                        settings.get("linkedin_email",""), settings.get("linkedin_password",""))
                elif portal == "instahyre":
                    new_jobs = scrapers.scrape_instahyre(keywords, loc_list)
                elif portal == "foundit":
                    new_jobs = scrapers.scrape_foundit(keywords, loc_list)
            except Exception as e:
                log_lines.append(f"[{portal.upper()}] Error: {str(e)[:50]}")

            added = add_jobs(new_jobs) if new_jobs else 0
            total_added += added
            log_lines.append(f"[{portal.upper()}] +{added} new jobs added")
            bar.progress(int((i + 1) / len(portals) * 100))

        # Fallback to demo jobs if nothing found
        if total_added == 0:
            log_lines.append("[INFO] No live results — loading demo jobs for preview")
            total_added = add_jobs(DEMO_JOBS)
            log_lines.append(f"[DEMO] +{total_added} demo finance jobs loaded")

        log_lines.append(f"[DONE] {total_added} new jobs added to pipeline")
        log_box.markdown(f'<div class="terminal-log">{"<br>".join(log_lines[-10:])}</div>', unsafe_allow_html=True)
        bar.progress(100)

        if total_added > 0:
            st.success(f"✓ {total_added} jobs added. Run AI Matching to score them.")
        st.rerun()

    # Jobs table
    if jobs:
        st.markdown('<div class="section-header">CURRENT PIPELINE</div>', unsafe_allow_html=True)
        col_f, col_s = st.columns([3,1])
        with col_f:
            portal_filter = st.multiselect("Filter", list({j.get("portal","") for j in jobs}),
                                            label_visibility="collapsed", placeholder="Filter by portal...")
        with col_s:
            sort_order = st.selectbox("Sort", ["Newest First","By Match Score"], label_visibility="collapsed")

        display_jobs = jobs if not portal_filter else [j for j in jobs if j.get("portal") in portal_filter]
        if sort_order == "By Match Score":
            display_jobs = sorted(display_jobs, key=lambda x: x.get("match_score") or 0, reverse=True)
        else:
            display_jobs = sorted(display_jobs, key=lambda x: x.get("scraped_at",""), reverse=True)

        for job in display_jobs[:40]:
            score = job.get("match_score")
            score_cls = "score-high" if (score or 0) >= 70 else ("score-mid" if (score or 0) >= 50 else "score-low")
            score_str = f'<span class="match-score {score_cls}">{score}%</span>' if score is not None else '<span style="color:#4a6080;font-size:12px;">Unscored</span>'
            st.markdown(f"""<div class="job-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div class="job-title">{job.get('title','')} <span class="job-company">@ {job.get('company','')}</span></div>
                        <div class="job-meta">{job.get('portal','').upper()} · {job.get('location','—')} · {job.get('salary','Salary not listed')}</div>
                    </div>
                    <div style="text-align:right;">
                        {score_str}
                        {f'<div style="margin-top:4px;"><a href="{job["url"]}" target="_blank" style="font-size:11px;color:#6366f1;">View →</a></div>' if job.get("url") else ''}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)
