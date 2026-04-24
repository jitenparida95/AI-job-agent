import json
import urllib.request


def _call_groq(prompt: str, api_key: str, max_tokens: int = 1200, temperature: float = 0.3) -> str:
    """Call Groq API. Returns empty string on any failure — NEVER raises."""
    if not api_key:
        return ""
    try:
        payload = json.dumps({
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }).encode()
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except Exception:
        return ""


def _parse_json(raw: str) -> dict:
    if not raw:
        return {}
    raw = raw.strip()
    for fence in ["```json", "```"]:
        if fence in raw:
            raw = raw.split(fence)[-1].split("```")[0]
    try:
        return json.loads(raw.strip())
    except Exception:
        return {}


# ── Job Match Scoring ─────────────────────────────────────────
def score_job(job: dict, prefs: dict, api_key: str) -> dict:
    if api_key:
        prompt = f"""Score this job match. Respond ONLY with valid JSON.

CANDIDATE:
- Target roles: {prefs.get('target_roles')}
- Experience: {prefs.get('experience_years')} years
- Skills: {prefs.get('keywords')}
- Salary: {prefs.get('min_salary_lpa')}-{prefs.get('max_salary_lpa')} LPA
- Locations: {prefs.get('locations')}

JOB:
Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location', '')}
Salary: {job.get('salary', '')}
Description: {str(job.get('description', ''))[:600]}

JSON format:
{{"score": <0-100>, "reasons": ["reason1"], "matched_keywords": ["kw1"], "missing": ["gap1"], "recommendation": "apply"}}"""
        result = _parse_json(_call_groq(prompt, api_key, max_tokens=400))
        if result and "score" in result:
            return result

    # Heuristic fallback
    score = 40
    jd_lower = f"{job.get('title','')} {job.get('description','')}".lower()
    for kw in (prefs.get("keywords") or []):
        if str(kw).lower() in jd_lower:
            score += 5
    for role in (prefs.get("target_roles") or []):
        if any(w in jd_lower for w in str(role).lower().split()):
            score += 8
    for excl in (prefs.get("exclude_keywords") or []):
        if str(excl).lower() in jd_lower:
            score -= 20
    score = max(0, min(100, score))
    return {
        "score": score,
        "reasons": ["Keyword-based heuristic match"],
        "matched_keywords": [],
        "missing": [],
        "recommendation": "apply" if score >= 70 else ("maybe" if score >= 50 else "skip")
    }


# ── Career Intelligence ────────────────────────────────────────
def analyze_career_paths(prefs: dict, api_key: str) -> dict:
    if api_key:
        prompt = f"""Analyze this career profile. Return ONLY valid JSON.

PROFILE:
- Current role: {prefs.get('current_role', 'Not specified')}
- Experience: {prefs.get('experience_years')} years
- Skills: {prefs.get('keywords')}
- Industry: {prefs.get('industry', 'General')}
- Target roles: {prefs.get('target_roles')}
- Target salary: {prefs.get('min_salary_lpa')}-{prefs.get('max_salary_lpa')} LPA
- Resume snippet: {str(prefs.get('resume_text', ''))[:400]}

Return exactly 5 career paths:
{{"career_paths":[{{"title":"...","category":"Lateral|Upward|Pivot","success_probability":75,"time_to_achieve":"3-6 months","salary_year1":18,"salary_year3":24,"salary_year5":32,"skill_gaps":["gap1"],"required_skills":["skill1"],"recommended_certifications":["cert1"],"companies_hiring":["co1","co2"],"why_fit":"explanation","action_priority":1}}],"ats_keywords_missing":["kw1"],"market_demand":"High","competitive_insight":"insight text","immediate_actions":["action1","action2","action3"]}}"""
        result = _parse_json(_call_groq(prompt, api_key, max_tokens=2000))
        if result and result.get("career_paths"):
            return result

    return _mock_career_intel(prefs)


