import json, os, uuid
from datetime import datetime

DATA_DIR = os.path.expanduser("~/.careeros")
os.makedirs(DATA_DIR, exist_ok=True)

PREFS_FILE    = f"{DATA_DIR}/prefs.json"
JOBS_FILE     = f"{DATA_DIR}/jobs.json"
APPLIED_FILE  = f"{DATA_DIR}/applied.json"
SETTINGS_FILE = f"{DATA_DIR}/settings.json"
TRACKER_FILE  = f"{DATA_DIR}/tracker.json"
INTEL_FILE    = f"{DATA_DIR}/career_intel.json"


def _load(path, default):
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return default
    return default

def _save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def get_prefs():
    return _load(PREFS_FILE, {
        "name": "", "email": "", "phone": "",
        "target_roles": [], "target_companies": [], "locations": [],
        "min_salary_lpa": 10, "max_salary_lpa": 25, "experience_years": 3,
        "current_role": "", "current_company": "", "industry": "",
        "keywords": [], "exclude_keywords": ["fresher", "0-2 years"],
        "resume_path": "", "resume_text": "", "cover_letter_template": "",
        "education": "", "linkedin_url": "",
    })

def save_prefs(prefs): _save(PREFS_FILE, prefs)

def get_jobs(): return _load(JOBS_FILE, [])
def save_jobs(jobs): _save(JOBS_FILE, jobs)

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

def get_applied(): return _load(APPLIED_FILE, [])

def log_application(job, cover_letter="", result="applied"):
    apps = get_applied()
    apps.append({
        "id": job.get("id", str(uuid.uuid4())[:8]),
        "title": job.get("title"), "company": job.get("company"),
        "portal": job.get("portal"), "url": job.get("url"),
        "match_score": job.get("match_score"), "cover_letter": cover_letter,
        "result": result, "status": "Applied",
        "applied_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(), "notes": "",
    })
    _save(APPLIED_FILE, apps)

def save_applied(apps): _save(APPLIED_FILE, apps)

def get_tracker(): return _load(TRACKER_FILE, [])
def save_tracker(entries): _save(TRACKER_FILE, entries)

def add_tracker_entry(entry: dict):
    entries = get_tracker()
    entry["id"] = str(uuid.uuid4())[:8]
    entry["created_at"] = datetime.now().isoformat()
    entry["last_updated"] = datetime.now().isoformat()
    entries.append(entry)
    save_tracker(entries)
    return entry

def get_career_intel(): return _load(INTEL_FILE, {})
def save_career_intel(data: dict): _save(INTEL_FILE, data)

def get_settings():
    return _load(SETTINGS_FILE, {
        "groq_api_key": "", "jsearch_api_key": "",
        "naukri_email": "", "naukri_password": "",
        "linkedin_email": "", "linkedin_password": "",
        "min_match_score": 70,
        "portals": ["naukri", "linkedin", "instahyre", "foundit", "wellfound", "remotive"],
        "daily_apply_limit": 30, "headless_browser": True,
        "auto_apply_enabled": False, "tier": "free",
    })

def save_settings(s): _save(SETTINGS_FILE, s)
def is_pro(settings=None):
    if settings is None: settings = get_settings()
    return settings.get("tier", "free") == "pro"
