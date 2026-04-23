import streamlit as st
from core.store import get_jobs, save_jobs, get_prefs, get_settings
from core.ai_engine import score_job
import time


def render():
    prefs = get_prefs()
    settings = get_settings()
    jobs = get_jobs()

    st.markdown("""<div style='padding: 8px 0 28px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 10px; color: #2d4060; letter-spacing: 0.2em;'>MODULE 3</div>
        <h1 style='font-size: 30px; font-weight: 800; margin: 4px 0 6px; color: #e2e8f0;'>AI Job Matching</h1>
        <p style='color: #4a6080; font-size: 14px; margin: 0;'>Score every job against your profile. Prioritize exactly which roles to apply to first — and which to skip.</p>
    </div>""", unsafe_allow_html=True)

    unscored = [j for j in jobs if j.get("match_score") is None]
    scored   = [j for j in jobs if j.get("match_score") is not None]
    min_score = settings.get("min_match_score", 70)
    high      = [j for j in scored if j["match_score"] >= min_score]
    avg       = int(sum(j["match_score"] for j in scored) / max(len(scored), 1)) if scored else 0

    # ── Metrics ───────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in [
        (c1, len(jobs),     "Total in Pipeline"),
        (c2, len(unscored), "Awaiting Score"),
        (c3, len(high),     f"High Matches (≥{min_score}%)"),
        (c4, f"{avg}%",     "Average Match Score"),
    ]:
        with col:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{val}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    # ── Settings ──────────────────────────────────────────────
    st.markdown('<div class="section-header">MATCH SETTINGS</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        min_score = st.slider("Apply threshold — minimum match score (%)", 40, 95,
                              value=min_score, step=5)
    with c2:
        api_key = st.text_input("Groq API key",
                                value=settings.get("groq_api_key", ""),
                                type="password",
                                help="Free at console.groq.com — powers AI scoring")

    if not jobs:
        st.markdown("""<div class="insight-card warning">
            <div style='font-weight:600; color:#fbbf24; margin-bottom:4px;'>No jobs in your pipeline yet</div>
            <div style='font-size:13px; color:#7a8faa;'>Run Job Discovery first to populate your queue.</div>
        </div>""", unsafe_allow_html=True)
        return

    # ── Job categorization preview ────────────────────────────
    if scored:
        easy   = [j for j in scored if j["match_score"] >= 80]
        medium = [j for j in scored if 60 <= j["match_score"] < 80]
        stretch= [j for j in scored if j["match_score"] < 60]
        st.markdown('<div class="section-header">JOB OPPORTUNITY TIERS</div>', unsafe_allow_html=True)
        tc1, tc2, tc3 = st.columns(3)
        for col, tier, count, color, desc in [
            (tc1, "🟢 High Probability", len(easy),   "#22d3a5", "Apply first — strong match, easier wins"),
            (tc2, "🟡 Medium Match",     len(medium),  "#f59e0b", "Apply with tailored cover letter"),
            (tc3, "🔴 Stretch Roles",    len(stretch), "#f87171", "Apply selectively — upskill gaps first"),
        ]:
            with col:
                st.markdown(f"""<div style='background:#0c1020; border:1px solid #1a2540; border-radius:10px; padding:16px; text-align:center;'>
                    <div style='font-size:13px; font-weight:600; color:{color}; margin-bottom:6px;'>{tier}</div>
                    <div style='font-size:32px; font-weight:800; color:{color}; font-family:JetBrains Mono,monospace;'>{count}</div>
                    <div style='font-size:11px; color:#4a6080; margin-top:6px;'>{desc}</div>
                </div>""", unsafe_allow_html=True)

    # ── Run scoring ───────────────────────────────────────────
    st.markdown('<div class="section-header">SCORING ENGINE</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        run_all = st.button(f"🤖 Score {len(unscored)} Unscored Jobs", disabled=not unscored,
                            use_container_width=True)
    with col2:
        rescore = st.button("♻️ Re-score All", use_container_width=True)

    targets = jobs if rescore else (unscored if run_all else [])

    if targets:
        bar    = st.progress(0)
        status = st.empty()
        log    = st.empty()
        lines  = [f"[INIT] Scoring {len(targets)} jobs against your profile..."]

        for i, job in enumerate(targets):
            result = score_job(job, prefs, api_key or settings.get("groq_api_key", ""))
            job["match_score"]  = result.get("score", 0)
            job["match_detail"] = result
            job["status"]       = "matched" if job["match_score"] >= min_score else "low-match"

            rec_upper = result.get("recommendation", "").upper()
            lines.append(
                f"[{i+1}/{len(targets)}] {job.get('title','')[:38]} @ {job.get('company','')[:18]} "
                f"→ {job['match_score']}%  [{rec_upper}]"
            )
            log.markdown(f'<div class="terminal-log">{"<br>".join(lines[-12:])}</div>',
                         unsafe_allow_html=True)
            bar.progress(int((i + 1) / len(targets) * 100))

        save_jobs(jobs)
        status.success(f"✓ Done. {len([j for j in jobs if j.get('match_score',0) >= min_score])} jobs meet your threshold.")
        time.sleep(0.5)
        st.rerun()

    # ── Results table ─────────────────────────────────────────
    if scored:
        st.markdown('<div class="section-header">SCORED JOBS — SORTED BY PRIORITY</div>', unsafe_allow_html=True)

        show_only = st.radio(
            "Show",
            ["All scored", f"High match (≥{min_score}%)", "Apply candidates", "Skip / Low match"],
            horizontal=True, label_visibility="collapsed"
        )

        sorted_jobs = sorted(scored, key=lambda j: j.get("match_score", 0), reverse=True)
        if show_only.startswith("High"):
            sorted_jobs = [j for j in sorted_jobs if j.get("match_score", 0) >= min_score]
        elif show_only == "Apply candidates":
            sorted_jobs = [j for j in sorted_jobs if j.get("match_detail", {}).get("recommendation") == "apply"]
        elif show_only.startswith("Skip"):
            sorted_jobs = [j for j in sorted_jobs if j.get("match_score", 0) < min_score]

        for job in sorted_jobs[:40]:
            score      = job.get("match_score", 0)
            detail     = job.get("match_detail", {})
            score_cls  = "score-high" if score >= 70 else ("score-mid" if score >= 50 else "score-low")
            rec        = detail.get("recommendation", "")
            rec_color  = {"apply": "#22d3a5", "maybe": "#f59e0b", "skip": "#f87171"}.get(rec, "#5a7090")
            matched_kw = detail.get("matched_keywords", [])
            missing_kw = detail.get("missing", [])

            with st.expander(
                f"{job.get('title','')} @ {job.get('company','')}  ·  {score}% match  ·  {rec.upper()}",
                expanded=False
            ):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(
                        f"**Portal:** {job.get('portal','').upper()}  ·  "
                        f"**Location:** {job.get('location','—')}  ·  "
                        f"**Salary:** {job.get('salary','Not listed')}"
                    )
                    if detail.get("reasons"):
                        st.markdown("**AI Analysis:** " + " · ".join(detail.get("reasons", [])))
                    if matched_kw:
                        st.markdown(f"**✓ Matched:** {', '.join(matched_kw[:8])}")
                    if missing_kw:
                        st.markdown(f"**✗ Missing:** {', '.join(missing_kw[:4])}")
                    if job.get("url"):
                        st.markdown(f"[View Job Posting →]({job['url']})")
                with c2:
                    st.markdown(f"""<div style='text-align:center; padding:16px; background:#060912; border:1px solid #1a2540; border-radius:10px;'>
                        <div class="match-score {score_cls}" style='font-size:44px;'>{score}%</div>
                        <div style='font-size:12px; color:{rec_color}; font-family:JetBrains Mono,monospace;
                                    margin-top:8px; font-weight:700; text-transform:uppercase;'>{rec}</div>
                    </div>""", unsafe_allow_html=True)