def _mock_career_intel(prefs: dict) -> dict:
    roles = prefs.get("target_roles") or ["Senior Analyst", "Finance Manager"]
    base_sal = prefs.get("min_salary_lpa") or 10
    return {
        "career_paths": [
            {"title": roles[0] if roles else "Senior FP&A Analyst", "category": "Upward", "success_probability": 82,
             "time_to_achieve": "3-6 months", "salary_year1": base_sal+5, "salary_year3": base_sal+10, "salary_year5": base_sal+18,
             "skill_gaps": ["Advanced Excel", "SQL"], "required_skills": (prefs.get("keywords") or [])[:4],
             "recommended_certifications": ["CFA Level 1", "CMA"], "companies_hiring": ["Deloitte","KPMG","EY","IBM"],
             "why_fit": "Strong match with your current skill trajectory.", "action_priority": 1},
            {"title": roles[1] if len(roles)>1 else "Business Analyst", "category": "Lateral", "success_probability": 71,
             "time_to_achieve": "2-4 months", "salary_year1": base_sal+3, "salary_year3": base_sal+9, "salary_year5": base_sal+15,
             "skill_gaps": ["Agile","Product thinking"], "required_skills": (prefs.get("keywords") or [])[:3],
             "recommended_certifications": ["CSPO","Six Sigma"], "companies_hiring": ["Amazon","Microsoft","Swiggy"],
             "why_fit": "Leverages analytical background in a growing market.", "action_priority": 2},
        ],
        "ats_keywords_missing": ["Python","Tableau","Agile","KPIs"],
        "market_demand": "High",
        "competitive_insight": "Market demand is strong for finance professionals. Add Groq API key for personalized analysis.",
        "immediate_actions": ["Upload resume for deeper analysis","Add Groq API key in Settings","Set target salary range"]
    }


# ── Resume ATS Optimizer ──────────────────────────────────────
def analyze_resume_ats(resume_text: str, prefs: dict, api_key: str) -> dict:
    if api_key and resume_text:
        prompt = f"""Analyze this resume for ATS optimization. Return ONLY valid JSON.

TARGET ROLE: {prefs.get('target_roles', ['Analyst'])}
EXPERIENCE: {prefs.get('experience_years')} years

RESUME:
{resume_text[:2000]}

JSON format:
{{"ats_score":<0-100>,"percentile":<0-100>,"strengths":["s1","s2"],"critical_gaps":["g1","g2"],"missing_keywords":["kw1","kw2","kw3"],"formatting_issues":["i1"],"impact_statements_weak":["weak1"],"impact_statements_improved":["strong1"],"recommended_summary":"2-3 sentences","overall_verdict":"one sentence","quick_wins":["win1","win2","win3"]}}"""
        result = _parse_json(_call_groq(prompt, api_key, max_tokens=1200))
        if result and "ats_score" in result:
            return result

    return _mock_ats(prefs)


def _mock_ats(prefs: dict) -> dict:
    return {
        "ats_score": 58, "percentile": 42,
        "strengths": ["Relevant experience", "Quantified achievements", "Clear structure"],
        "critical_gaps": ["Missing action verbs", "No metrics in last 2 roles"],
        "missing_keywords": ["KPI", "Stakeholder management", "Data-driven", "Cross-functional"],
        "formatting_issues": ["Use standard section headers"],
        "impact_statements_weak": ["Responsible for financial reporting"],
        "impact_statements_improved": ["Led monthly financial reporting for ₹50Cr portfolio, reducing close time by 2 days"],
        "recommended_summary": f"Results-driven {prefs.get('experience_years', 3)}-year finance professional. Add Groq API key for personalized analysis.",
        "overall_verdict": "Resume needs optimization. Add Groq API key for detailed recommendations.",
        "quick_wins": ["Add metrics to every bullet", "Include ATS keywords from job descriptions", "Add a skills summary section"]
    }


