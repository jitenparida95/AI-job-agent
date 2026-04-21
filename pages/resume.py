import streamlit as st
from core.store import get_prefs, save_prefs
import re


def extract_text_from_pdf(uploaded_file) -> str:
    try:
        import fitz  # PyMuPDF
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


def render():
    prefs = get_prefs()

    st.markdown("""<div style='padding: 8px 0 24px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 11px; color: #3d5a80; letter-spacing: 0.1em;'>CONFIGURATION</div>
        <h1 style='font-size: 28px; margin: 4px 0 0; color: #e8eaf0;'>Resume & Preferences</h1>
        <p style='color: #5a7090; font-size: 14px; margin: 4px 0 0;'>The agent uses this to score job matches and personalise applications.</p>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📄 Resume", "🎯 Job Preferences", "✉️ Cover Letter"])

    with tab1:
        st.markdown('<div class="section-header">UPLOAD RESUME</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload your resume (PDF)", type=["pdf"], help="PDF preferred for accurate text extraction")
        if uploaded:
            text = extract_text_from_pdf(uploaded)
            if text:
                prefs["resume_text"] = text
                prefs["resume_path"] = uploaded.name
                st.success(f"✓ Extracted {len(text.split())} words from resume")
                with st.expander("Preview extracted text"):
                    st.text(text[:1200] + "..." if len(text) > 1200 else text)
            else:
                st.warning("Could not extract text. Install: pip install PyMuPDF")

        if prefs.get("resume_text"):
            st.markdown(f"""<div style='background:#111827; border:1px solid #1e2d4a; border-radius:8px; padding:12px 16px;'>
                <div style='font-family: JetBrains Mono, monospace; font-size:11px; color:#22d3a5;'>✓ RESUME LOADED</div>
                <div style='color:#5a7090; font-size:12px; margin-top:4px;'>{prefs.get("resume_path","uploaded")} · {len(prefs["resume_text"].split())} words</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-header">PERSONAL INFO</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            prefs["name"] = st.text_input("Full name", value=prefs.get("name",""))
            prefs["email"] = st.text_input("Email", value=prefs.get("email",""))
        with c2:
            prefs["phone"] = st.text_input("Phone", value=prefs.get("phone",""))
            prefs["experience_years"] = st.number_input("Years of experience", value=prefs.get("experience_years", 6), min_value=0, max_value=40)

    with tab2:
        st.markdown('<div class="section-header">TARGET ROLES</div>', unsafe_allow_html=True)
        roles_str = st.text_area("Target job titles (one per line)",
            value="\n".join(prefs.get("target_roles",[])), height=100)
        prefs["target_roles"] = [r.strip() for r in roles_str.splitlines() if r.strip()]

        c1, c2 = st.columns(2)
        with c1:
            prefs["min_salary_lpa"] = st.number_input("Min salary (LPA)", value=prefs.get("min_salary_lpa", 15), min_value=0)
        with c2:
            prefs["max_salary_lpa"] = st.number_input("Max salary (LPA)", value=prefs.get("max_salary_lpa", 30), min_value=0)

        st.markdown('<div class="section-header">LOCATIONS</div>', unsafe_allow_html=True)
        loc_str = st.text_area("Preferred locations (one per line)",
            value="\n".join(prefs.get("locations",[])), height=80)
        prefs["locations"] = [l.strip() for l in loc_str.splitlines() if l.strip()]

        st.markdown('<div class="section-header">KEYWORDS</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            kw_str = st.text_area("Must-have keywords (one per line)",
                value="\n".join(prefs.get("keywords",[])), height=120)
            prefs["keywords"] = [k.strip() for k in kw_str.splitlines() if k.strip()]
        with c2:
            exc_str = st.text_area("Exclude if JD contains (one per line)",
                value="\n".join(prefs.get("exclude_keywords",[])), height=120)
            prefs["exclude_keywords"] = [k.strip() for k in exc_str.splitlines() if k.strip()]

    with tab3:
        st.markdown('<div class="section-header">COVER LETTER TEMPLATE</div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#5a7090; font-size:13px;">The AI will personalise this template for each job. Use {COMPANY} and {ROLE} as placeholders.</p>', unsafe_allow_html=True)
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

At IBM (supporting Reckitt's MENARP & Africa portfolio), I manage a £60M supply chain P&L — driving period-close accuracy, variance analysis, and Finance Director-level reporting. Prior to this, at Capgemini supporting Unilever ANZ/APAC, I built automated MIS frameworks that reduced reporting time by 40%.

For the {ROLE} role at {COMPANY}, I bring:
• Hands-on FP&A: budgeting, forecasting, actuals vs. plan variance
• Supply chain finance: standard costing, working capital, DIO/DSO analysis
• Tech stack: SAP, Power BI, Excel (advanced), Sunrise ERP

I'd welcome the opportunity to discuss how I can add immediate value.

Best regards,
Jitendra Parida
"""
