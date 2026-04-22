"""
Job scrapers using:
1. JSearch API (RapidAPI) - pulls from LinkedIn, Naukri, Indeed, Glassdoor in one call
2. requests-based session scrapers with browser cookies for Naukri direct
3. Selenium fallback for portals that require login

JSearch free tier: 200 calls/month (enough for daily use)
Sign up at: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
"""

import json, re, time
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# ── Finance relevance filter ──────────────────────────────────

FINANCE_TITLES = [
    "fp&a", "fpa", "financial planning", "finance manager", "finance analyst",
    "financial analyst", "business analyst", "supply chain finance",
    "budgeting", "forecasting", "cost analyst", "commercial finance",
    "corporate finance", "finance business partner", "financial controller",
    "management accountant", "chartered accountant", "senior analyst finance",
    "accounts manager", "finance lead", "finance head", "vp finance",
    "treasury", "financial reporting", "variance analysis", "mis analyst",
]

EXCLUDE_TITLES = [
    "software engineer", "developer", "fullstack", "frontend", "backend",
    "data scientist", "machine learning", "devops", "react", "python developer",
    "java developer", "android", "ios developer", "ui designer", "ux designer",
    "graphic designer", "content writer", "customer support", "customer retention",
    "sales executive", "telecaller", "hr executive", "recruiter", "teacher",
    "nursing", "driver", "delivery", "field executive",
]


def _is_finance_role(title: str, description: str = "") -> bool:
    t = title.lower()
    d = (description or "").lower()[:600]

    for kw in EXCLUDE_TITLES:
        if kw in t:
            return False

    for kw in FINANCE_TITLES:
        if kw in t:
            return True

    finance_kws = ["fp&a", "fpa", "financial planning", "budgeting", "forecasting",
                   "variance", "p&l", "ebitda", "working capital", "ifrs", "ind as",
                   "sap fi", "hyperion", "anaplan", "management accounting", "mis report"]
    hits = sum(1 for kw in finance_kws if kw in d)
    return hits >= 2


def _make_session():
    """Create requests session with browser-like headers."""
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    })
    return s


# ── JSearch API (RapidAPI) — most reliable ────────────────────

def scrape_jsearch(api_key: str, keywords: list, locations: list,
                   max_jobs: int = 50) -> list:
    """
    JSearch pulls from LinkedIn, Naukri, Indeed, Glassdoor, ZipRecruiter.
    Free tier: 200 calls/month at rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
    """
    if not api_key or not REQUESTS_AVAILABLE:
        return []

    jobs = []
    seen = set()

    finance_queries = [
        f"FP&A Analyst {locations[0] if locations else 'Bangalore'}",
        f"Finance Manager {locations[0] if locations else 'Bangalore'}",
        f"Financial Planning Analysis {locations[0] if locations else 'Bangalore'}",
        f"Business Analyst Finance {locations[0] if locations else 'Bangalore'}",
        f"Supply Chain Finance FMCG {locations[0] if locations else 'Bangalore'}",
        f"Senior Finance Analyst {locations[0] if locations else 'Bangalore'}",
    ]

    # Add user keywords too
    for kw in keywords[:3]:
        finance_queries.insert(0, f"{kw} {locations[0] if locations else 'Bangalore'} India")

    for query in finance_queries[:6]:
        url = "https://jsearch.p.rapidapi.com/search"
        params = {
            "query": query,
            "page": "1",
            "num_pages": "1",
            "country": "in",
            "date_posted": "month",
        }
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "jsearch.p.rapidapi.com",
        }
        try:
            r = requests.get(url, headers=headers, params=params, timeout=15)
            if r.status_code != 200:
                continue
            data = r.json()
            for job in data.get("data", []):
                jid = job.get("job_id", "")
                if jid in seen:
                    continue
                title = job.get("job_title", "")
                desc = job.get("job_description", "")
                if not _is_finance_role(title, desc):
                    continue
                seen.add(jid)
                # Get salary info
                min_sal = job.get("job_min_salary")
                max_sal = job.get("job_max_salary")
                salary = ""
                if min_sal and max_sal:
                    salary = f"{int(min_sal/100000)}-{int(max_sal/100000)} LPA"
                elif min_sal:
                    salary = f"{int(min_sal/100000)}+ LPA"

                jobs.append({
                    "title": title,
                    "company": job.get("employer_name", ""),
                    "location": f"{job.get('job_city', '')} {job.get('job_state', '')}".strip(),
                    "salary": salary,
                    "description": desc[:800],
                    "url": job.get("job_apply_link", job.get("job_google_link", "")),
                    "portal": job.get("job_publisher", "jsearch").lower(),
                    "posted_date": job.get("job_posted_at_datetime_utc", "")[:10],
                })
                if len(jobs) >= max_jobs:
                    return jobs
        except Exception:
            continue
        time.sleep(0.5)

    return jobs