# ── Application Content Generator ────────────────────────────
def generate_application_content(job: dict, prefs: dict, content_type: str, api_key: str) -> str:
    templates = {
        "cover_letter":    _gen_cover_letter,
        "cold_email":      _gen_cold_email,
        "referral_message": _gen_referral,
        "linkedin_dm":     _gen_linkedin_dm,
    }
    fn = templates.get(content_type, _gen_cover_letter)
    try:
        return fn(job, prefs, api_key)
    except Exception:
        return f"Content generation failed. Please verify your Groq API key in Settings and try again."


def _gen_cover_letter(job, prefs, api_key):
    name = prefs.get("name") or "Candidate"
    role = job.get("title", "this role")
    company = job.get("company", "your company")
    exp = prefs.get("experience_years", 3)

    if api_key:
        prompt = f"""Write a compelling cover letter (220-260 words).

CANDIDATE: {name} | {exp} years experience
SKILLS: {prefs.get('keywords')}
RESUME SNIPPET: {str(prefs.get('resume_text',''))[:400]}

JOB: {role} at {company}
JD: {str(job.get('description',''))[:500]}

Rules: Open with quantified impact. Connect 2-3 skills to JD. No "I am writing to express" openers. Output ONLY the letter body."""
        result = _call_groq(prompt, api_key, max_tokens=600)
        if result:
            return result

    return f"""With {exp}+ years in finance and FP&A, I bring the analytical rigour and commercial insight that the {role} role at {company} demands.

In my current position, I manage multi-million pound supply chain P&Ls — owning period-close, variance analysis, and Director-level reporting. I've driven automation initiatives that reduced reporting cycle time by 40% and built forecasting models that improved budget accuracy.

For this role, I offer hands-on FP&A expertise across budgeting, forecasting, and actuals-vs-plan variance, combined with strong technical skills (SAP, Power BI, advanced Excel).

I'd welcome a conversation about how I can add immediate value to {company}'s finance function.

Best regards,
{name}"""


def _gen_cold_email(job, prefs, api_key):
    name = prefs.get("name") or "Candidate"
    role = job.get("title", "Finance")
    company = job.get("company", "your company")
    exp = prefs.get("experience_years", 3)

    if api_key:
        prompt = f"""Write a cold outreach email for a job (150-180 words). Include subject line.
CANDIDATE: {name} | {exp} yrs | Skills: {prefs.get('keywords')}
JOB: {role} at {company}
Rules: Punchy subject. Research the company. One achievement with number. Clear ask. Output ONLY the email."""
        result = _call_groq(prompt, api_key, max_tokens=350)
        if result:
            return result

    return f"""Subject: {role} — {exp}yr Finance Professional | Open to Explore

Hi [Name],

I noticed {company} is building out its finance function and wanted to reach out directly.

I'm a finance professional with {exp} years specializing in FP&A and supply chain finance — managing multi-million portfolios, driving variance analysis, and delivering Finance Director-level reporting.

If there's an opening for a {role} or similar, I'd love 15 minutes to explore whether there's a fit.

Best,
{name}"""


def _gen_referral(job, prefs, api_key):
    name = prefs.get("name") or "Candidate"
    role = job.get("title", "Finance Role")
    company = job.get("company", "")
    exp = prefs.get("experience_years", 3)

    if api_key:
        prompt = f"""Write a referral request (100-130 words). Professional but warm.
FROM: {name} ({exp} yrs, {(prefs.get('keywords') or [])[:3]})
TARGET: {role} at {company}
Rules: Acknowledge relationship. Specific role. One achievement. Make it easy to say yes. Output ONLY the message."""
        result = _call_groq(prompt, api_key, max_tokens=250)
        if result:
            return result

    return f"""Hi [Name],

I hope you're doing well! I'm reaching out because I noticed a {role} opening at {company} and thought you might be able to help.

With {exp} years in finance and FP&A, I've been managing large-scale P&Ls and driving significant process improvements. I think it could be a strong fit.

If you're comfortable with it, would you be able to refer me or share any insights about the team? I'm happy to send my resume.

Thanks so much,
{name}"""


