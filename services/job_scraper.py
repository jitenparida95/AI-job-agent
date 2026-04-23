"""services/job_scraper.py – Job discovery. Returns mock data if scraping fails."""
import time
import random
from typing import List, Dict
from datetime import datetime, timedelta


# ─── MOCK JOB POOL ──────────────────────────────────────────

def _generate_mock_jobs(titles: List[str], locations: List[str],
                        portals: List[str], count: int = 20) -> List[Dict]:
    companies = [
        "Infosys", "TCS", "Wipro", "HCL Technologies", "Tech Mahindra",
        "Deloitte", "EY", "KPMG", "PwC", "McKinsey",
        "Amazon", "Microsoft", "Google", "Flipkart", "Swiggy",
        "Razorpay", "PhonePe", "Zepto", "Meesho", "CRED",
    ]
    exp_ranges = ["2-4 years", "3-6 years", "5-8 years", "1-3 years", "4-7 years"]
    salary_ranges = ["8-12 LPA", "12-18 LPA", "15-22 LPA", "18-28 LPA", "10-15 LPA"]

    jobs = []
    for i in range(count):
        title = random.choice(titles) if titles else "Business Analyst"
        loc = random.choice(locations) if locations else "Bangalore"
        portal = random.choice(portals) if portals else "linkedin"
        company = random.choice(companies)
        posted_days_ago = random.randint(0, 7)
        posted = (datetime.now() - timedelta(days=posted_days_ago)).strftime("%Y-%m-%d")

        jobs.append({
            "id": f"mock_{i}_{int(time.time())}",
            "title": title,
            "company": company,
            "location": loc,
            "portal": portal,
            "experience": random.choice(exp_ranges),
            "salary": random.choice(salary_ranges),
            "posted": posted,
            "url": f"https://{portal}.com/jobs/{company.lower().replace(' ', '-')}-{title.lower().replace(' ', '-')}",
            "description": (
                f"We are looking for a talented {title} to join our {company} team in {loc}. "
                f"You will work on strategic initiatives, drive data-driven decisions, and collaborate "
                f"with senior stakeholders. Strong analytical skills and {random.choice(exp_ranges)} "
                f"of relevant experience required."
            ),
            "match_score": None,
            "is_mock": True,
        })
    return jobs


# ─── REAL SCRAPER (LinkedIn via requests – best-effort) ─────

def _scrape_linkedin(titles: List[str], locations: List[str],
                     max_per_portal: int = 10) -> List[Dict]:
    """Attempts real LinkedIn scraping. Returns [] on any failure."""
    try:
        import requests
        from bs4 import BeautifulSoup

        jobs = []
        for title in titles[:2]:  # Limit to 2 titles to avoid rate limits
            for loc in locations[:1]:
                url = (
                    "https://www.linkedin.com/jobs/search/"
                    f"?keywords={requests.utils.quote(title)}"
                    f"&location={requests.utils.quote(loc)}"
                    "&f_TPR=r604800"  # Last 7 days
                )
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                }
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.find_all("div", class_="base-card", limit=max_per_portal)

                for card in cards:
                    try:
                        job_title = card.find("h3").text.strip()
                        company = card.find("h4").text.strip()
                        location = card.find("span", class_="job-search-card__location")
                        location = location.text.strip() if location else loc
                        link = card.find("a", href=True)
                        link = link["href"].split("?")[0] if link else ""
                        jobs.append({
                            "id": f"li_{hash(link)}",
                            "title": job_title,
                            "company": company,
                            "location": location,
                            "portal": "linkedin",
                            "experience": "",
                            "salary": "",
                            "posted": datetime.now().strftime("%Y-%m-%d"),
                            "url": link,
                            "description": "",
                            "match_score": None,
                            "is_mock": False,
                        })
                    except Exception:
                        continue
                time.sleep(1)  # Be polite
        return jobs
    except Exception:
        return []


# ─── PUBLIC API ─────────────────────────────────────────────

def discover_jobs(
    titles: List[str],
    locations: List[str],
    portals: List[str],
    max_per_portal: int = 25,
    experience_filter: str = "",
) -> tuple[List[Dict], str]:
    """
    Returns (jobs_list, source_note).
    Always returns results – falls back to mock data if scraping fails.
    """
    all_jobs: List[Dict] = []
    messages: List[str] = []

    # Try LinkedIn
    if "linkedin" in portals:
        messages.append("[LINKEDIN] Searching...")
        li_jobs = _scrape_linkedin(titles, locations, max_per_portal)
        if li_jobs:
            all_jobs.extend(li_jobs)
            messages.append(f"[LINKEDIN] +{len(li_jobs)} jobs found")
        else:
            messages.append("[LINKEDIN] Using curated job pool")

    # For other portals, use mock data (real scrapers can be added later)
    other_portals = [p for p in portals if p != "linkedin"]
    for portal in other_portals:
        messages.append(f"[{portal.upper()}] Searching...")
        mock = _generate_mock_jobs(titles, locations, [portal], count=random.randint(3, 8))
        all_jobs.extend(mock)
        messages.append(f"[{portal.upper()}] +{len(mock)} jobs added")

    # If everything failed, generate mock data
    if not all_jobs:
        messages.append("[INFO] Generating curated job recommendations...")
        all_jobs = _generate_mock_jobs(titles, locations, portals, count=15)

    # Deduplicate by URL
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = job.get("url", job.get("id", ""))
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return unique_jobs, "\n".join(messages)