# ── Naukri — requests session approach ───────────────────────

NAUKRI_QUERIES = [
    ("FP%26A+Analyst", "bangalore-jobs"),
    ("Finance+Manager", "bangalore-jobs"),
    ("Financial+Planning+Analysis", "bangalore-jobs"),
    ("Business+Analyst+Finance", "bangalore-jobs"),
    ("Supply+Chain+Finance", "bangalore-jobs"),
    ("Senior+Finance+Analyst", "mumbai-jobs"),
    ("FP%26A", "hyderabad-jobs"),
]


def scrape_naukri(keywords: list, locations: list, experience: int = 6,
                  headless: bool = True, max_jobs: int = 40) -> list:
    """Scrape Naukri using requests session with proper headers."""
    if not REQUESTS_AVAILABLE:
        return []

    jobs = []
    seen = set()
    session = _make_session()
    session.headers.update({
        "appid": "109",
        "systemid": "109",
        "Referer": "https://www.naukri.com/",
        "x-requested-with": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    })

    # First visit homepage to get cookies
    try:
        session.get("https://www.naukri.com/", timeout=10)
        time.sleep(1)
    except Exception:
        pass

    # Build queries
    loc_slug = "bangalore-jobs" if not locations or "bang" in locations[0].lower() else f"{locations[0].lower()}-jobs"
    queries = [(urllib.parse.quote(kw), loc_slug) for kw in keywords[:3]] if False else []

    import urllib.parse
    for kw in keywords[:3]:
        queries.append((urllib.parse.quote(kw.replace("&", "%26")), loc_slug))
    queries += NAUKRI_QUERIES[:5]

    for kw, loc in queries[:7]:
        url = (
            f"https://www.naukri.com/jobapi/v3/search?noOfResults=20"
            f"&urlType=search_by_key_loc&searchType=adv"
            f"&keyword={kw}&location={loc.replace('-jobs', '')}"
            f"&experience={experience}&sort=1"
        )
        try:
            r = session.get(url, timeout=12)
            if r.status_code != 200:
                continue
            data = r.json()
            for job in data.get("jobDetails", []):
                title = job.get("title", "")
                placeholders = job.get("placeholders", [])
                jd_url = "https://www.naukri.com" + job.get("jdURL", "")
                desc = job.get("jobDescription", "")

                if jd_url in seen or not _is_finance_role(title, desc):
                    continue
                seen.add(jd_url)

                loc_str = placeholders[1].get("label", "") if len(placeholders) > 1 else ""
                sal_str = placeholders[2].get("label", "") if len(placeholders) > 2 else ""

                jobs.append({
                    "title": title,
                    "company": job.get("companyName", ""),
                    "location": loc_str,
                    "salary": sal_str,
                    "description": desc,
                    "url": jd_url,
                    "portal": "naukri",
                    "posted_date": job.get("modifiedOn", ""),
                })
                if len(jobs) >= max_jobs:
                    return jobs
        except Exception:
            continue
        time.sleep(0.5)

    return jobs


# ── LinkedIn — public search (no login for discovery) ─────────

LINKEDIN_QUERIES = [
    "FP&A Analyst Bangalore",
    "Finance Manager Bangalore India",
    "Financial Planning Analysis Bangalore",
    "Business Analyst Finance India",
    "Supply Chain Finance FMCG India",
]


