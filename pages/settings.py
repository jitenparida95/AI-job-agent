import streamlit as st
from core.store import get_settings, save_settings

RAZORPAY_LINK = "https://rzp.io/rzp/StnjPRq"


def render():
    settings = get_settings()

    st.markdown("""<div style='padding: 8px 0 24px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 11px; color: #3d5a80; letter-spacing: 0.1em;'>CONFIG</div>
        <h1 style='font-size: 28px; margin: 4px 0 0; color: #e8eaf0;'>Settings</h1>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🔐 Job Portals", "⚙️ Agent Config", "🔧 Browser", "🤖 AI Resume Update"])

    # ── TAB 1: Job Portal Credentials only (no API keys shown to user) ──
    with tab1:
        st.markdown('<div class="section-header">NAUKRI.COM LOGIN</div>', unsafe_allow_html=True)
        st.caption("Your credentials are stored locally and never shared.")
        c1, c2 = st.columns(2)
        with c1:
            settings["naukri_email"] = st.text_input("Naukri email", value=settings.get("naukri_email", ""))
        with c2:
            settings["naukri_password"] = st.text_input("Naukri password", value=settings.get("naukri_password", ""), type="password")

        st.markdown('<div class="section-header">LINKEDIN LOGIN</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            settings["linkedin_email"] = st.text_input("LinkedIn email", value=settings.get("linkedin_email", ""))
        with c2:
            settings["linkedin_password"] = st.text_input("LinkedIn password", value=settings.get("linkedin_password", ""), type="password")

        st.markdown("""<div style='background:#1a1000; border:1px solid #f59e0b33; border-radius:8px; padding:12px 16px; margin-top:8px;'>
            <div style='color:#f59e0b; font-size:11px; font-family: JetBrains Mono, monospace;'>⚠ CREDENTIALS STORED LOCALLY</div>
            <div style='color:#8a6a30; font-size:12px; margin-top:4px;'>Saved to ~/.jobagent/settings.json on your machine only. Never uploaded or shared.</div>
        </div>""", unsafe_allow_html=True)

        # Subscription / upgrade section
        st.markdown('<div class="section-header">SUBSCRIPTION</div>', unsafe_allow_html=True)
        sub = st.session_state.get("subscription")
        if sub and sub.get("status") == "trial":
            from auth import days_left
            d = days_left(sub)
            st.markdown(f"""<div style='background:#111827; border:1px solid #22d3a5; border-radius:8px; padding:16px; margin-bottom:12px;'>
                <div style='font-family: JetBrains Mono, monospace; font-size:13px; color:#22d3a5;'>🎁 FREE TRIAL — {d} day{"s" if d!=1 else ""} left</div>
                <div style='font-size:12px; color:#5a7090; margin-top:6px;'>Upgrade to Pro for ₹49/month to keep full access after your trial ends.</div>
            </div>""", unsafe_allow_html=True)
            st.link_button("⚡ Upgrade to Pro — ₹49/month", RAZORPAY_LINK)
        elif sub and sub.get("status") == "active":
            st.success("✓ Pro plan active")
        else:
            st.link_button("⚡ Subscribe — ₹49/month", RAZORPAY_LINK)

    # ── TAB 2: Agent Config ──
    with tab2:
        st.markdown('<div class="section-header">MATCHING</div>', unsafe_allow_html=True)
        settings["min_match_score"] = st.slider(
            "Minimum match score to apply (%)", 40, 95,
            value=settings.get("min_match_score", 70), step=5,
        )

        st.markdown('<div class="section-header">APPLY LIMITS</div>', unsafe_allow_html=True)
        settings["daily_apply_limit"] = st.number_input(
            "Max applications per day", value=settings.get("daily_apply_limit", 30),
            min_value=1, max_value=100,
        )

        st.markdown('<div class="section-header">PORTALS TO SEARCH</div>', unsafe_allow_html=True)
        all_portals = ["naukri", "linkedin", "instahyre", "foundit", "wellfound", "remotive"]
        current = settings.get("portals", all_portals)
        selected = []
        cols = st.columns(3)
        for i, p in enumerate(all_portals):
            with cols[i % 3]:
                if st.checkbox(p.capitalize(), value=p in current, key=f"sett_portal_{p}"):
                    selected.append(p)
        settings["portals"] = selected

        st.markdown('<div class="section-header">AUTO-APPLY</div>', unsafe_allow_html=True)
        settings["auto_apply_enabled"] = st.toggle(
            "Enable fully automated apply",
            value=settings.get("auto_apply_enabled", False),
        )

    # ── TAB 3: Browser ──
    with tab3:
        st.markdown('<div class="section-header">SELENIUM BROWSER</div>', unsafe_allow_html=True)
        settings["headless_browser"] = st.toggle(
            "Run browser headless (invisible)",
            value=settings.get("headless_browser", True),
        )
        st.caption("Turn OFF to watch the browser and solve CAPTCHAs manually on first run.")

    # ── TAB 4: AI Resume Update ──
    with tab4:
        st.markdown('<div class="section-header">AI-POWERED RESUME UPDATER</div>', unsafe_allow_html=True)
        st.markdown("""<p style='color:#5a7090; font-size:13px; margin-bottom:16px;'>
            Paste a job description and let AI rewrite your resume summary and skills section
            to better match the role — without changing your actual experience.
        </p>""", unsafe_allow_html=True)

        from core.store import get_prefs, save_prefs
        prefs = get_prefs()

        groq_key = settings.get("groq_api_key", "") or st.secrets.get("GROQ_API_KEY", "")

        if not groq_key:
            st.warning("⚠️ No Groq API key configured. Contact support or add GROQ_API_KEY to secrets.")
        else:
            jd_input = st.text_area(
                "Paste the Job Description here",
                height=200,
                placeholder="Paste the full job description of the role you want to tailor your resume for..."
            )

            current_resume = prefs.get("resume_text", "")
            if current_resume:
                st.markdown(f"""<div style='background:#111827; border:1px solid #1e2d4a; border-radius:6px;
                    padding:10px 14px; font-size:12px; color:#5a7090; margin-bottom:12px;'>
                    📄 Current resume: <span style='color:#22d3a5;'>{prefs.get("resume_path","uploaded")} · {len(current_resume.split())} words</span>
                </div>""", unsafe_allow_html=True)
            else:
                st.warning("No resume loaded yet. Go to Resume & Prefs to upload your PDF first.")

            col1, col2 = st.columns(2)
            with col1:
                update_summary = st.checkbox("Rewrite professional summary", value=True)
            with col2:
                update_skills = st.checkbox("Optimize skills/keywords section", value=True)

            if st.button("🤖 Generate AI-Optimized Resume Section", disabled=not jd_input or not current_resume):
                with st.spinner("AI is tailoring your resume to the job description..."):
                    result = _ai_resume_update(
                        resume_text=current_resume,
                        jd_text=jd_input,
                        prefs=prefs,
                        groq_key=groq_key,
                        update_summary=update_summary,
                        update_skills=update_skills,
                    )

                if result.get("success"):
                    st.markdown('<div class="section-header">AI-GENERATED CONTENT</div>', unsafe_allow_html=True)

                    if result.get("summary"):
                        st.markdown("**✨ Optimized Professional Summary**")
                        summary_val = st.text_area("", value=result["summary"], height=150, key="ai_summary")
                        if st.button("✓ Apply this summary to my profile"):
                            prefs["ai_summary"] = summary_val
                            prefs["cover_letter_template"] = summary_val + "\n\n" + prefs.get("cover_letter_template", "")
                            save_prefs(prefs)
                            st.success("Summary saved to your profile!")

                    if result.get("keywords"):
                        st.markdown("**🎯 Recommended Keywords to Add**")
                        st.markdown(f"""<div style='background:#0f3a2a; border:1px solid #22d3a5; border-radius:8px;
                            padding:12px 16px; font-family: JetBrains Mono, monospace; font-size:12px; color:#22d3a5;'>
                            {" · ".join(result["keywords"])}
                        </div>""", unsafe_allow_html=True)
                        if st.button("✓ Add these keywords to my profile"):
                            existing = prefs.get("keywords", [])
                            new_kws = [k for k in result["keywords"] if k not in existing]
                            prefs["keywords"] = existing + new_kws
                            save_prefs(prefs)
                            st.success(f"Added {len(new_kws)} new keywords!")

                    if result.get("match_tips"):
                        st.markdown("**💡 Tips to improve your match score**")
                        for tip in result["match_tips"]:
                            st.markdown(f"- {tip}")
                else:
                    st.error(f"AI update failed: {result.get('error')}")

    if st.button("💾  Save Settings"):
        save_settings(settings)
        st.success("✓ Settings saved")


def _ai_resume_update(resume_text, jd_text, prefs, groq_key, update_summary=True, update_skills=True):
    """Call Groq to generate optimized resume sections."""
    import json, urllib.request
    prompt = f"""You are an expert resume writer and ATS optimization specialist.

CANDIDATE'S CURRENT RESUME:
{resume_text[:2000]}

JOB DESCRIPTION:
{jd_text[:1500]}

CANDIDATE NAME: {prefs.get('name', '')}
EXPERIENCE: {prefs.get('experience_years', '')} years

Tasks:
{"1. Write an optimized 3-4 sentence professional summary that aligns with this JD while staying true to the candidate's actual experience." if update_summary else ""}
{"2. Extract 10-15 ATS keywords from the JD that the candidate should include in their resume (only ones relevant to their background)." if update_skills else ""}
3. Give 3 specific tips to improve match score for this role.

Respond ONLY with valid JSON, no markdown backticks:
{{
  "summary": "...",
  "keywords": ["kw1", "kw2", ...],
  "match_tips": ["tip1", "tip2", "tip3"]
}}"""

    try:
        payload = json.dumps({
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.3,
        }).encode()
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = json.loads(r.read())["choices"][0]["message"]["content"]
        raw = raw.strip().strip("```json").strip("```").strip()
        data = json.loads(raw)
        return {"success": True, **data}
    except Exception as e:
        return {"success": False, "error": str(e)}
