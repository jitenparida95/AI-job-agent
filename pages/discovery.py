import streamlit as st
from core.store import get_prefs, get_settings, add_jobs, get_jobs, save_jobs
from core.scrapers import DEMO_JOBS


def render():
    prefs    = get_prefs()
    settings = get_settings()
    jobs     = get_jobs()

    st.markdown("""<div style='padding:8px 0 28px;'>
<div style='font-family:JetBrains Mono,monospace;font-size:10px;color:#2d4060;letter-spacing:.2em;'>MODULE 3A</div>
<h1 style='font-size:30px;font-weight:800;margin:4px 0 6px;color:#e2e8f0;'>Job Discovery</h1>
<p style='color:#4a6080;font-size:14px;margin:0;'>Pull live jobs from Naukri, LinkedIn, and more — filtered for FP&A and Finance roles.</p>
</div>""", unsafe_allow_html=True)

    new  = len([j for j in jobs if j.get("status") == "new"])
    high = len([j for j in jobs if (j.get("match_score") or 0) >= settings.get("min_match_score",70)])
    c1,c2,c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="metric-value">{len(jobs)}</div><div class="metric-label">Jobs in Pipeline</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-value">{new}</div><div class="metric-label">Unscored</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-value">{high}</div><div class="metric-label">High Matches</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">SEARCH PARAMETERS</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        query = st.text_input("Job titles to search",
            value=", ".join((prefs.get("target_roles") or [])[:3]) or "Senior FP&A Analyst, Finance Manager, Business Analyst")
        locs  = st.text_input("Locations",
            value=", ".join((prefs.get("locations") or [])[:3]) or "Bangalore, Mumbai, Remote")
    with c2:
        portals = st.multiselect("Portals to search",
            ["naukri","linkedin","instahyre","foundit","jsearch"],
            default=["naukri","linkedin"])
        max_res = st.slider("Max results per portal", 10, 100, 25, step=5)

    jsearch_key = settings.get("jsearch_api_key","")
    if not jsearch_key:
        st.markdown("""<div class="insight-card info">
<div style='font-size:13px;color:#a5b4fc;font-weight:600;margin-bottom:4px;'>💡 JSearch API = Best live results</div>
<div style='font-size:12px;color:#7a8faa;'>Without it, scrapers may be blocked on Streamlit Cloud. Get a free key at rapidapi.com → search "JSearch" → Basic plan (200 calls/month free). Add it in Settings.</div>
</div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([3,1])
    with col1:
        discover = st.button("🔍 Discover Jobs Now", use_container_width=True, disabled=not portals)
    with col2:
        if st.button("🗑️ Clear Queue", use_container_width=True):
            save_jobs([])
            st.success("Queue cleared")
            st.rerun()

    if discover:
        log_box = st.empty()
        bar     = st.progress(0)
        log_lines = [f"[INIT] Starting discovery across {len(portals)} portals..."]
        total_added = 0

        keywords = [q.strip() for q in query.split(",") if q.strip()]
        loc_list = [l.strip() for l in locs.split(",") if l.strip()]

        # Try JSearch first if key available
        if jsearch_key and "jsearch" not in portals:
            portals = ["jsearch"] + portals

        for i, portal in enumerate(portals):
            log_lines.append(f"[{portal.upper()}] Searching: {query[:50]}...")
            log_box.markdown(f'<div class="terminal-log">{"<br>".join(log_lines[-8:])}</div>', unsafe_allow_html=True)
            bar.progress(int((i+0.5)/len(portals)*100))

            new_jobs = []
            try:
                from core import scrapers as sc
                if portal == "jsearch":
                    new_jobs = sc.scrape_jsearch(jsearch_key, keywords, loc_list, max_res)
                elif portal == "naukri":
                    new_jobs = sc.scrape_naukri(keywords, loc_list, prefs.get("experience_years",6))
                elif portal == "linkedin":
                    new_jobs = sc.scrape_linkedin(keywords, loc_list)
                elif portal == "instahyre":
                    new_jobs = sc.scrape_instahyre(keywords, loc_list)
                elif portal == "foundit":
                    new_jobs = sc.scrape_foundit(keywords, loc_list)
            except Exception as e:
                log_lines.append(f"[{portal.upper()}] Blocked/Error: {str(e)[:40]}")

            added = add_jobs(new_jobs) if new_jobs else 0
            total_added += added
            log_lines.append(f"[{portal.upper()}] +{added} new jobs added")
            bar.progress(int((i+1)/len(portals)*100))

        # ALWAYS load demo jobs if nothing found
        if total_added == 0:
            log_lines.append("[INFO] Live scrapers blocked on cloud. Loading curated demo jobs...")
            import uuid; from datetime import datetime
            demo = []
            for j in DEMO_JOBS:
                jc = dict(j)
                jc["id"] = str(uuid.uuid4())[:8]
                jc["scraped_at"] = datetime.now().isoformat()
                demo.append(jc)
            total_added = add_jobs(demo)
            log_lines.append(f"[DEMO] ✓ {total_added} curated FP&A jobs loaded")
            log_lines.append("[TIP] Add JSearch API key in Settings for live jobs from LinkedIn/Naukri/Indeed")

        log_lines.append(f"[DONE] Pipeline now has {len(get_jobs())} jobs total")
        log_box.markdown(f'<div class="terminal-log">{"<br>".join(log_lines[-12:])}</div>', unsafe_allow_html=True)
        bar.progress(100)
        st.success(f"✓ {total_added} jobs added. Go to AI Job Matching to score them.")
        import time; time.sleep(0.5)
        st.rerun()

    # Pipeline display
    if jobs:
        st.markdown('<div class="section-header">CURRENT PIPELINE</div>', unsafe_allow_html=True)
        col_f, col_s = st.columns([3,1])
        with col_f:
            pf = st.multiselect("Filter by portal", list({j.get("portal","") for j in jobs}),
                                label_visibility="collapsed", placeholder="Filter by portal...")
        with col_s:
            so = st.selectbox("Sort", ["Newest First","By Match Score"], label_visibility="collapsed")

        disp = jobs if not pf else [j for j in jobs if j.get("portal") in pf]
        if so == "By Match Score":
            disp = sorted(disp, key=lambda x: x.get("match_score") or 0, reverse=True)
        else:
            disp = sorted(disp, key=lambda x: x.get("scraped_at",""), reverse=True)

        for job in disp[:40]:
            score = job.get("match_score")
            sc = "score-high" if (score or 0)>=70 else ("score-mid" if (score or 0)>=50 else "score-low")
            score_str = f'<span class="match-score {sc}">{score}%</span>' if score is not None else '<span style="color:#4a6080;font-size:12px;">Unscored</span>'
            portal_badge = f'<span style="background:#1a2540;color:#6366f1;border-radius:4px;padding:2px 8px;font-size:10px;font-family:JetBrains Mono,monospace;">{job.get("portal","").upper()}</span>'
            url_str = f'<a href="{job["url"]}" target="_blank" style="font-size:11px;color:#6366f1;margin-left:8px;">View →</a>' if job.get("url") else ""
            st.markdown(f"""<div class="job-card">
<div style="display:flex;justify-content:space-between;align-items:center;">
  <div>
    <div class="job-title">{job.get('title','')} <span class="job-company">@ {job.get('company','')}</span></div>
    <div class="job-meta" style="margin-top:6px;">{portal_badge} {job.get('location','—')} · {job.get('salary','Salary not listed')}{url_str}</div>
  </div>
  <div style="text-align:right;">{score_str}</div>
</div>
</div>""", unsafe_allow_html=True)

        if st.button("→ Score with AI Matching", use_container_width=True):
            st.session_state.page = "AI Job Matching"
            st.rerun()
