import streamlit as st
from core.store import get_settings, save_settings, get_prefs


def render():
    settings = get_settings()
    prefs    = get_prefs()

    st.markdown("""<div style='padding: 8px 0 28px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 10px; color: #2d4060; letter-spacing: 0.2em;'>CONFIGURATION</div>
        <h1 style='font-size: 30px; font-weight: 800; margin: 4px 0 6px; color: #e2e8f0;'>Settings</h1>
        <p style='color: #4a6080; font-size: 14px; margin: 0;'>Configure your API keys, portal credentials, and automation preferences.</p>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🔑 API Keys", "🌐 Job Portals", "⚙️ Automation", "💳 Plan"])

    with tab1:
        st.markdown('<div class="section-header">AI ENGINE</div>', unsafe_allow_html=True)
        groq_key = st.text_input(
            "Groq API Key",
            value=settings.get("groq_api_key", ""),
            type="password",
            help="Powers Career Intelligence, Resume Optimizer, and all AI generation. Free at console.groq.com"
        )
        st.caption("Get your free key at [console.groq.com](https://console.groq.com) — no credit card required.")

        st.markdown('<div class="section-header">JOB SEARCH API</div>', unsafe_allow_html=True)
        jsearch_key = st.text_input(
            "JSearch API Key (RapidAPI)",
            value=settings.get("jsearch_api_key", ""),
            type="password",
            help="Enables Job Discovery from LinkedIn, Indeed, Glassdoor via API."
        )
        st.caption("Get key at [rapidapi.com/jsearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch).")

        if st.button("💾 Save API Keys", use_container_width=True):
            settings["groq_api_key"]    = groq_key
            settings["jsearch_api_key"] = jsearch_key
            save_settings(settings)
            st.success("✓ API keys saved")

        if groq_key:
            st.markdown("""<div class="insight-card success">
                <div style='font-size:13px; color:#22d3a5; font-weight:600;'>✓ AI Engine Active</div>
                <div style='font-size:12px; color:#7a8faa; margin-top:4px;'>Career Intelligence, Resume Optimizer, Application Engine, and AI Coach are all powered on.</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="insight-card warning">
                <div style='font-size:13px; color:#fbbf24; font-weight:600;'>⚠️ AI Engine Offline</div>
                <div style='font-size:12px; color:#7a8faa; margin-top:4px;'>Add your Groq API key to unlock Career Intelligence, ATS scoring, and personalized content generation.</div>
            </div>""", unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="section-header">PORTAL CREDENTIALS</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Naukri**")
            naukri_email = st.text_input("Naukri Email", value=settings.get("naukri_email", ""), key="naukri_email")
            naukri_pass  = st.text_input("Naukri Password", value=settings.get("naukri_password", ""), type="password", key="naukri_pass")
        with c2:
            st.markdown("**LinkedIn**")
            li_email = st.text_input("LinkedIn Email", value=settings.get("linkedin_email", ""), key="li_email")
            li_pass  = st.text_input("LinkedIn Password", value=settings.get("linkedin_password", ""), type="password", key="li_pass")

        st.markdown('<div class="section-header">ACTIVE PORTALS</div>', unsafe_allow_html=True)
        portal_options = ["naukri", "linkedin", "instahyre", "foundit", "wellfound", "remotive", "internshala"]
        active_portals = st.multiselect(
            "Portals to search",
            portal_options,
            default=settings.get("portals", ["naukri", "linkedin"])
        )

        if st.button("💾 Save Portal Settings", use_container_width=True):
            settings.update({
                "naukri_email": naukri_email, "naukri_password": naukri_pass,
                "linkedin_email": li_email,   "linkedin_password": li_pass,
                "portals": active_portals,
            })
            save_settings(settings)
            st.success("✓ Portal settings saved")

    with tab3:
        st.markdown('<div class="section-header">AUTO-APPLY CONTROLS</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            min_match    = st.slider("Minimum match score to auto-apply (%)", 50, 95,
                                     value=settings.get("min_match_score", 70), step=5)
            daily_limit  = st.number_input("Daily application limit", min_value=1, max_value=100,
                                            value=settings.get("daily_apply_limit", 30))
        with c2:
            auto_apply   = st.toggle("Enable Auto-Apply", value=settings.get("auto_apply_enabled", False))
            headless     = st.toggle("Headless browser mode", value=settings.get("headless_browser", True))

        st.markdown("""<div class="insight-card warning" style='margin-top:12px;'>
            <div style='font-size:13px; color:#fbbf24; font-weight:600;'>⚠️ Auto-Apply Safety Guidelines</div>
            <div style='font-size:12px; color:#7a8faa; margin-top:4px;'>Set a high match threshold (≥75%) before enabling auto-apply. Always review applications in the Tracker. Portals may flag rapid automated submissions.</div>
        </div>""", unsafe_allow_html=True)

        if st.button("💾 Save Automation Settings", use_container_width=True):
            settings.update({
                "min_match_score":    min_match,
                "daily_apply_limit":  daily_limit,
                "auto_apply_enabled": auto_apply,
                "headless_browser":   headless,
            })
            save_settings(settings)
            st.success("✓ Automation settings saved")

    with tab4:
        tier = settings.get("tier", "free")
        if tier == "pro":
            st.markdown("""<div style='background:linear-gradient(135deg,#052e16,#0f2d1a); border:1px solid #166534; border-radius:12px; padding:24px; text-align:center; margin-bottom:20px;'>
                <div style='font-size:24px; font-weight:800; color:#22d3a5; margin-bottom:6px;'>✓ CareerOS Pro</div>
                <div style='font-size:14px; color:#7a8faa;'>All modules active. Full AI intelligence unlocked.</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="upgrade-banner">
                <div style='font-size:22px; font-weight:800; color:#e2e8f0; margin-bottom:6px;'>Upgrade to CareerOS Pro</div>
                <div style='font-size:14px; color:#a5b4fc; margin-bottom:16px;'>Unlock full AI Career Intelligence, unlimited applications, and priority coaching.</div>
                <div style='display:flex; justify-content:center; gap:30px; margin-bottom:16px;'>
                    <div style='text-align:center;'><div style='font-size:13px; color:#22d3a5;'>✓</div><div style='font-size:12px; color:#7a8faa;'>Career Intelligence</div></div>
                    <div style='text-align:center;'><div style='font-size:13px; color:#22d3a5;'>✓</div><div style='font-size:12px; color:#7a8faa;'>Resume Optimizer</div></div>
                    <div style='text-align:center;'><div style='font-size:13px; color:#22d3a5;'>✓</div><div style='font-size:12px; color:#7a8faa;'>AI Coach Chat</div></div>
                    <div style='text-align:center;'><div style='font-size:13px; color:#22d3a5;'>✓</div><div style='font-size:12px; color:#7a8faa;'>Application Engine</div></div>
                </div>
                <div style='font-size:28px; font-weight:800; color:#e2e8f0; margin-bottom:4px;'>₹499<span style="font-size:14px; color:#7a8faa;">/month</span></div>
            </div>""", unsafe_allow_html=True)
            st.link_button("🚀 Unlock CareerOS Pro — ₹499/month", "https://rzp.io/rzp/StnjPRq", use_container_width=True)

        st.markdown('<div class="section-header">FREE VS PRO</div>', unsafe_allow_html=True)
        features = [
            ("Job Discovery & Scraping",         True,  True),
            ("AI Job Matching (basic)",           True,  True),
            ("Resume Upload & Parsing",           True,  True),
            ("Application Tracker",               True,  True),
            ("Career Intelligence (5 paths)",     False, True),
            ("Resume ATS Optimizer",              False, True),
            ("Application Engine (4 formats)",    False, True),
            ("AI Career Coach",                   False, True),
            ("Coach Chat (unlimited)",            False, True),
            ("Resume Rewriter (AI)",              False, True),
            ("Auto-Apply Automation",             False, True),
            ("Full Application Package Download", False, True),
        ]
        header = f"""<div style='display:grid; grid-template-columns:2fr 1fr 1fr; gap:0; background:#0c1020; border:1px solid #1a2540; border-radius:10px; overflow:hidden;'>
        <div style='padding:10px 14px; font-size:11px; color:#4a6080; font-family:JetBrains Mono,monospace; border-bottom:1px solid #1a2540;'>FEATURE</div>
        <div style='padding:10px 14px; font-size:11px; color:#4a6080; font-family:JetBrains Mono,monospace; text-align:center; border-bottom:1px solid #1a2540;'>FREE</div>
        <div style='padding:10px 14px; font-size:11px; color:#6366f1; font-family:JetBrains Mono,monospace; text-align:center; border-bottom:1px solid #1a2540;'>PRO</div>"""
        rows = ""
        for name, free, pro in features:
            rows += f"""
        <div style='padding:9px 14px; font-size:12px; color:#e2e8f0; border-bottom:1px solid #1a2540;'>{name}</div>
        <div style='padding:9px 14px; text-align:center; border-bottom:1px solid #1a2540; color:{"#22d3a5" if free else "#2d4060"};'>{"✓" if free else "—"}</div>
        <div style='padding:9px 14px; text-align:center; border-bottom:1px solid #1a2540; color:#22d3a5;'>✓</div>"""
        st.markdown(header + rows + "</div>", unsafe_allow_html=True)