def scrape_linkedin(keywords: list, locations: list,
                    email: str = "", password: str = "",
                    headless: bool = True, max_jobs: int = 25) -> list:
    if not REQUESTS_AVAILABLE:
        return []

    jobs = []
    seen = set()
    session = _make_session()

    loc = locations[0] if locations else "Bangalore"
    queries = [f"{kw} {loc}" for kw in keywords[:3]] + LINKEDIN_QUERIES[:3]

    for query in queries[:5]:
        import urllib.parse
        encoded_kw = urllib.parse.quote(query)
        encoded_loc = urllib.parse.quote(loc)
        url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={encoded_kw}&location={encoded_loc}&f_AL=true&start=0"
        )
        try:
            r = session.get(url, timeout=12)
            if r.status_code != 200:
                continue
            job_ids = re.findall(r'data-job-id="(\d+)"', r.text)

            for jid in job_ids[:6]:
                if jid in seen:
                    continue
                seen.add(jid)
                detail_url = f"https://www.linkedin.com/jobs/view/{jid}/"
                try:
                    dr = session.get(detail_url, timeout=10)
                    html = dr.text
                    title_m = re.search(r'<h1[^>]*class="[^"]*top-card-layout__title[^"]*"[^>]*>([^<]+)<', html)
                    company_m = re.search(r'class="[^"]*topcard__org-name-link[^"]*"[^>]*>\s*([^<]+)\s*<', html)
                    location_m = re.search(r'class="[^"]*topcard__flavor--bullet[^"]*"[^>]*>\s*([^<]+)\s*<', html)
                    desc_m = re.search(r'class="[^"]*description__text[^"]*"[^>]*>([\s\S]{0,1500}?)<\/div>', html)

                    title = title_m.group(1).strip() if title_m else query
                    desc = re.sub(r"<[^>]+>", " ", desc_m.group(1)) if desc_m else ""

                    if not _is_finance_role(title, desc):
                        continue

                    jobs.append({
                        "title": title,
                        "company": company_m.group(1).strip() if company_m else "",
                        "location": location_m.group(1).strip() if location_m else loc,
                        "salary": "",
                        "description": desc[:800],
                        "url": detail_url,
                        "portal": "linkedin",
                        "posted_date": datetime.now().strftime("%Y-%m-%d"),
                    })
                    if len(jobs) >= max_jobs:
                        return jobs
                except Exception:
                    continue
                time.sleep(0.8)
        except Exception:
            continue
        time.sleep(1)

    return jobs


# ── Instahyre ─────────────────────────────────────────────────

def scrape_instahyre(keywords: list, locations: list, max_jobs: int = 25) -> list:
    if not REQUESTS_AVAILABLE:
        return []
    jobs = []
    session = _make_session()
    loc = locations[0] if locations else "Bangalore"
    finance_kws = ["FP&A", "Finance Manager", "Financial Analyst", "Business Analyst Finance"]
    all_kws = keywords[:2] + finance_kws

    for kw in all_kws[:5]:
        import urllib.parse
        url = f"https://www.instahyre.com/api/v1/opportunity/?q={urllib.parse.quote(kw)}&l={urllib.parse.quote(loc)}&limit=20"
        try:
            r = session.get(url, timeout=10)
            if r.status_code != 200:
                continue
            for item in r.json().get("results", []):
                title = item.get("designation", "")
                desc = item.get("description", "")
                if not _is_finance_role(title, desc):
                    continue
                min_c = item.get("min_ctc", "")
                max_c = item.get("max_ctc", "")
                jobs.append({
                    "title": title,
                    "company": item.get("company", {}).get("name", ""),
                    "location": item.get("location", loc),
                    "salary": f"{min_c}-{max_c} LPA" if min_c else "",
                    "description": desc,
                    "url": f"https://www.instahyre.com/job-{item.get('id','')}/",
                    "portal": "instahyre",
                    "posted_date": item.get("posted_on", ""),
                })
                if len(jobs) >= max_jobs:
                    return jobs
        except Exception:
            continue
        time.sleep(0.4)
    return jobs


# ── Foundit ───────────────────────────────────────────────────

def scrape_foundit(keywords: list, locations: list, max_jobs: int = 25) -> list:
    if not REQUESTS_AVAILABLE:
        return []
    jobs = []
    session = _make_session()
    session.headers["Referer"] = "https://www.foundit.in/"
    loc = locations[0] if locations else "Bangalore"
    finance_kws = ["FP&A Analyst", "Finance Manager", "Financial Planning", "Business Analyst Finance"]
    all_kws = keywords[:2] + finance_kws

    for kw in all_kws[:5]:
        import urllib.parse
        url = (
            f"https://www.foundit.in/middleware/jobsearch/v1/search"
            f"?query={urllib.parse.quote_plus(kw)}&locationId={urllib.parse.quote_plus(loc)}&limit=20&sort=1"
        )
        try:
            r = session.get(url, timeout=10)
            if r.status_code != 200:
                continue
            job_list = r.json().get("jobSearchResponse", {}).get("data", {}).get("jobList", [])
            for job in job_list:
                title = job.get("jobTitle", "")
                desc = job.get("jobDesc", "")
                if not _is_finance_role(title, desc):
                    continue
                jobs.append({
                    "title": title,
                    "company": job.get("companyName", ""),
                    "location": job.get("jobLocation", loc),
                    "salary": job.get("salaryText", ""),
                    "description": desc,
                    "url": f"https://www.foundit.in/job/{job.get('jobId','')}",
                    "portal": "foundit",
                    "posted_date": job.get("postingDate", ""),
                })
                if len(jobs) >= max_jobs:
                    return jobs
        except Exception:
            continue
        time.sleep(0.4)
    return jobs


