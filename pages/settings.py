import streamlit as st
from core.store import get_settings, save_settings


def render():
    settings = get_settings()

    st.markdown("""<div style='padding: 8px 0 24px;'>
        <div style='font-family: JetBrains Mono, monospace; font-size: 11px; color: #3d5a80; letter-spacing: 0.1em;'>CONFIG</div>
        <h1 style='font-size: 28px; margin: 4px 0 0; color: #e8eaf0;'>Settings</h1>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔑 API & Credentials", "⚙️ Agent Config", "🔧 Browser"])

    with tab1:
        st.markdown('<div class="section-header">AI API — FOR MATCHING & COVER LETTERS</div>', unsafe_allow_html=True)
        settings["groq_api_key"] = st.text_input(
            "Groq API key", value=settings.get("groq_api_key",""), type="password",
            help="Free at console.groq.com — used for AI job matching and cover letter generation"
        )
        st.markdown("""<div style='background:#0d1a10; border:1px solid #1a4a25; border-radius:8px; padding:12px 16px; margin-bottom:16px;'>
            <div style='color:#22d3a5; font-size:12px; font-family: JetBrains Mono, monospace;'>FREE · No credit card required</div>
            <div style='color:#5a7090; font-size:12px; margin-top:4px;'>Groq's free tier gives ~14,400 requests/day on Llama 3.1 8B — more than enough for daily job scanning.</div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-header">JSEARCH API — FOR JOB DISCOVERY (RECOMMENDED)</div>', unsafe_allow_html=True)
        settings["jsearch_api_key"] = st.text_input(
            "JSearch RapidAPI key", value=settings.get("jsearch_api_key",""), type="password",
            help="Free 200 calls/month. Get it at rapidapi.com — search JSearch by letscrape"
        )
        st.markdown("""<div style='background:#0d1020; border:1px solid #1a2a4a; border-radius:8px; padding:12px 16px; margin-bottom:16px;'>
            <div style='color:#60a5fa; font-size:12px; font-family: JetBrains Mono, monospace;'>⚡ PULLS FROM: LinkedIn · Naukri · Indeed · Glassdoor · ZipRecruiter</div>
            <div style='color:#5a7090; font-size:12px; margin-top:4px;'>
                1. Go to <b>rapidapi.com</b> → Sign up free<br>
                2. Search <b>"JSearch"</b> → Subscribe to Basic (free, 200 calls/month)<br>
                3. Copy your API key and paste above<br>
                This gives the best job results across all portals in one call.
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-header">NAUKRI.COM</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            settings["naukri_email"] = st.text_input("Naukri email", value=settings.get("naukri_email",""))
        with c2:
            settings["naukri_password"] = st.text_input("Naukri password", value=settings.get("naukri_password",""), type="password")

        st.markdown('<div class="section-header">LINKEDIN</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            settings["linkedin_email"] = st.text_input("LinkedIn email", value=settings.get("linkedin_email",""))
        with c2:
            settings["linkedin_password"] = st.text_input("LinkedIn password", value=settings.get("linkedin_password",""), type="password")

        st.markdown("""<div style='background:#1a1000; border:1px solid #f59e0b33; border-radius:8px; padding:12px 16px; margin-top:8px;'>
            <div style='color:#f59e0b; font-size:11px; font-family: JetBrains Mono, monospace;'>⚠ CREDENTIALS STORED LOCALLY</div>
            <div style='color:#8a6a30; font-size:12px; margin-top:4px;'>Credentials are saved to ~/.jobagent/settings.json on your machine only. Never shared or uploaded.</div>
        </div>""", unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="section-header">MATCHING</div>', unsafe_allow_html=True)
        settings["min_match_score"] = st.slider(
            "Minimum match score to apply (%)", 40, 95,
            value=settings.get("min_match_score", 70), step=5,
            help="Jobs below this score will be skipped"
        )

        st.markdown('<div class="section-header">APPLY LIMITS</div>', unsafe_allow_html=True)
        settings["daily_apply_limit"] = st.number_input(
            "Max applications per day", value=settings.get("daily_apply_limit", 30),
            min_value=1, max_value=100,
            help="Naukri allows ~50/day. LinkedIn may throttle beyond 20-25."
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
            help="When ON, the agent will apply without human review"
        )

    with tab3:
        st.markdown('<div class="section-header">SELENIUM BROWSER</div>', unsafe_allow_html=True)
        settings["headless_browser"] = st.toggle(
            "Run browser headless (invisible)",
            value=settings.get("headless_browser", True),
            help="Turn OFF to watch the browser and solve CAPTCHAs manually"
        )

        st.markdown('<div class="section-header">INSTALLATION</div>', unsafe_allow_html=True)
        st.code("""# Install all dependencies
pip install streamlit selenium PyMuPDF requests

# Install ChromeDriver (must match your Chrome version)
# Option 1: Auto-install via webdriver-manager
pip install webdriver-manager

# Then in your code it auto-downloads the right driver
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
driver = webdriver.Chrome(ChromeDriverManager().install())
""", language="bash")

    if st.button("💾  Save Settings"):
        save_settings(settings)
        st.success("✓ Settings saved")
