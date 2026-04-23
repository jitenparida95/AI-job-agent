# 🚀 CareerOS — AI Career Operating System

A complete transformation of the AI Job Agent into a premium, 6-module career platform.

## What's New

| Module | Description |
|--------|-------------|
| 🏠 Command Center | Live dashboard with setup progress, pipeline metrics, readiness checks |
| 🧠 Career Intelligence | 5 ranked career paths, success probabilities, salary trajectories (Y1/Y3/Y5), skill gap analysis |
| 📄 Resume Optimizer | ATS score (0-100), percentile ranking, impact rewrites, missing keywords |
| ✉️ Application Engine | Cover letter, cold email, referral message, LinkedIn DM — all personalized |
| 📊 Tracker & Analytics | Full pipeline tracker, status updates, conversion funnel, weekly score |
| 🤖 AI Career Coach | Personalized insights, focus roles, action plan, live chat |

## Preserved Modules (upgraded UI)

- ✨ Resume Rewriter
- 🔍 Job Discovery
- 🎯 AI Job Matching (+ tier categorization)
- 🚀 Auto Apply
- ⚙️ Settings (+ Free vs Pro comparison)

## Setup

1. **Supabase** — Auth still uses Supabase (see original auth.py comments)
2. **Groq API** — Free at console.groq.com. Powers all AI modules.
3. **JSearch API** — Optional, for Job Discovery via RapidAPI.

### Streamlit secrets.toml

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_ANON_KEY = "eyJh..."
GROQ_API_KEY = "gsk_..."
JSEARCH_API_KEY = "your_rapidapi_key"
```

## Deploy to Streamlit Cloud

1. Push this folder to GitHub
2. Connect at share.streamlit.io
3. Set `app.py` as the main file
4. Add secrets in the dashboard

## Data Storage

All user data stored locally at `~/.careeros/`:
- `prefs.json` — Profile & preferences
- `jobs.json` — Job pipeline
- `applied.json` — Auto-applied log
- `tracker.json` — Manual tracker entries
- `career_intel.json` — Career Intelligence cache
- `settings.json` — API keys & config

## Monetization

- **Free tier**: Job Discovery, basic matching, tracker
- **Pro tier (₹499/mo)**: Career Intelligence, Resume Optimizer, Application Engine, AI Coach
- Upgrade via Razorpay link in Settings → Plan tab
