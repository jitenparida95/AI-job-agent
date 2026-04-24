"""
Scrapers for CareerOS. Streamlit Cloud safe.
JSearch (RapidAPI) is the primary source — works on cloud.
Direct portal scraping as secondary attempt.
Always falls back to demo jobs.
"""
import re, time, json
from datetime import datetime

try:
    import requests
    _REQ = True
except ImportError:
    _REQ = False


FINANCE_TITLES = [
    "fp&a","fpa","financial planning","finance manager","finance analyst",
    "financial analyst","business analyst finance","supply chain finance",
    "budgeting","forecasting","cost analyst","commercial finance",
    "finance business partner","financial controller","management accountant",
    "mis analyst","variance analyst","treasury analyst","financial reporting",
    "chartered accountant","accounts manager","finance lead","finance head",
]
EXCLUDE_TITLES = [
    "software engineer","developer","fullstack","frontend","backend",
    "data scientist","machine learning","devops","react developer",
    "java developer","android developer","ios developer","ui designer",
    "graphic designer","content writer","customer support","telecaller",
    "hr executive","recruiter","driver","delivery executive","field sales",
]

def _is_finance(title: str, desc: str = "") -> bool:
    t = title.lower()
    d = (desc or "").lower()[:500]
    for kw in EXCLUDE_TITLES:
        if kw in t: return False
    for kw in FINANCE_TITLES:
        if kw in t: return True
    hits = sum(1 for kw in ["fp&a","financial planning","budgeting","forecasting",
                              "variance","p&l","ebitda","working capital","ifrs"] if kw in d)
    return hits >= 2


def _session():
    if not _REQ: return None
    s = requests.Session()
    s.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36","Accept-Language":"en-IN,en;q=0.9"})
    return s


# ── JSearch (RapidAPI) — works on Streamlit Cloud ─────────────
def scrape_jsearch(api_key: str, keywords: list, locations: list, max_jobs: int = 40) -> list:
    if not api_key or not _REQ:
        return []
    jobs, seen = [], set()
    loc = locations[0] if locations else "Bangalore"

    queries = [f"{kw} {loc} India" for kw in keywords[:3]] + [
        f"FP&A Analyst {loc}", f"Finance Manager {loc}",
        f"Senior Financial Analyst {loc} FMCG", f"Business Analyst Finance {loc}",
    ]

    for q in queries[:5]:
        try:
            r = requests.get("https://jsearch.p.rapidapi.com/search",
                headers={"x-rapidapi-key":api_key,"x-rapidapi-host":"jsearch.p.rapidapi.com"},
                params={"query":q,"page":"1","num_pages":"1","country":"in","date_posted":"month"},
                timeout=15)
            if r.status_code != 200: continue
            for job in r.json().get("data",[]):
                jid = job.get("job_id","")
                if jid in seen: continue
                title = job.get("job_title","")
                desc  = job.get("job_description","")
                if not _is_finance(title, desc): continue
                seen.add(jid)
                mn = job.get("job_min_salary"); mx = job.get("job_max_salary")
                sal = f"{int(mn/100000)}-{int(mx/100000)} LPA" if mn and mx else ""
                jobs.append({"title":title,"company":job.get("employer_name",""),
                    "location":f"{job.get('job_city','')} {job.get('job_state','')}".strip(),
                    "salary":sal,"description":desc[:600],
                    "url":job.get("job_apply_link",job.get("job_google_link","")),
                    "portal":job.get("job_publisher","jsearch").lower()[:10],
                    "posted_date":(job.get("job_posted_at_datetime_utc") or "")[:10],
                    "match_score":None,"status":"new"})
                if len(jobs) >= max_jobs: return jobs
        except Exception:
            continue
        time.sleep(0.4)
    return jobs


# ── Naukri (requests session) ─────────────────────────────────
def scrape_naukri(keywords: list, locations: list, experience: int = 6, *args, **kwargs) -> list:
    s = _session()
    if not s: return []
    jobs, seen = [], set()
    s.headers.update({"appid":"109","systemid":"109","Referer":"https://www.naukri.com/","Accept":"application/json"})
    try: s.get("https://www.naukri.com/", timeout=8); time.sleep(0.5)
    except Exception: pass

    loc = (locations[0] if locations else "Bangalore").lower().replace(" ","-")
    import urllib.parse
    queries = [(urllib.parse.quote(str(kw).replace("&","%26")), loc) for kw in keywords[:3]]
    queries += [("FP%26A+Analyst","bangalore"),("Finance+Manager","bangalore"),
                ("Financial+Planning+Analysis","bangalore"),("Senior+Finance+Analyst","mumbai")]

    for kw, l in queries[:7]:
        try:
            url = (f"https://www.naukri.com/jobapi/v3/search?noOfResults=15"
                   f"&urlType=search_by_key_loc&searchType=adv"
                   f"&keyword={kw}&location={l}&experience={experience}&sort=1")
            r = s.get(url, timeout=12)
            if r.status_code != 200: continue
            for job in r.json().get("jobDetails",[]):
                title = job.get("title","")
                desc  = job.get("jobDescription","")
                jd_url = "https://www.naukri.com" + job.get("jdURL","")
                if jd_url in seen or not _is_finance(title, desc): continue
                seen.add(jd_url)
                p = job.get("placeholders",[])
                jobs.append({"title":title,"company":job.get("companyName",""),
                    "location":p[1].get("label","") if len(p)>1 else "",
                    "salary":p[2].get("label","") if len(p)>2 else "",
                    "description":desc[:500],"url":jd_url,"portal":"naukri",
                    "posted_date":job.get("modifiedOn",""),"match_score":None,"status":"new"})
        except Exception:
            continue
        time.sleep(0.4)
    return jobs


