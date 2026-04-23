import streamlit as st
from core.store import get_prefs, save_prefs, get_settings
from core.ai_engine import analyze_resume_ats


def extract_text_from_pdf(uploaded_file) -> str:
    try:
        import fitz
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        return "\n".join(page.get_text() for page in doc)
    except Exception:
        pass
    try:
        import PyPDF2
        from io import BytesIO
        reader = PyPDF2.PdfReader(BytesIO(uploaded_file.getvalue()))
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception:
        return ""


def _parse_resume_with_ai(resume_text: str, groq_key: str) -> dict:
    import json, urllib.request
    prompt = f"""Extract job search preferences from this resume. Return ONLY valid JSON, no markdown.

RESUME:
{resume_text[:3000]}

Extract and return:
{{
  "name": "full name",
  "email": "email if found else empty string",
  "phone": "phone if found else empty string",
  "experience_years": <integer years of total experience>,
  "current_role": "most recent job title",
  "industry": "primary industry",
  "target_roles": ["3-5 job titles this person should target"],
  "keywords": ["8-12 key skills/tools from the resume"],
  "locations": ["cities mentioned or inferred from resume"],
  "min_salary_lpa": <integer, estimate based on experience>,
  "max_salary_lpa": <integer, estimate based on experience>,
  "education": "highest degree and institution"
}}"""
    try:
        payload = json.dumps({
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 700, "temperature": 0.1,
        }).encode()
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = json.loads(r.read())["choices"][0]["message"]["content"]
        raw = raw.strip().strip("```json").strip("```").strip()
        return json.loads(raw)
    except Exception:
        return {}


