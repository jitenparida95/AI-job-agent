# 🚀 CareerOS – AI Career Operating System

A **production-ready SaaS** Streamlit app for AI-powered job searching, resume optimization, and career coaching.

---

## ✅ Features

| Module | Description | Free | Pro |
|---|---|---|---|
| Job Discovery | Search across Naukri, LinkedIn, Foundit, etc. | ✅ | ✅ |
| AI Job Matching | Score and rank jobs vs your resume | ✅ | ✅ |
| Resume Optimizer | ATS-optimized resume rewriting | Template | AI |
| Application Engine | Cover letters, cold emails, referrals | Template | AI |
| Auto Apply | Automated job applications | 5/day | 50/day |
| Tracker & Analytics | Track application status | ✅ | ✅ |
| AI Career Coach | Chat-based career guidance | Template | AI |
| Career Intelligence | Market insights and strategy | Template | AI |

---

## 🚀 Quick Start

### 1. Clone / download the project

```bash
cd careeros
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```env
# At minimum, add ONE of these for real AI (Groq is free):
GROQ_API_KEY=gsk_...          # Free at console.groq.com
OPENAI_API_KEY=sk-...         # platform.openai.com

# For payments (optional):
RAZORPAY_KEY_ID=rzp_live_...
RAZORPAY_KEY_SECRET=...
```

> **No keys needed to run** – app works in demo mode with template responses.

### 4. Run

```bash
streamlit run app.py
```

Open http://localhost:8501

---

## 📁 Project Structure

```
careeros/
├── app.py                  # Main entry point + auth gate
├── config.py               # Central config loader
├── .env                    # Your keys (not committed)
├── .env.example            # Key template
├── requirements.txt
│
├── pages/                  # One file per page (Streamlit multi-page)
│   ├── dashboard.py
│   ├── career_intelligence.py
│   ├── resume_optimizer.py
│   ├── resume_rewriter.py
│   ├── job_discovery.py
│   ├── matching.py
│   ├── application_engine.py
│   ├── auto_apply.py
│   ├── tracker.py
│   ├── coach.py
│   └── settings.py
│
├── components/             # Reusable UI components
│   ├── auth.py             # Login / signup forms
│   ├── sidebar.py          # Navigation sidebar
│   └── ui.py               # Cards, alerts, helpers
│
├── services/               # Business logic
│   ├── ai_service.py       # AI calls + mock fallback
│   ├── job_scraper.py      # Job discovery + mock data
│   └── payment.py          # Razorpay / demo upgrade
│
├── utils/
│   └── session.py          # Safe session state helpers
│
├── database/
│   └── db.py               # SQLite (users, apps, resumes)
│
└── data/
    └── careeros.db         # Auto-created on first run
```

---

## 🐞 Bugs Fixed

| Bug | Root Cause | Fix |
|---|---|---|
| `IndexError` on Dashboard | `.split()[0]` on empty name string | `get_first_name()` returns `"there"` safely |
| `HTTP 403` on Resume Rewriter | API key not loaded, no fallback | Try 3 providers → mock template if all fail |
| `HTTP 403` on AI Coach | Same API issue | Same fix + chat history preserved in session |
| App crash on missing user data | No default session values | `init_session()` sets all defaults on startup |
| Payment not unlocking Pro | No DB write after payment | `upgrade_user_to_pro()` writes to SQLite + session |
| Raw tracebacks shown to users | No global error handling | All pages wrapped in try/except with clean UI |
| App resets on every action | No session persistence | `st.session_state` properly initialized + SQLite |

---

## 💰 Monetization Setup

### Razorpay (India)
1. Create account at razorpay.com
2. Add `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` to `.env`
3. Create a payment link in Razorpay dashboard
4. Update the link in `pages/settings.py`

### Demo Mode (no keys)
- Click **"Simulate Pro Upgrade"** in Settings → Plan
- Instantly unlocks Pro features for testing

---

## 🔑 Getting Free AI Keys

| Provider | URL | Free Tier |
|---|---|---|
| Groq | console.groq.com | 14,400 req/day free |
| OpenAI | platform.openai.com | $5 free credit |
| Anthropic | console.anthropic.com | $5 free credit |

---

## 🌐 Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to share.streamlit.io
3. Connect your repo, set `app.py` as entry point
4. Add secrets in the Streamlit Cloud dashboard (same keys as `.env`)

```toml
# .streamlit/secrets.toml (for cloud deployment)
OPENAI_API_KEY = "sk-..."
GROQ_API_KEY = "gsk_..."
RAZORPAY_KEY_ID = "rzp_..."
RAZORPAY_KEY_SECRET = "..."
```
