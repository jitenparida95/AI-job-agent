import streamlit as st
from core.store import get_jobs, save_jobs, get_prefs, get_settings
from core.ai_engine import score_job
import time


def render():
    prefs = get_prefs()
    settings = get_settings()
    jobs = get_jobs()

    st.markdown("""<div style='padding: 8px 0 24px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 11px; color: #3d5a80; letter-spacing: 0.1em;'>AI ENGINE</div>
        <h1 style='font-size: 28px; margin: 4px 0 0; color: #e8eaf0;'>AI Matching</h1>
        <p style='color: #5a7090; font-size: 14px; margin: 4px 0 0;'>Score every job in your queue against your resume and preferences.</p>
    </div>""", unsafe_allow_html=True)

    unscored = [j for j in jobs if j.get("match_score") is None]
    scored = [j for j in jobs if j.get("match_score") is not None]
    high = [j for j in scored if j["match_score"] >= settings.get("min_match_score", 70)]

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-value">{len(jobs)}</div><div class="metric-label">Total in queue</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-value">{len(unscored)}</div><div class="metric-label">Unscored</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-value">{len(high)}</div><div class="metric-label">High matches</div></div>', unsafe_allow_html=True)
    avg = int(sum(j["match_score"] for j in scored) / max(len(scored), 1))
    c4.markdown(f'<div class="metric-card"><div class="metric-value">{avg}%</div><div class="metric-label">Avg match score</div></div>', unsafe_allow_html=True)

    # Config
    st.markdown('<div class="section-header">MATCH SETTINGS</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        min_score = st.slider("Minimum match score to apply (%)", 40, 95,
                              value=settings.get("min_match_score", 70), step=5)
    with c2:
        api_key = st.text_input("Groq API key (for AI scoring)",
                                value=settings.get("groq_api_key", ""),
                                type="password",
                                help="Get free key at console.groq.com")

    if not jobs:
        st.info("No jobs in queue. Run Job Discovery first.")
        return

    col1, col2 = st.columns([2, 1])
    with col1:
        run_all = st.button(f"🤖  Score All {len(unscored)} Unscored Jobs", disabled=not unscored)
    with col2:
        rescore = st.button("♻️  Re-score All Jobs")

    targets = jobs if rescore else (unscored if run_all else [])

    if targets:
        bar = st.progress(0)
        status = st.empty()
        log = st.empty()
        log_lines = [f"[INIT] Scoring {len(targets)} jobs..."]

        for i, job in enumerate(targets):
            result = score_job(job, prefs, api_key or settings.get("groq_api_key", ""))
            job["match_score"] = result.get("score", 0)
            job["match_detail"] = result
            job["status"] = "matched" if job["match_score"] >= min_score else "low-match"

            log_lines.append(
                f"[{i+1}/{len(targets)}] {job.get('title','')[:40]} @ {job.get('company','')[:20]} → {job['match_score']}% ({result.get('recommendation','').upper()})"
            )
            log.markdown(f'<div class="terminal-log">{"<br>".join(log_lines[-10:])}</div>', unsafe_allow_html=True)
            bar.progress(int((i + 1) / len(targets) * 100))

        save_jobs(jobs)
        status.success(f"✓ Scoring complete. {len([j for j in jobs if j.get('match_score',0) >= min_score])} jobs meet threshold.")
        time.sleep(0.5)
        st.rerun()

    # Results table
    if scored:
        st.markdown('<div class="section-header">SCORED JOBS — SORTED BY MATCH</div>', unsafe_allow_html=True)

        filter_col, sort_col = st.columns([3, 1])
        with filter_col:
            show_only = st.radio("Show", ["All", f"High match (≥{min_score}%)", "Apply candidates"],
                                 horizontal=True, label_visibility="collapsed")
        with sort_col:
            st.markdown("")  # spacer

        sorted_jobs = sorted(scored, key=lambda j: j.get("match_score", 0), reverse=True)
        if show_only.startswith("High"):
            sorted_jobs = [j for j in sorted_jobs if j.get("match_score", 0) >= min_score]
        elif show_only == "Apply candidates":
            sorted_jobs = [j for j in sorted_jobs if j.get("match_detail", {}).get("recommendation") == "apply"]

        for job in sorted_jobs[:30]:
            score = job.get("match_score", 0)
            detail = job.get("match_detail", {})
            score_cls = "score-high" if score >= 70 else ("score-mid" if score >= 50 else "score-low")
            rec = detail.get("recommendation", "")
            rec_color = {"apply": "#22d3a5", "maybe": "#f59e0b", "skip": "#f87171"}.get(rec, "#5a7090")

            matched_kw = detail.get("matched_keywords", [])
            missing_kw = detail.get("missing", [])

            with st.expander(f"{job.get('title','')} @ {job.get('company','')} — {score}% match"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"**Portal:** {job.get('portal','').upper()} · **Location:** {job.get('location','—')} · **Salary:** {job.get('salary','Not listed')}")
                    if detail.get("reasons"):
                        st.markdown("**AI Analysis:** " + " · ".join(detail.get("reasons", [])))
                    if matched_kw:
                        st.markdown(f"**Matched:** {', '.join(matched_kw[:8])}")
                    if missing_kw:
                        st.markdown(f"**Missing:** {', '.join(missing_kw[:4])}")
                    if job.get("url"):
                        st.markdown(f"[View Job →]({job['url']})")
                with c2:
                    st.markdown(f"""<div style='text-align:center; padding:16px;'>
                        <div class="match-score {score_cls}" style='font-size:40px;'>{score}%</div>
                        <div style='font-size:13px; color:{rec_color}; font-family: JetBrains Mono, monospace; margin-top:8px; text-transform:uppercase;'>{rec}</div>
                    </div>""", unsafe_allow_html=True)