def render():
    prefs = get_prefs()
    settings = get_settings()
    groq_key = settings.get("groq_api_key", "") or ""

    st.markdown("""<div style='padding: 8px 0 28px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 10px; color: #2d4060; letter-spacing: 0.2em;'>MODULE 2</div>
        <h1 style='font-size: 30px; font-weight: 800; margin: 4px 0 6px; color: #e2e8f0;'>Resume Optimizer</h1>
        <p style='color: #4a6080; font-size: 14px; margin: 0;'>Get your ATS score, percentile ranking, and a recruiter-grade analysis of your resume — in 30 seconds.</p>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📤 Upload & Analyze", "📊 ATS Report", "🎯 Job Preferences"])

    with tab1:
        st.markdown('<div class="section-header">UPLOAD YOUR RESUME</div>', unsafe_allow_html=True)

        uploaded = st.file_uploader("Drop your resume here (PDF)", type=["pdf"], label_visibility="collapsed")
        if uploaded:
            with st.spinner("Extracting resume text..."):
                text = extract_text_from_pdf(uploaded)
            if text:
                prefs["resume_text"] = text
                prefs["resume_path"] = uploaded.name
                save_prefs(prefs)
                st.success(f"✓ Resume extracted — {len(text)} characters")

                if groq_key:
                    with st.spinner("Parsing your profile with AI..."):
                        parsed = _parse_resume_with_ai(text, groq_key)
                    if parsed:
                        for key in ["name", "email", "phone", "experience_years", "current_role",
                                    "industry", "target_roles", "keywords", "locations",
                                    "min_salary_lpa", "max_salary_lpa", "education"]:
                            if parsed.get(key) and not prefs.get(key):
                                prefs[key] = parsed[key]
                        save_prefs(prefs)
                        st.success("✓ Profile auto-populated from your resume")
            else:
                st.error("Could not extract text from this PDF. Try a text-based PDF.")

        # Manual resume text
        with st.expander("Or paste resume text directly"):
            manual_text = st.text_area("Paste your resume here", value=prefs.get("resume_text", "")[:500] + "..." if len(prefs.get("resume_text", "")) > 500 else prefs.get("resume_text", ""), height=200)
            if st.button("Save Resume Text"):
                prefs["resume_text"] = manual_text
                save_prefs(prefs)
                st.success("Saved.")

        # Run ATS analysis
        st.markdown('<div class="section-header">RUN ATS ANALYSIS</div>', unsafe_allow_html=True)
        if prefs.get("resume_text"):
            if st.button("🔍 Analyze Resume — Get ATS Score", use_container_width=True):
                with st.spinner("Running recruiter-grade analysis..."):
                    result = analyze_resume_ats(prefs["resume_text"], prefs, groq_key)
                st.session_state["ats_result"] = result
                st.success("Analysis complete! View your ATS Report →")
                st.rerun()
        else:
            st.info("Upload or paste your resume above to run ATS analysis.")

    with tab2:
        result = st.session_state.get("ats_result")
        if not result:
            st.markdown("""<div style='text-align:center; padding: 60px; background: #0c1020; border: 1px dashed #1a2540; border-radius: 12px;'>
                <div style='font-size: 28px; margin-bottom: 12px;'>📊</div>
                <div style='font-size: 13px; color: #4a6080;'>Run the ATS analysis from the Upload tab to see your report here.</div>
            </div>""", unsafe_allow_html=True)
        else:
            score = result.get("ats_score", 0)
            percentile = result.get("percentile", 50)
            score_color = "#22d3a5" if score >= 75 else ("#f59e0b" if score >= 55 else "#f87171")
            top_pct = 100 - percentile

            # Score hero
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                st.markdown(f"""<div class="metric-card" style='text-align:center;'>
                    <div style='font-size: 56px; font-weight: 800; color: {score_color}; font-family: JetBrains Mono, monospace; line-height:1;'>{score}</div>
                    <div style='font-size: 13px; color: #7a8faa; margin-top: 6px;'>ATS Score / 100</div>
                    <div class="prob-bar-wrap" style='margin-top: 10px;'><div class="prob-bar-fill" style='width:{score}%;'></div></div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="metric-card" style='text-align:center;'>
                    <div style='font-size: 38px; font-weight: 800; color: #6366f1; font-family: JetBrains Mono, monospace; line-height:1;'>Top {top_pct}%</div>
                    <div style='font-size: 13px; color: #7a8faa; margin-top: 6px;'>Candidate Ranking</div>
                    <div style='font-size: 11px; color: #4a6080; margin-top: 4px;'>vs. similar applicants</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                verdict = result.get("overall_verdict", "")
                st.markdown(f"""<div class="metric-card">
                    <div style='font-size: 11px; color: #4a6080; font-family: JetBrains Mono, monospace; margin-bottom: 8px;'>VERDICT</div>
                    <div style='font-size: 13px; color: #e2e8f0;'>{verdict}</div>
                </div>""", unsafe_allow_html=True)

            # Quick wins
            quick_wins = result.get("quick_wins", [])
            if quick_wins:
                st.markdown('<div class="section-header">QUICK WINS — DO THESE FIRST</div>', unsafe_allow_html=True)
                for i, win in enumerate(quick_wins):
                    st.markdown(f"""<div style='display:flex; align-items:center; margin-bottom: 8px; background: #052e16; border: 1px solid #166534; border-radius: 8px; padding: 10px 14px;'>
                        <div style='color: #22d3a5; font-size: 14px; margin-right: 10px; font-weight: 700;'>{i+1}</div>
                        <div style='font-size: 13px; color: #e2e8f0;'>{win}</div>
                    </div>""", unsafe_allow_html=True)

            # Strengths vs gaps
            col_s, col_g = st.columns(2)
            with col_s:
                strengths = result.get("strengths", [])
                st.markdown('<div class="section-header">STRENGTHS</div>', unsafe_allow_html=True)
                for s in strengths:
                    st.markdown(f"""<div style='background:#052e16; border:1px solid #166534; border-radius:6px; padding:8px 12px; margin-bottom:6px; font-size:13px; color:#e2e8f0;'>✓ {s}</div>""", unsafe_allow_html=True)

            with col_g:
                gaps = result.get("critical_gaps", [])
                st.markdown('<div class="section-header">CRITICAL GAPS</div>', unsafe_allow_html=True)
                for g in gaps:
                    st.markdown(f"""<div style='background:#1c0a0a; border:1px solid #7f1d1d; border-radius:6px; padding:8px 12px; margin-bottom:6px; font-size:13px; color:#e2e8f0;'>✗ {g}</div>""", unsafe_allow_html=True)

            # Missing keywords
            missing_kw = result.get("missing_keywords", [])
            if missing_kw:
                st.markdown('<div class="section-header">MISSING ATS KEYWORDS</div>', unsafe_allow_html=True)
                st.markdown(f"""<div style='background: #0c1020; border:1px solid #1a2540; border-radius:8px; padding:14px;'>
                    {''.join(f'<span style="background:#1c0a0a; color:#f87171; border:1px solid #7f1d1d; border-radius:4px; padding:3px 10px; font-size:12px; font-family: JetBrains Mono, monospace; margin-right:6px; margin-bottom:6px; display:inline-block;">{kw}</span>' for kw in missing_kw)}
                </div>""", unsafe_allow_html=True)

            # Impact rewrites
            weak = result.get("impact_statements_weak", [])
            improved = result.get("impact_statements_improved", [])
            if weak and improved:
                st.markdown('<div class="section-header">IMPACT STATEMENT REWRITES</div>', unsafe_allow_html=True)
                for w, imp in zip(weak, improved):
                    st.markdown(f"""<div style='background:#0c1020; border:1px solid #1a2540; border-radius:8px; padding:14px; margin-bottom:10px;'>
                        <div style='font-size:11px; color:#f87171; font-family: JetBrains Mono, monospace; margin-bottom:4px;'>BEFORE</div>
                        <div style='font-size:13px; color:#7a8faa; margin-bottom:10px;'>{w}</div>
                        <div style='font-size:11px; color:#22d3a5; font-family: JetBrains Mono, monospace; margin-bottom:4px;'>AFTER</div>
                        <div style='font-size:13px; color:#e2e8f0;'>{imp}</div>
                    </div>""", unsafe_allow_html=True)

            # Recommended summary
            summary = result.get("recommended_summary", "")
            if summary:
                st.markdown('<div class="section-header">RECOMMENDED PROFESSIONAL SUMMARY</div>', unsafe_allow_html=True)
                st.markdown(f"""<div style='background:#1e1b4b; border:1px solid #3730a3; border-radius:8px; padding:16px; font-size:13px; color:#e2e8f0; line-height:1.7;'>{summary}</div>""", unsafe_allow_html=True)
                st.code(summary, language=None)

    with tab3:
        st.markdown('<div class="section-header">JOB SEARCH PREFERENCES</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name", value=prefs.get("name", ""))
            email = st.text_input("Email", value=prefs.get("email", ""))
            current_role = st.text_input("Current Role", value=prefs.get("current_role", ""))
            exp = st.number_input("Years of Experience", value=prefs.get("experience_years", 3), min_value=0, max_value=40)
            industry = st.text_input("Industry", value=prefs.get("industry", ""))
        with c2:
            min_sal = st.number_input("Min Salary (LPA)", value=prefs.get("min_salary_lpa", 10))
            max_sal = st.number_input("Max Salary (LPA)", value=prefs.get("max_salary_lpa", 25))
            locations = st.text_area("Preferred Locations (one per line)", value="\n".join(prefs.get("locations", [])), height=80)
            education = st.text_input("Education", value=prefs.get("education", ""))

        target_roles = st.text_area("Target Roles (one per line)", value="\n".join(prefs.get("target_roles", [])), height=80)
        keywords = st.text_area("Key Skills (comma separated)", value=", ".join(prefs.get("keywords", [])), height=60)
        exclude = st.text_area("Exclude Keywords (comma separated)", value=", ".join(prefs.get("exclude_keywords", [])), height=40)

        if st.button("💾 Save Preferences", use_container_width=True):
            prefs.update({
                "name": name, "email": email, "current_role": current_role,
                "experience_years": exp, "industry": industry,
                "min_salary_lpa": min_sal, "max_salary_lpa": max_sal,
                "education": education,
                "locations": [l.strip() for l in locations.split("\n") if l.strip()],
                "target_roles": [r.strip() for r in target_roles.split("\n") if r.strip()],
                "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
                "exclude_keywords": [k.strip() for k in exclude.split(",") if k.strip()],
            })
            save_prefs(prefs)
            st.success("✓ Preferences saved")
