import streamlit as st
from core.store import get_prefs, save_prefs, get_settings
import re


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
    """Use Groq to extract job preferences from resume text."""
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
  "target_roles": ["3-5 job titles this person should target based on their background"],
  "keywords": ["8-12 key skills/tools from the resume"],
  "locations": ["cities mentioned or inferred from resume"],
  "min_salary_lpa": <integer, estimate based on experience>,
  "max_salary_lpa": <integer, estimate based on experience>
}}"""

    try:
        payload = json.dumps({
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 600,
            "temperature": 0.1,
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
    except Exception as e:
        return {}


def render():
    prefs = get_prefs()
    settings = get_settings()
    groq_key = settings.get("groq_api_key", "") or st.secrets.get("GROQ_API_KEY", "")

    st.markdown("""<div style='padding: 8px 0 24px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 11px; color: #3d5a80; letter-spacing: 0.1em;'>CONFIGURATION</div>
        <h1 style='font-size: 28px; margin: 4px 0 0; color: #e8eaf0;'>Resume & Preferences</h1>
        <p style='color: #5a7090; font-size: 14px; margin: 4px 0 0;'>The agent uses this to score job matches and personalise applications.</p>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📄 Resume", "🎯 Job Preferences", "✉️ Cover Letter"])

    with tab1:
        st.markdown('<div class="section-header">UPLOAD RESUME</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

        if uploaded:
            text = extract_text_from_pdf(uploaded)
            if text:
                prefs["resume_text"] = text
                prefs["resume_path"] = uploaded.name

                st.success(f"✓ Extracted {len(text.split())} words from resume")

                # Auto-parse with AI if Groq key available
                if groq_key:
                    with st.spinner("🤖 AI is reading your resume and auto-filling your preferences..."):
                        parsed = _parse_resume_with_ai(text, groq_key)

                    if parsed:
                        # Auto-update prefs from resume
                        for field in ["name", "email", "phone", "experience_years",
                                      "target_roles", "keywords", "locations",
                                      "min_salary_lpa", "max_salary_lpa"]:
                            if parsed.get(field):
                                prefs[field] = parsed[field]

                        save_prefs(prefs)
                        st.markdown("""<div style='background:#0f3a2a; border:1px solid #22d3a5;
                            border-radius:8px; padding:14px 16px; margin:12px 0;'>
                            <div style='font-family: JetBrains Mono, monospace; font-size:12px; color:#22d3a5;'>
                                ✓ AI AUTO-FILLED YOUR JOB PREFERENCES
                            </div>
                            <div style='font-size:12px; color:#5a7090; margin-top:6px;'>
                                Target roles, skills, and location have been updated from your resume.
                                Check the "Job Preferences" tab to review and adjust.
                            </div>
                        </div>""", unsafe_allow_html=True)

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Experience", f"{parsed.get('experience_years', '?')} yrs")
                        col2.metric("Skills found", len(parsed.get('keywords', [])))
                        col3.metric("Target roles", len(parsed.get('target_roles', [])))
                else:
                    save_prefs(prefs)
                    st.info("💡 Add a Groq API key in Settings to auto-fill job preferences from your resume.")

                with st.expander("Preview extracted text"):
                    st.text(text[:1200] + "..." if len(text) > 1200 else text)
            else:
                st.warning("Could not extract text from PDF.")

        if prefs.get("resume_text"):
            st.markdown(f"""<div style='background:#111827; border:1px solid #1e2d4a; border-radius:8px; padding:12px 16px;'>
                <div style='font-family: JetBrains Mono, monospace; font-size:11px; color:#22d3a5;'>✓ RESUME LOADED</div>
                <div style='color:#5a7090; font-size:12px; margin-top:4px;'>{prefs.get("resume_path","uploaded")} · {len(prefs["resume_text"].split())} words</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-header">PERSONAL INFO</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            prefs["name"] = st.text_input("Full name", value=prefs.get("name", ""))
            prefs["email"] = st.text_input("Email", value=prefs.get("email", ""))
        with c2:
            prefs["phone"] = st.text_input("Phone", value=prefs.get("phone", ""))
            prefs["experience_years"] = st.number_input("Years of experience",
                value=prefs.get("experience_years", 6), min_value=0, max_value=40)

    with tab2:
        st.markdown('<div class="section-header">TARGET ROLES</div>', unsafe_allow_html=True)
        roles_str = st.text_area("Target job titles (one per line)",
            value="\n".join(prefs.get("target_roles", [])), height=100)
        prefs["target_roles"] = [r.strip() for r in roles_str.splitlines() if r.strip()]

        c1, c2 = st.columns(2)
        with c1:
            prefs["min_salary_lpa"] = st.number_input("Min salary (LPA)",
                value=prefs.get("min_salary_lpa", 15), min_value=0)
        with c2:
            prefs["max_salary_lpa"] = st.number_input("Max salary (LPA)",
                value=prefs.get("max_salary_lpa", 30), min_value=0)

        st.markdown('<div class="section-header">LOCATIONS</div>', unsafe_allow_html=True)
        loc_str = st.text_area("Preferred locations (one per line)",
            value="\n".join(prefs.get("locations", [])), height=80)
        prefs["locations"] = [l.strip() for l in loc_str.splitlines() if l.strip()]

        st.markdown('<div class="section-header">KEYWORDS</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            kw_str = st.text_area("Must-have keywords (one per line)",
                value="\n".join(prefs.get("keywords", [])), height=120)
            prefs["keywords"] = [k.strip() for k in kw_str.splitlines() if k.strip()]
        with c2:
            exc_str = st.text_area("Exclude if JD contains (one per line)",
                value="\n".join(prefs.get("exclude_keywords", [])), height=120)
            prefs["exclude_keywords"] = [k.strip() for k in exc_str.splitlines() if k.strip()]

    with tab3:
        st.markdown('<div class="section-header">COVER LETTER TEMPLATE</div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#5a7090; font-size:13px;">The AI personalises this for each job. Use {COMPANY} and {ROLE} as placeholders.</p>',
            unsafe_allow_html=True)
        prefs["cover_letter_template"] = st.text_area(
            "Template / style guide",
            value=prefs.get("cover_letter_template", DEFAULT_TEMPLATE),
            height=280
        )

    if st.button("💾  Save Preferences"):
        save_prefs(prefs)
        st.success("✓ Preferences saved")


DEFAULT_TEMPLATE = """Dear Hiring Manager,

With {experience_years}+ years in FP&A and supply chain finance across FMCG portfolios, I bring a data-driven approach to financial planning that directly supports commercial and operational decision-making.

At IBM (supporting Reckitt's MENARP & Africa portfolio), I manage a £60M supply chain P&L — driving period-close accuracy, variance analysis, and Finance Director-level reporting.

For the {ROLE} role at {COMPANY}, I bring hands-on FP&A expertise including budgeting, forecasting, and variance analysis.

Best regards,
Jitendra Parida
"""