# ── LinkedIn public scrape ─────────────────────────────────────
def scrape_linkedin(keywords: list, locations: list, *args, **kwargs) -> list:
    s = _session()
    if not s: return []
    jobs, seen = [], set()
    loc = locations[0] if locations else "Bangalore"
    import urllib.parse

    for kw in keywords[:3]:
        try:
            r = s.get(
                f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                f"?keywords={urllib.parse.quote(str(kw))}&location={urllib.parse.quote(loc)}&f_AL=true&start=0",
                timeout=12)
            if r.status_code != 200: continue
            for jid in re.findall(r'data-job-id="(\d+)"', r.text)[:5]:
                if jid in seen: continue
                seen.add(jid)
                try:
                    dr = s.get(f"https://www.linkedin.com/jobs/view/{jid}/", timeout=10)
                    html = dr.text
                    tm = re.search(r'top-card-layout__title[^>]+>([^<]+)<', html)
                    cm = re.search(r'topcard__org-name-link[^>]+>\s*([^<]+)\s*<', html)
                    dm = re.search(r'description__text[^>]+>([\s\S]{0,1000}?)<\/div>', html)
                    title = tm.group(1).strip() if tm else str(kw)
                    desc  = re.sub(r"<[^>]+>"," ",dm.group(1)) if dm else ""
                    if not _is_finance(title, desc): continue
                    jobs.append({"title":title,"company":cm.group(1).strip() if cm else "",
                        "location":loc,"salary":"","description":desc[:500],
                        "url":f"https://www.linkedin.com/jobs/view/{jid}/","portal":"linkedin",
                        "posted_date":datetime.now().strftime("%Y-%m-%d"),"match_score":None,"status":"new"})
                except Exception: continue
                time.sleep(0.5)
        except Exception: continue
        time.sleep(0.8)
    return jobs


def scrape_instahyre(keywords: list, locations: list, *args, **kwargs) -> list:
    s = _session()
    if not s: return []
    jobs = []
    import urllib.parse
    loc = locations[0] if locations else "Bangalore"
    for kw in keywords[:3]:
        try:
            r = s.get(f"https://www.instahyre.com/api/v1/opportunity/?q={urllib.parse.quote(str(kw))}&l={urllib.parse.quote(loc)}&limit=20",timeout=10)
            if r.status_code!=200: continue
            for item in r.json().get("results",[]):
                title = item.get("designation","")
                desc  = item.get("description","")
                if not _is_finance(title,desc): continue
                mn=item.get("min_ctc",""); mx=item.get("max_ctc","")
                jobs.append({"title":title,"company":item.get("company",{}).get("name",""),
                    "location":item.get("location",loc),"salary":f"{mn}-{mx} LPA" if mn else "",
                    "description":desc[:500],"url":f"https://www.instahyre.com/job-{item.get('id','')}/",
                    "portal":"instahyre","posted_date":item.get("posted_on",""),"match_score":None,"status":"new"})
        except Exception: continue
        time.sleep(0.3)
    return jobs


def scrape_foundit(keywords: list, locations: list, *args, **kwargs) -> list:
    s = _session()
    if not s: return []
    jobs = []
    import urllib.parse
    loc = locations[0] if locations else "Bangalore"
    for kw in keywords[:3]:
        try:
            r = s.get(f"https://www.foundit.in/middleware/jobsearch/v1/search?query={urllib.parse.quote_plus(str(kw))}&locationId={urllib.parse.quote_plus(loc)}&limit=20&sort=1",
                headers={"Referer":"https://www.foundit.in/"},timeout=10)
            if r.status_code!=200: continue
            for job in r.json().get("jobSearchResponse",{}).get("data",{}).get("jobList",[]):
                title=job.get("jobTitle",""); desc=job.get("jobDesc","")
                if not _is_finance(title,desc): continue
                jobs.append({"title":title,"company":job.get("companyName",""),
                    "location":job.get("jobLocation",loc),"salary":job.get("salaryText",""),
                    "description":desc[:500],"url":f"https://www.foundit.in/job/{job.get('jobId','')}",
                    "portal":"foundit","posted_date":job.get("postingDate",""),"match_score":None,"status":"new"})
        except Exception: continue
        time.sleep(0.3)
    return jobs


