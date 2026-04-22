# ⚡ JobAgent AI — Automated Job Application Bot

AI-powered job discovery, matching, and auto-apply agent.  
Built for FP&A / Finance professionals targeting FMCG GCCs and consulting firms.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

## Setup Order (inside the app)

1. **Settings** → Add your Groq API key (free at console.groq.com)
2. **Settings** → Add Naukri + LinkedIn credentials
3. **Resume & Prefs** → Upload resume PDF + set target roles, salary, keywords
4. **Job Discovery** → Select portals → Run scan
5. **AI Matching** → Score all jobs against your resume
6. **Auto Apply** → Review the apply queue → Hit Apply Now

## Portal Coverage

| Portal | Method | Login needed |
|--------|--------|-------------|
| Naukri.com | Internal API + Selenium apply | Yes (for apply) |
| LinkedIn | Public scrape + Easy Apply | Yes (for apply) |
| Instahyre | API | No |
| Foundit | API | No |
| Wellfound | GraphQL API | No |
| Remotive | Public API | No |

## Architecture

```
app.py                 ← Streamlit entry point + CSS theme
├── pages/
│   ├── dashboard.py   ← Overview + quick actions
│   ├── resume.py      ← Resume upload + job preferences
│   ├── discovery.py   ← Multi-portal job scraping
│   ├── matching.py    ← AI match scoring (Groq/Llama 3.1)
│   ├── apply.py       ← Bulk auto-apply with Selenium
│   ├── log.py         ← Application history tracker
│   └── settings.py    ← Credentials + config
└── core/
    ├── store.py        ← JSON-based persistence (~/.jobagent/)
    ├── scrapers.py     ← Portal scrapers (API + Selenium)
    ├── ai_engine.py    ← Match scoring + cover letter gen
    └── apply_bot.py    ← Selenium apply automation
```

## CAPTCHA Note

On first run, LinkedIn/Naukri may show a CAPTCHA. Go to Settings → turn OFF headless 
mode → run once → solve the CAPTCHA manually → turn headless back on.

## Data Privacy

All data is stored locally in `~/.jobagent/` — no cloud sync, no third-party sharing.
Your credentials never leave your machine.
