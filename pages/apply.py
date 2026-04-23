import streamlit as st
from core.store import get_jobs, get_prefs, get_settings, log_application
from core.ai_engine import generate_cover_letter
import time

def render():
    prefs = get_prefs()
    settings = get_settings()
    jobs = get_jobs()

    st.markdown("""<div style='padding: 8px 0 28px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 10px; color: #2d4060; letter-spacing: 0.2em;'>MODULE 3C</div>
        <h1 style='font-size: 30px; font-weight: 800; margin: 4px 0 6px; color: #e2e8f0;'>Auto Apply</h1>
        <p style='color: #4a6080; font-size: 14px; margin: 0;'>Automatically apply to your highest-scoring jobs with personalized cover letters.</p>
    </div>""", unsafe_allow_html=True)

    min_score = settings.get("min_match_score", 70)
    ready = [j for j in jobs if (j.get("match_score") or 0) >= min_score and j.get("status") == "matched"]
    api_key = settings.get("groq_api_key", "")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(ready)}</div><div class="metric-label">Ready to Apply</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{min_score}%</div><div class="metric-label">Match Threshold</div></div>', unsafe_allow_html=True)
    with c3:
        limit = settings.get("daily_apply_limit", 30)
        st.markdown(f'<div class="metric-card"><div class="metric-value">{limit}</div><div class="metric-label">Daily Apply Limit</div></div>', unsafe_allow_html=True)

    if not ready:
        st.markdown("""<div class="insight-card warning">
            <div style='font-weight:600; color:#fbbf24; margin-bottom:6px;'>No jobs ready to apply</div>
            <div style='color:#7a8faa; font-size:13px;'>Run Job Discovery and AI Matching first to build your apply queue.</div>
        </div>""", unsafe_allow_html=True)
        return

    if not settings.get("auto_apply_enabled"):
        st.markdown("""<div class="insight-card info">
            <div style='font-weight:600; color:#a5b4fc; margin-bottom:6px;'>Auto-Apply is disabled</div>
            <div style='color:#7a8faa; font-size:13px;'>Enable it in Settings to allow automated form submissions. You can still manually review and copy application content below.</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">APPLY QUEUE</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:13px; color:#7a8faa; margin-bottom:16px;">{len(ready)} jobs ready · sorted by match score</div>', unsafe_allow_html=True)

    sorted_ready = sorted(ready, key=lambda j: j.get("match_score", 0), reverse=True)

    for job in sorted_ready[:20]:
        score = job.get("match_score", 0)
        score_cls = "score-high" if score >= 80 else "score-mid"
        with st.expander(f"{job.get('title','')} @ {job.get('company','')} — {score}% match"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{job.get('location','—')}** · {job.get('salary','Salary not listed')} · {job.get('portal','').upper()}")
                if job.get("url"):
                    st.markdown(f"[Open Job Page →]({job['url']})")
            with c2:
                st.markdown(f'<div class="match-score {score_cls}" style="font-size:28px; text-align:center;">{score}%</div>', unsafe_allow_html=True)

            if st.button("Generate Cover Letter", key=f"cl_{job.get('id','')}"):
                with st.spinner("Generating..."):
                    cl = generate_cover_letter(job, prefs, prefs.get("cover_letter_template", ""), api_key)
                st.session_state[f"cl_text_{job.get('id','')}"] = cl

            cl_text = st.session_state.get(f"cl_text_{job.get('id','')}", "")
            if cl_text:
                st.text_area("Cover Letter", value=cl_text, height=180, key=f"cl_display_{job.get('id','')}")
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("Download Cover Letter", data=cl_text,
                        file_name=f"cover_letter_{job.get('company','')}.txt", key=f"dl_{job.get('id','')}")
                with col2:
                    if st.button("Mark as Applied", key=f"mark_{job.get('id','')}"):
                        log_application(job, cl_text, "applied")
                        job["status"] = "applied"
                        from core.store import save_jobs
                        save_jobs(jobs)
                        st.success("Logged as applied!")
                        st.rerun()

            if settings.get("auto_apply_enabled") and st.button("Auto-Submit Application", key=f"auto_{job.get('id','')}"):
                with st.spinner(f"Submitting to {job.get('portal','').upper()}..."):
                    try:
                        from core.apply_bot import apply_to_job
                        cl = st.session_state.get(f"cl_text_{job.get('id','')}", generate_cover_letter(job, prefs, "", api_key))
                        result = apply_to_job(job, prefs, settings, cl)
                        status = result.get("status", "error")
                        log_application(job, cl, "applied" if status == "applied" else "error")
                        if status == "applied":
                            st.success("Application submitted!")
                        else:
                            st.error(f"Failed: {result.get('message', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error: {e}")