def _make_driver(headless=True):
    """
    Create a Selenium Chrome driver.
    Handles three environments:
      1. Streamlit Cloud / Linux servers  — uses the system chromium-browser + chromedriver
      2. Local Windows/Mac with Chrome    — uses webdriver-manager to auto-download chromedriver
      3. Fallback                         — raises a clear error with install instructions
    """
    import os, shutil, subprocess
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    def _build_opts():
        opts = Options()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--remote-debugging-port=9222")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        return opts

    # ── Strategy 1: system chromium (Streamlit Cloud / Ubuntu) ──
    chromium_bin = shutil.which("chromium-browser") or shutil.which("chromium") or shutil.which("google-chrome")
    chromedriver_bin = shutil.which("chromedriver")
    if chromium_bin and chromedriver_bin:
        opts = _build_opts()
        opts.binary_location = chromium_bin
        service = Service(chromedriver_bin)
        return webdriver.Chrome(service=service, options=opts)

    # ── Strategy 2: webdriver-manager (local dev) ───────────────
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        opts = _build_opts()
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=opts)
    except Exception as wdm_err:
        pass

    # ── Strategy 3: try installing chromium on the fly (Linux) ──
    try:
        if os.name != "nt":  # not Windows
            subprocess.run(
                ["apt-get", "install", "-y", "chromium-browser", "chromium-chromedriver"],
                capture_output=True, timeout=120,
            )
            chromium_bin = shutil.which("chromium-browser") or shutil.which("chromium")
            chromedriver_bin = shutil.which("chromedriver")
            if chromium_bin and chromedriver_bin:
                opts = _build_opts()
                opts.binary_location = chromium_bin
                service = Service(chromedriver_bin)
                return webdriver.Chrome(service=service, options=opts)
    except Exception:
        pass

    raise RuntimeError(
        "Chrome/ChromeDriver not found.\n\n"
        "On Streamlit Cloud add to packages.txt:\n"
        "  chromium-browser\n  chromium-chromedriver\n\n"
        "Locally run:\n"
        "  pip install webdriver-manager selenium"
    )


# ── Master function ───────────────────────────────────────────

def scrape_all(prefs: dict, settings: dict, portals: list = None,
               progress_callback=None) -> list:

    portals = portals or settings.get("portals", ["naukri", "linkedin", "instahyre", "foundit"])
    portals = [p for p in portals if p in ["naukri", "linkedin", "instahyre", "foundit", "jsearch"]]

    keywords = prefs.get("target_roles", []) + prefs.get("keywords", [])
    keywords = [k for k in keywords if k]
    locations = prefs.get("locations", ["Bangalore"])
    experience = prefs.get("experience_years", 6)
    headless = settings.get("headless_browser", True)
    jsearch_key = settings.get("jsearch_api_key", "")
    all_jobs = []

    steps = {}

    # JSearch first if key available - most reliable
    if jsearch_key:
        steps["jsearch"] = lambda: scrape_jsearch(jsearch_key, keywords, locations)

    steps["naukri"]    = lambda: scrape_naukri(keywords, locations, experience, headless)
    steps["linkedin"]  = lambda: scrape_linkedin(keywords, locations,
                                                  settings.get("linkedin_email", ""),
                                                  settings.get("linkedin_password", ""), headless)
    steps["instahyre"] = lambda: scrape_instahyre(keywords, locations)
    steps["foundit"]   = lambda: scrape_foundit(keywords, locations)

    total = len([p for p in portals if p in steps or p == "jsearch"])
    done = 0

    for portal, fn in steps.items():
        if portal not in portals and portal != "jsearch":
            continue
        if portal == "jsearch" and not jsearch_key:
            continue
        if progress_callback:
            progress_callback(portal, done, total)
        try:
            jobs = fn()
            all_jobs.extend(jobs)
        except Exception:
            pass
        done += 1

    # Deduplicate by URL
    seen = set()
    unique = []
    for j in all_jobs:
        if j.get("url") not in seen:
            seen.add(j.get("url"))
            unique.append(j)

    return unique
