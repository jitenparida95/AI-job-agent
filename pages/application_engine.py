import streamlit as st
from core.store import get_prefs, get_settings, get_jobs
from core.ai_engine import generate_application_content


def render():
    prefs = get_prefs()
    settings = get_settings()
    api_key = settings.get("groq_api_key", "") or ""
    jobs = get_jobs()
    scored_jobs = sorted(
        [j for j in jobs if j.get("match_score") is not None],
        key=lambda x: x.get("match_score", 0), reverse=True
    )

    st.markdown("""<div style='padding: 8px 0 28px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 10px; color: #2d4060; letter-spacing: 0.2em;'>MODULE 4</div>
        <h1 style='font-size: 30px; font-weight: 800; margin: 4px 0 6px; color: #e2e8f0;'>Application Engine</h1>
        <p style='color: #4a6080; font-size: 14px; margin: 0;'>Generate personalized cover letters, cold emails, referral messages, and LinkedIn DMs — instantly.</p>
    </div>""", unsafe_allow_html=True)

    if not api_key:
        st.markdown("""<div class="upgrade-banner">
            <div style='font-size: 16px; font-weight: 700; color: #e2e8f0; margin-bottom: 6px;'>🔒 AI Generation Requires Groq API Key</div>
            <div style='font-size: 13px; color: #a5b4fc; margin-bottom: 14px;'>Add your free Groq API key in Settings to generate personalized application content.</div>
            <div style='font-size: 12px; color: #6366f1;'>Get your free key at console.groq.com → Settings → Add API Key</div>
        </div>""", unsafe_allow_html=True)

    # ── Job selector ────────────────────────────────────────
    st.markdown('<div class="section-header">SELECT TARGET JOB</div>', unsafe_allow_html=True)

    use_custom = st.checkbox("Enter job details manually (no job in pipeline)", value=len(scored_jobs) == 0)

    if use_custom or not scored_jobs:
        c1, c2 = st.columns(2)
        with c1:
            job_title = st.text_input("Job Title", placeholder="e.g. Senior FP&A Manager")
            company = st.text_input("Company Name", placeholder="e.g. Unilever India")
        with c2:
            location = st.text_input("Location", placeholder="e.g. Bangalore")
            salary = st.text_input("Salary Range", placeholder="e.g. 20-28 LPA")
        jd = st.text_area("Job Description (paste here)", height=120, placeholder="Paste the job description for better personalization...")
        selected_job = {
            "title": job_title, "company": company, "location": location,
            "salary": salary, "description": jd, "portal": "manual"
        }
    else:
        job_options = {f"{j.get('title','')} @ {j.get('company','')} ({j.get('match_score',0)}% match)": j for j in scored_jobs[:20]}
        selected_label = st.selectbox("Choose from your matched jobs", list(job_options.keys()))
        selected_job = job_options[selected_label]
        st.markdown(f"""<div class="job-card">
            <div class="job-title">{selected_job.get('title','')} @ <span style='color:#6366f1;'>{selected_job.get('company','')}</span></div>
            <div class="job-meta">{selected_job.get('location','—')} · {selected_job.get('salary','Salary not listed')} · {selected_job.get('portal','').upper()}</div>
        </div>""", unsafe_allow_html=True)

    # ── Content type selector ───────────────────────────────
    st.markdown('<div class="section-header">SELECT CONTENT TO GENERATE</div>', unsafe_allow_html=True)

    content_types = {
        "📝 Cover Letter": "cover_letter",
        "✉️ Cold Email": "cold_email",
        "🤝 Referral Message": "referral_message",
        "💼 LinkedIn DM": "linkedin_dm",
    }

    col_tabs = st.columns(len(content_types))
    selected_type_label = st.session_state.get("app_engine_type", "📝 Cover Letter")

    for col, (label, key) in zip(col_tabs, content_types.items()):
        with col:
            active = selected_type_label == label
            bg = "#1e1b4b" if active else "#0c1020"
            border = "#6366f1" if active else "#1a2540"
            if st.button(label, use_container_width=True, key=f"type_{key}"):
                st.session_state["app_engine_type"] = label
                st.rerun()

    content_key = content_types.get(selected_type_label, "cover_letter")

    # ── Generate ────────────────────────────────────────────
    st.markdown('<div class="section-header">GENERATED CONTENT</div>', unsafe_allow_html=True)

    cache_key = f"app_content_{content_key}_{selected_job.get('title','')}_{selected_job.get('company','')}"

    if st.button(f"⚡ Generate {selected_type_label}", use_container_width=True):
        if not selected_job.get("title") or not selected_job.get("company"):
            st.error("Please select or enter a job first.")
        else:
            with st.spinner("Generating personalized content..."):
                content = generate_application_content(selected_job, prefs, content_key, api_key)
            st.session_state[cache_key] = content

    result = st.session_state.get(cache_key, "")
    if result:
        st.markdown(f"""<div style='background:#060912; border:1px solid #1a2540; border-radius:10px; padding:20px; font-size:13px; color:#e2e8f0; line-height:1.8; white-space:pre-wrap; font-family: Inter, sans-serif;'>{result}</div>""", unsafe_allow_html=True)
        st.code(result, language=None)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Regenerate", use_container_width=True):
                if cache_key in st.session_state:
                    del st.session_state[cache_key]
                st.rerun()
        with col2:
            st.download_button(
                "⬇️ Download as TXT",
                data=result,
                file_name=f"{content_key}_{selected_job.get('company','')}.txt",
                use_container_width=True
            )
    else:
        st.markdown("""<div style='text-align:center; padding: 48px; background: #0c1020; border: 1px dashed #1a2540; border-radius: 12px;'>
            <div style='font-size: 28px; margin-bottom: 12px;'>✉️</div>
            <div style='font-size: 13px; color: #4a6080;'>Select a job and click Generate to create your personalized content.</div>
        </div>""", unsafe_allow_html=True)

    # ── All-in-one package ──────────────────────────────────
    if not api_key:
        return

    st.markdown('<div class="section-header">FULL APPLICATION PACKAGE</div>', unsafe_allow_html=True)
    if st.button("🚀 Generate Complete Application Package (All 4 formats)", use_container_width=True):
        if not selected_job.get("title"):
            st.error("Select a job first.")
        else:
            all_content = {}
            prog = st.progress(0)
            for i, (label, key) in enumerate(content_types.items()):
                with st.spinner(f"Generating {label}..."):
                    all_content[label] = generate_application_content(selected_job, prefs, key, api_key)
                prog.progress(int((i + 1) / len(content_types) * 100))

            package_text = f"APPLICATION PACKAGE\n{'='*50}\n"
            package_text += f"Role: {selected_job.get('title')} at {selected_job.get('company')}\n"
            package_text += f"Generated by CareerOS\n{'='*50}\n\n"
            for label, content in all_content.items():
                package_text += f"\n{label.upper()}\n{'-'*40}\n{content}\n"

            st.session_state["full_package"] = package_text
            st.success("✓ Complete application package ready!")

    if st.session_state.get("full_package"):
        st.download_button(
            "⬇️ Download Full Application Package",
            data=st.session_state["full_package"],
            file_name=f"application_package_{selected_job.get('company','')}.txt",
            use_container_width=True
        )
