import json, os, uuid
from datetime import datetime

DATA_DIR = os.path.expanduser("~/.jobagent")
os.makedirs(DATA_DIR, exist_ok=True)

PREFS_FILE   = f"{DATA_DIR}/prefs.json"
JOBS_FILE    = f"{DATA_DIR}/jobs.json"
APPLIED_FILE = f"{DATA_DIR}/applied.json"
SETTINGS_FILE = f"{DATA_DIR}/settings.json"


def _load(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default

def _save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ── Preferences ──────────────────────────────────────────────
def get_prefs():
    return _load(PREFS_FILE, {
        "name": "Jitendra Parida",
        "email": "",
        "phone": "",
        "target_roles": ["Senior FP&A Analyst", "Finance Manager", "Business Analyst"],
        "target_companies": ["FMCG GCCs", "Consulting", "MNC"],
        "locations": ["Bangalore", "Mumbai", "Hyderabad", "Remote"],
        "min_salary_lpa": 15,
        "max_salary_lpa": 30,
        "experience_years": 6,
        "keywords": ["FP&A", "FMCG", "Supply Chain Finance", "SAP", "Power BI", "IFRS"],
        "exclude_keywords": ["fresher", "0-2 years", "BPO"],
        "resume_path": "",
        "resume_text": "",
        "cover_letter_template": "",
    })

def save_prefs(prefs):
    _save(PREFS_FILE, prefs)


# ── Jobs ─────────────────────────────────────────────────────
def get_jobs():
    return _load(JOBS_FILE, [])

def save_jobs(jobs):
    _save(JOBS_FILE, jobs)

def add_jobs(new_jobs):
    existing = get_jobs()
    existing_urls = {j["url"] for j in existing}
    added = 0
    for j in new_jobs:
        if j.get("url") not in existing_urls:
            j["id"] = str(uuid.uuid4())[:8]
            j["scraped_at"] = datetime.now().isoformat()
            j["status"] = "new"
            j["match_score"] = None
            existing.append(j)
            added += 1
    save_jobs(existing)
    return added


# ── Applied log ───────────────────────────────────────────────
def get_applied():
    return _load(APPLIED_FILE, [])

def log_application(job, cover_letter="", result="applied"):
    apps = get_applied()
    apps.append({
        "id": job.get("id"),
        "title": job.get("title"),
        "company": job.get("company"),
        "portal": job.get("portal"),
        "url": job.get("url"),
        "match_score": job.get("match_score"),
        "cover_letter": cover_letter,
        "result": result,
        "applied_at": datetime.now().isoformat(),
    })
    _save(APPLIED_FILE, apps)


# ── Settings ─────────────────────────────────────────────────
def get_settings():
    return _load(SETTINGS_FILE, {
        "groq_api_key": "",
        "jsearch_api_key": "",
        "naukri_email": "",
        "naukri_password": "",
        "linkedin_email": "",
        "linkedin_password": "",
        "min_match_score": 70,
        "portals": ["naukri", "linkedin", "instahyre", "foundit", "wellfound", "remotive"],
        "daily_apply_limit": 30,
        "headless_browser": True,
        "auto_apply_enabled": False,
    })

def save_settings(s):
    _save(SETTINGS_FILE, s)