# ── Master (with demo fallback) ────────────────────────────────
DEMO_JOBS = [
    {"title":"Senior FP&A Analyst","company":"Unilever GCC","location":"Bangalore","salary":"18-24 LPA","description":"FP&A, budgeting, forecasting, variance analysis, SAP, Power BI. Supply chain P&L. 5+ years FMCG finance.","url":"https://www.naukri.com/fpa-analyst-jobs","portal":"naukri","match_score":None,"status":"new"},
    {"title":"Finance Manager - Supply Chain","company":"Reckitt GCC","location":"Bangalore","salary":"22-28 LPA","description":"Lead supply chain finance team. FP&A, IFRS, working capital, DIO/DSO. FMCG experience essential.","url":"https://www.linkedin.com/jobs/view/1001","portal":"linkedin","match_score":None,"status":"new"},
    {"title":"Senior Business Analyst - Finance","company":"Capgemini","location":"Bangalore","salary":"16-22 LPA","description":"Finance BA: SAP FI, requirements gathering, Power BI dashboards, stakeholder management, process mapping.","url":"https://www.naukri.com/business-analyst-jobs","portal":"naukri","match_score":None,"status":"new"},
    {"title":"FP&A Lead","company":"Marico Ltd","location":"Mumbai","salary":"20-26 LPA","description":"Lead FP&A function. Monthly MIS, annual budgeting, 3-year LRP, EBITDA bridge analysis and tracking.","url":"https://www.foundit.in/job/marico-fpa","portal":"foundit","match_score":None,"status":"new"},
    {"title":"Senior Financial Analyst","company":"ITC Limited","location":"Bangalore","salary":"15-20 LPA","description":"Financial planning, variance reporting, management reporting, SAP. CA/MBA preferred. FMCG experience.","url":"https://www.naukri.com/financial-analyst-jobs","portal":"naukri","match_score":None,"status":"new"},
    {"title":"Finance Business Partner","company":"Hindustan Unilever","location":"Mumbai","salary":"24-32 LPA","description":"Strategic finance partner. P&L ownership, forecasting, investment appraisals, board presentations.","url":"https://www.linkedin.com/jobs/view/1002","portal":"linkedin","match_score":None,"status":"new"},
    {"title":"FP&A Manager","company":"P&G India","location":"Mumbai","salary":"26-35 LPA","description":"Lead FP&A team of 4. Drive annual operating plan, monthly forecasting, EBITDA variance, CFO reporting.","url":"https://www.linkedin.com/jobs/view/1003","portal":"linkedin","match_score":None,"status":"new"},
    {"title":"Supply Chain Finance Analyst","company":"Nestlé India","location":"Gurgaon","salary":"14-20 LPA","description":"Supply chain finance: standard costing, DIO/DSO tracking, working capital optimization, ERP SAP.","url":"https://www.naukri.com/supply-chain-finance","portal":"naukri","match_score":None,"status":"new"},
]


def scrape_all(prefs: dict, settings: dict, portals: list = None, progress_callback=None) -> list:
    portals = portals or settings.get("portals",["naukri","linkedin"])
    keywords = list(prefs.get("target_roles") or []) + list(prefs.get("keywords") or [])
    if not keywords: keywords = ["FP&A Analyst","Finance Manager","Financial Analyst"]
    locations = list(prefs.get("locations") or ["Bangalore"])
    exp = prefs.get("experience_years", 6)
    jsearch_key = settings.get("jsearch_api_key","")
    all_jobs = []

    scraper_map = {
        "jsearch":  lambda: scrape_jsearch(jsearch_key, keywords, locations) if jsearch_key else [],
        "naukri":   lambda: scrape_naukri(keywords, locations, exp),
        "linkedin": lambda: scrape_linkedin(keywords, locations),
        "instahyre":lambda: scrape_instahyre(keywords, locations),
        "foundit":  lambda: scrape_foundit(keywords, locations),
    }

    active = [p for p in (["jsearch"]+portals if jsearch_key else portals) if p in scraper_map]

    for i, portal in enumerate(active):
        if progress_callback: progress_callback(portal, i, len(active))
        try:
            jobs = scraper_map[portal]()
            all_jobs.extend(jobs)
        except Exception: pass

    # Deduplicate
    seen, unique = set(), []
    for j in all_jobs:
        key = j.get("url","") or f"{j.get('title','')}_{j.get('company','')}"
        if key not in seen:
            seen.add(key)
            unique.append(j)

    return unique if unique else []
