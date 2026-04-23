import streamlit as st
from core.store import get_prefs, get_settings, get_career_intel, save_career_intel
from core.ai_engine import analyze_career_paths


def render():
    prefs = get_prefs()
    settings = get_settings()
    api_key = settings.get("groq_api_key", "") or ""
    cached = get_career_intel()

    st.markdown("""<div style='padding: 8px 0 28px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 10px; color: #2d4060; letter-spacing: 0.2em;'>MODULE 1</div>
        <h1 style='font-size: 30px; font-weight: 800; margin: 4px 0 6px; color: #e2e8f0;'>Career Intelligence Engine</h1>
        <p style='color: #4a6080; font-size: 14px; margin: 0;'>Your strategic decision engine. Know exactly which paths to pursue and why — before you apply to a single job.</p>
    </div>""", unsafe_allow_html=True)

    if not prefs.get("resume_text") and not prefs.get("target_roles"):
        st.markdown("""<div class="insight-card warning">
            <div style='font-weight: 600; color: #fbbf24; margin-bottom: 6px;'>⚡ Complete your profile first</div>
            <div style='color: #7a8faa; font-size: 13px;'>Upload your resume in the Resume Optimizer, then return here for your personalized career roadmap.</div>
        </div>""", unsafe_allow_html=True)
        return

    # ── Input form ─────────────────────────────────────────
    st.markdown('<div class="section-header">YOUR CAREER PROFILE</div>', unsafe_allow_html=True)
    with st.expander("Review & Update Profile Inputs", expanded=not bool(cached)):
        c1, c2 = st.columns(2)
        with c1:
            current_role = st.text_input("Current Role", value=prefs.get("current_role", ""))
            experience = st.number_input("Years of Experience", value=prefs.get("experience_years", 3), min_value=0, max_value=40)
            target_salary_min = st.number_input("Target Salary Min (LPA)", value=prefs.get("min_salary_lpa", 10))
        with c2:
            industry = st.text_input("Industry", value=prefs.get("industry", ""))
            target_salary_max = st.number_input("Target Salary Max (LPA)", value=prefs.get("max_salary_lpa", 25))
            location = st.text_input("Preferred Locations", value=", ".join(prefs.get("locations", [])))

        target_roles_raw = st.text_area("Target Roles (one per line)",
            value="\n".join(prefs.get("target_roles", [])), height=80)
        skills_raw = st.text_area("Key Skills (comma separated)",
            value=", ".join(prefs.get("keywords", [])), height=60)

        if st.button("💾 Save & Run Analysis", use_container_width=True):
            from core.store import save_prefs
            prefs["current_role"] = current_role
            prefs["experience_years"] = experience
            prefs["industry"] = industry
            prefs["min_salary_lpa"] = target_salary_min
            prefs["max_salary_lpa"] = target_salary_max
            prefs["locations"] = [l.strip() for l in location.split(",") if l.strip()]
            prefs["target_roles"] = [r.strip() for r in target_roles_raw.split("\n") if r.strip()]
            prefs["keywords"] = [k.strip() for k in skills_raw.split(",") if k.strip()]
            save_prefs(prefs)

            with st.spinner("Analyzing your career landscape..."):
                result = analyze_career_paths(prefs, api_key)
                save_career_intel(result)
                cached = result
            st.success("Analysis complete!")
            st.rerun()

    if not cached:
        st.markdown("""<div style='text-align:center; padding: 60px; background: #0c1020; border: 1px dashed #1a2540; border-radius: 12px;'>
            <div style='font-size: 32px; margin-bottom: 12px;'>🧠</div>
            <div style='font-size: 14px; color: #4a6080;'>Expand the profile section above and click "Save & Run Analysis" to generate your career roadmap.</div>
        </div>""", unsafe_allow_html=True)
        return

    # ── Market overview ────────────────────────────────────
    demand = cached.get("market_demand", "Medium")
    demand_color = {"High": "#22d3a5", "Medium": "#f59e0b", "Low": "#f87171"}.get(demand, "#f59e0b")

    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #0f1629, #111827); border: 1px solid #1a2540; border-radius: 12px; padding: 20px 24px; margin-bottom: 24px;'>
        <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
            <div>
                <div style='font-size: 11px; color: #4a6080; font-family: JetBrains Mono, monospace; letter-spacing: 0.1em; margin-bottom: 6px;'>MARKET INTELLIGENCE</div>
                <div style='font-size: 14px; color: #e2e8f0;'>{cached.get("competitive_insight", "")}</div>
            </div>
            <div style='text-align:right; flex-shrink:0; margin-left:20px;'>
                <div style='font-size: 11px; color: #4a6080; margin-bottom: 4px;'>MARKET DEMAND</div>
                <div style='font-size: 20px; font-weight: 700; color: {demand_color}; font-family: JetBrains Mono, monospace;'>{demand}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Career paths ───────────────────────────────────────
    st.markdown('<div class="section-header">YOUR 5 CAREER PATHS — RANKED BY SUCCESS PROBABILITY</div>', unsafe_allow_html=True)

    paths = cached.get("career_paths", [])
    for i, path in enumerate(paths):
        prob = path.get("success_probability", 50)
        prob_color = "#22d3a5" if prob >= 75 else ("#f59e0b" if prob >= 55 else "#f87171")
        category = path.get("category", "")
        cat_colors = {"Upward": "#6366f1", "Lateral": "#22d3a5", "Pivot": "#f59e0b"}
        cat_color = cat_colors.get(category, "#7a8faa")
        priority = path.get("action_priority", i + 1)

        with st.expander(f"{'★' if priority == 1 else f'#{priority}'}  {path.get('title', '')}  ·  {prob}% success probability", expanded=(i == 0)):
            col_left, col_right = st.columns([3, 2])

            with col_left:
                st.markdown(f"""
                <div style='margin-bottom: 12px;'>
                    <span style='background: {cat_color}22; color: {cat_color}; border: 1px solid {cat_color}44; border-radius: 20px; padding: 2px 12px; font-size: 11px; font-family: JetBrains Mono, monospace;'>{category}</span>
                    <span style='color: #4a6080; font-size: 12px; margin-left: 10px;'>⏱ {path.get('time_to_achieve', '')}</span>
                </div>
                <div style='font-size: 13px; color: #7a8faa; margin-bottom: 16px;'>{path.get('why_fit', '')}</div>
                """, unsafe_allow_html=True)

                # Salary trajectory
                st.markdown("""<div style='font-size: 11px; color: #4a6080; font-family: JetBrains Mono, monospace; margin-bottom: 8px;'>SALARY TRAJECTORY</div>""", unsafe_allow_html=True)
                s1, s3, s5 = st.columns(3)
                for col, year, val in [(s1, "Year 1", path.get("salary_year1", 0)),
                                        (s3, "Year 3", path.get("salary_year3", 0)),
                                        (s5, "Year 5", path.get("salary_year5", 0))]:
                    with col:
                        st.markdown(f"""<div style='background: #0c1020; border: 1px solid #1a2540; border-radius: 8px; padding: 10px; text-align:center;'>
                            <div style='font-size: 16px; font-weight: 700; color: #22d3a5; font-family: JetBrains Mono, monospace;'>₹{val}L</div>
                            <div style='font-size: 10px; color: #4a6080; margin-top: 2px;'>{year}</div>
                        </div>""", unsafe_allow_html=True)

                # Skill gaps
                gaps = path.get("skill_gaps", [])
                if gaps:
                    st.markdown(f"""<div style='margin-top: 14px;'>
                        <div style='font-size: 11px; color: #4a6080; font-family: JetBrains Mono, monospace; margin-bottom: 6px;'>SKILL GAPS TO CLOSE</div>
                        <div>{''.join(f'<span style="background:#1c0a0a; color:#f87171; border:1px solid #7f1d1d; border-radius:4px; padding:2px 8px; font-size:11px; margin-right:6px;">{g}</span>' for g in gaps)}</div>
                    </div>""", unsafe_allow_html=True)

                certs = path.get("recommended_certifications", [])
                if certs:
                    st.markdown(f"""<div style='margin-top: 10px;'>
                        <div style='font-size: 11px; color: #4a6080; font-family: JetBrains Mono, monospace; margin-bottom: 6px;'>CERTIFICATIONS</div>
                        <div>{''.join(f'<span style="background:#1e1b4b; color:#a5b4fc; border:1px solid #3730a3; border-radius:4px; padding:2px 8px; font-size:11px; margin-right:6px;">{c}</span>' for c in certs)}</div>
                    </div>""", unsafe_allow_html=True)

            with col_right:
                st.markdown(f"""
                <div style='background: #060912; border: 1px solid #1a2540; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 14px;'>
                    <div style='font-size: 11px; color: #4a6080; font-family: JetBrains Mono, monospace; margin-bottom: 8px;'>SUCCESS PROBABILITY</div>
                    <div style='font-size: 48px; font-weight: 800; color: {prob_color}; font-family: JetBrains Mono, monospace; line-height: 1;'>{prob}%</div>
                    <div class="prob-bar-wrap" style='margin-top: 12px;'>
                        <div class="prob-bar-fill" style='width: {prob}%;'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                companies = path.get("companies_hiring", [])
                if companies:
                    st.markdown(f"""<div style='background: #0c1020; border: 1px solid #1a2540; border-radius: 8px; padding: 14px;'>
                        <div style='font-size: 11px; color: #4a6080; font-family: JetBrains Mono, monospace; margin-bottom: 8px;'>HIRING NOW</div>
                        {''.join(f'<div style="font-size: 12px; color: #7a8faa; margin-bottom: 4px;">→ {c}</div>' for c in companies[:4])}
                    </div>""", unsafe_allow_html=True)

    # ── Missing keywords ───────────────────────────────────
    missing_kw = cached.get("ats_keywords_missing", [])
    if missing_kw:
        st.markdown('<div class="section-header">ATS KEYWORDS TO ADD TO YOUR RESUME</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="insight-card danger">
            <div style='font-size: 13px; color: #f87171; font-weight: 600; margin-bottom: 8px;'>These keywords are missing from your resume but expected by ATS systems:</div>
            <div>{''.join(f'<span style="background:#1c0a0a; color:#f87171; border:1px solid #7f1d1d; border-radius:4px; padding:3px 10px; font-size:12px; font-family: JetBrains Mono, monospace; margin-right:6px; margin-bottom:6px; display:inline-block;">{kw}</span>' for kw in missing_kw)}</div>
        </div>""", unsafe_allow_html=True)

    # ── Immediate actions ──────────────────────────────────
    actions = cached.get("immediate_actions", [])
    if actions:
        st.markdown('<div class="section-header">YOUR IMMEDIATE ACTION PLAN</div>', unsafe_allow_html=True)
        for i, action in enumerate(actions):
            st.markdown(f"""<div style='display:flex; align-items:flex-start; margin-bottom: 10px; background: #0f1629; border: 1px solid #1a2540; border-radius: 8px; padding: 12px 16px;'>
                <div class="step-number">{i+1}</div>
                <div style='font-size: 13px; color: #e2e8f0;'>{action}</div>
            </div>""", unsafe_allow_html=True)

    if st.button("🔄 Regenerate Analysis"):
        save_career_intel({})
        st.rerun()