def _gen_linkedin_dm(job, prefs, api_key):
    name = prefs.get("name") or "Candidate"
    role = job.get("title", "Finance")
    company = job.get("company", "")
    kws = (prefs.get("keywords") or ["finance"])[0]

    if api_key:
        prompt = f"""Write a LinkedIn DM (under 120 words). Conversational, not salesy.
FROM: {name} | Skills: {(prefs.get('keywords') or [])[:3]}
JOB: {role} at {company}
Rules: Genuine connection point. One-liner on relevant experience. Soft ask. No "I hope this finds you well". Output ONLY the message."""
        result = _call_groq(prompt, api_key, max_tokens=200)
        if result:
            return result

    return f"""Hi [Name],

I came across your profile while researching {company}'s finance team — really impressed by the work you're doing there.

I'm a finance professional with a background in {kws} and FP&A, and I noticed the {role} opening. My experience managing large P&Ls and delivering variance analysis feels like a good match.

Would you be open to a quick 15-minute chat to explore if there's a fit?

Thanks,
{name}"""


# ── AI Career Coach ───────────────────────────────────────────
def generate_coach_insights(prefs: dict, tracker_data: list, applied_data: list, api_key: str) -> dict:
    total = len(applied_data) + len(tracker_data)
    statuses = {}
    for entry in tracker_data:
        s = entry.get("status", "Applied")
        statuses[s] = statuses.get(s, 0) + 1

    if api_key:
        prompt = f"""Analyze this job seeker's activity. Return ONLY valid JSON.

PROFILE:
- Target roles: {prefs.get('target_roles')}
- Experience: {prefs.get('experience_years')} years
- Skills: {prefs.get('keywords')}

ACTIVITY:
- Total tracked: {total}
- Status breakdown: {statuses}

JSON format:
{{"weekly_score":<0-100>,"score_label":"Good","headline_insight":"max 15 words","insights":[{{"type":"info","title":"title","body":"2-3 sentences"}}],"focus_roles":["role1","role2"],"this_week_actions":["action1","action2","action3"],"conversion_rate":0.1,"benchmark_comparison":"1 sentence"}}"""
        result = _parse_json(_call_groq(prompt, api_key, max_tokens=800))
        if result and "weekly_score" in result:
            return result

    return _mock_coach_insights(total, statuses)


def _mock_coach_insights(total, statuses):
    interviews = statuses.get("Interview", 0)
    rate = round(interviews / max(total, 1), 2)
    return {
        "weekly_score": min(100, 30 + total * 5),
        "score_label": "Needs Work" if total < 5 else "Good",
        "headline_insight": "Increase application volume to get market feedback faster.",
        "insights": [
            {"type": "info", "title": "Volume is your friend", "body": "Job seekers who apply to 15+ roles/week get first responses 60% faster. Set a daily target of 3-5 applications."},
            {"type": "warning", "title": "Diversify your portals", "body": "Don't rely on a single platform. LinkedIn, Naukri, and Instahyre reach different hiring managers."},
            {"type": "success", "title": "Resume is your asset", "body": "A well-optimized resume gets 3x more callbacks. Use the Resume Optimizer to boost your ATS score above 75."}
        ],
        "focus_roles": ["Add Groq API key for personalized role recommendations"],
        "this_week_actions": ["Apply to 15 roles minimum", "Optimize resume ATS score", "Send 3 cold emails to target companies"],
        "conversion_rate": rate,
        "benchmark_comparison": "Add Groq API key for personalized benchmarking."
    }


# ── Cover letter (legacy compatibility) ──────────────────────
def generate_cover_letter(job: dict, prefs: dict, template: str, api_key: str) -> str:
    return _gen_cover_letter(job, prefs, api_key)
