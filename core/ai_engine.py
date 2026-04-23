import json
import urllib.request


def _call_groq(prompt: str, api_key: str, max_tokens: int = 1200, temperature: float = 0.3) -> str:
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


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    for fence in ["```json", "```"]:
        if fence in raw:
            raw = raw.split(fence)[-1].split("```")[0]
    return json.loads(raw.strip())


# ── Job Match Scoring ─────────────────────────────────────────
def score_job(job: dict, prefs: dict, api_key: str) -> dict:
    if api_key:
        prompt = f"""You are a senior recruiter. Score this job match objectively.

CANDIDATE:
- Target roles: {prefs.get('target_roles')}
- Experience: {prefs.get('experience_years')} years
- Skills: {prefs.get('keywords')}
- Salary: {prefs.get('min_salary_lpa')}-{prefs.get('max_salary_lpa')} LPA
- Locations: {prefs.get('locations')}
- Exclude: {prefs.get('exclude_keywords')}

JOB:
Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location', '')}
Salary: {job.get('salary', '')}
Description: {job.get('description', '')[:800]}

Respond ONLY with valid JSON:
{{
  "score": <0-100>,
  "reasons": ["reason1", "reason2"],
  "matched_keywords": ["kw1", "kw2"],
  "missing": ["gap1"],
  "recommendation": "apply" | "skip" | "maybe"
}}"""
        try:
            return _parse_json(_call_groq(prompt, api_key))
        except Exception:
            pass

    # Heuristic fallback
    score = 40
    jd_lower = f"{job.get('title','')} {job.get('description','')}".lower()
    for kw in prefs.get("keywords", []):
        if kw.lower() in jd_lower:
            score += 5
    for role in prefs.get("target_roles", []):
        if any(w in jd_lower for w in role.lower().split()):
            score += 8
    for excl in prefs.get("exclude_keywords", []):
        if excl.lower() in jd_lower:
            score -= 20
    score = max(0, min(100, score))
    return {
        "score": score,
        "reasons": ["Keyword-based heuristic match"],
        "matched_keywords": [],
        "missing": [],
        "recommendation": "apply" if score >= 70 else ("maybe" if score >= 50 else "skip")
    }


# ── Career Intelligence Engine ────────────────────────────────
def analyze_career_paths(prefs: dict, api_key: str) -> dict:
    if not api_key:
        return _mock_career_intel(prefs)

    prompt = f"""You are a strategic career advisor with deep market knowledge. Analyze this profile and output career intelligence.

PROFILE:
- Name: {prefs.get('name')}
- Current role: {prefs.get('current_role', 'Not specified')}
- Experience: {prefs.get('experience_years')} years
- Skills: {prefs.get('keywords')}
- Industry: {prefs.get('industry', 'General')}
- Target roles: {prefs.get('target_roles')}
- Target salary: {prefs.get('min_salary_lpa')}-{prefs.get('max_salary_lpa')} LPA
- Location: {prefs.get('locations')}
- Education: {prefs.get('education', 'Not specified')}
- Resume summary: {prefs.get('resume_text', '')[:600]}

Respond ONLY with valid JSON (no markdown):
{{
  "career_paths": [
    {{
      "title": "Path name",
      "category": "Lateral | Upward | Pivot",
      "success_probability": <integer 40-95>,
      "time_to_achieve": "e.g. 3-6 months",
      "salary_year1": <integer LPA>,
      "salary_year3": <integer LPA>,
      "salary_year5": <integer LPA>,
      "skill_gaps": ["gap1", "gap2"],
      "required_skills": ["skill1", "skill2"],
      "recommended_certifications": ["cert1"],
      "companies_hiring": ["company1", "company2"],
      "why_fit": "1-2 sentence explanation",
      "action_priority": <1-5, 1=highest>
    }}
  ],
  "ats_keywords_missing": ["kw1", "kw2", "kw3"],
  "market_demand": "High | Medium | Low",
  "competitive_insight": "2-3 sentence market reality check",
  "immediate_actions": ["action1", "action2", "action3"]
}}

Generate exactly 5 career paths, ordered by success_probability descending."""

    try:
        return _parse_json(_call_groq(prompt, api_key, max_tokens=2000))
    except Exception:
        return _mock_career_intel(prefs)


def _mock_career_intel(prefs: dict) -> dict:
    roles = prefs.get("target_roles", ["Analyst", "Manager"])
    base_sal = prefs.get("min_salary_lpa", 10)
    return {
        "career_paths": [
            {
                "title": roles[0] if roles else "Senior Analyst",
                "category": "Upward",
                "success_probability": 82,
                "time_to_achieve": "3-6 months",
                "salary_year1": base_sal + 5,
                "salary_year3": base_sal + 10,
                "salary_year5": base_sal + 18,
                "skill_gaps": ["Advanced Excel", "SQL"],
                "required_skills": prefs.get("keywords", [])[:4],
                "recommended_certifications": ["CFA Level 1", "PMP"],
                "companies_hiring": ["Deloitte", "KPMG", "EY", "Flipkart"],
                "why_fit": "Strong match with your current skill trajectory.",
                "action_priority": 1
            },
            {
                "title": roles[1] if len(roles) > 1 else "Business Analyst",
                "category": "Lateral",
                "success_probability": 71,
                "time_to_achieve": "2-4 months",
                "salary_year1": base_sal + 3,
                "salary_year3": base_sal + 9,
                "salary_year5": base_sal + 15,
                "skill_gaps": ["Agile", "Product thinking"],
                "required_skills": prefs.get("keywords", [])[:3],
                "recommended_certifications": ["CSPO", "Six Sigma"],
                "companies_hiring": ["Amazon", "Microsoft", "Swiggy"],
                "why_fit": "Leverages analytical background in a growing market.",
                "action_priority": 2
            },
        ],
        "ats_keywords_missing": ["Python", "Tableau", "Agile", "KPIs"],
        "market_demand": "High",
        "competitive_insight": "Market demand is strong. Add API key for personalized analysis.",
        "immediate_actions": ["Upload resume for deeper analysis", "Add Groq API key", "Set target salary"]
    }


# ── Resume ATS Optimizer ──────────────────────────────────────
def analyze_resume_ats(resume_text: str, prefs: dict, api_key: str) -> dict:
    if not api_key:
        return _mock_ats(prefs)

    prompt = f"""You are an ATS expert and senior recruiter. Analyze this resume deeply.

TARGET ROLE: {prefs.get('target_roles', ['Analyst'])}
EXPERIENCE: {prefs.get('experience_years')} years
INDUSTRY: {prefs.get('industry', 'General')}

RESUME:
{resume_text[:2500]}

Respond ONLY with valid JSON:
{{
  "ats_score": <integer 0-100>,
  "percentile": <integer, e.g. 72 means top 28%>,
  "strengths": ["strength1", "strength2", "strength3"],
  "critical_gaps": ["gap1", "gap2"],
  "missing_keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],
  "formatting_issues": ["issue1", "issue2"],
  "impact_statements_weak": ["original weak bullet", "another weak line"],
  "impact_statements_improved": ["stronger version", "stronger version"],
  "recommended_summary": "2-3 sentence professional summary optimized for ATS",
  "overall_verdict": "1 sentence honest assessment",
  "quick_wins": ["quick fix 1", "quick fix 2", "quick fix 3"]
}}"""

    try:
        return _parse_json(_call_groq(prompt, api_key, max_tokens=1500))
    except Exception:
        return _mock_ats(prefs)


def _mock_ats(prefs: dict) -> dict:
    return {
        "ats_score": 58,
        "percentile": 42,
        "strengths": ["Relevant experience", "Quantified achievements", "Clear structure"],
        "critical_gaps": ["Missing action verbs", "No metrics in last 2 roles", "Skills section incomplete"],
        "missing_keywords": ["KPI", "Stakeholder management", "Data-driven", "Cross-functional"],
        "formatting_issues": ["Use standard section headers", "Avoid tables in resume"],
        "impact_statements_weak": ["Responsible for financial reporting"],
        "impact_statements_improved": ["Led monthly financial reporting for ₹50Cr portfolio, reducing close time by 2 days"],
        "recommended_summary": f"Results-driven {prefs.get('experience_years', 3)}-year professional with expertise in {', '.join(prefs.get('keywords', ['finance'])[:3])}. Add Groq API key for personalized analysis.",
        "overall_verdict": "Resume needs optimization. Add Groq API key for detailed recommendations.",
        "quick_wins": ["Add metrics to every bullet", "Include ATS keywords from job descriptions", "Add a skills summary section"]
    }


# ── Application Content Generator ────────────────────────────
def generate_application_content(job: dict, prefs: dict, content_type: str, api_key: str) -> str:
    templates = {
        "cover_letter": _gen_cover_letter,
        "cold_email": _gen_cold_email,
        "referral_message": _gen_referral,
        "linkedin_dm": _gen_linkedin_dm,
    }
    gen_fn = templates.get(content_type, _gen_cover_letter)
    return gen_fn(job, prefs, api_key)


def _gen_cover_letter(job, prefs, api_key):
    if not api_key:
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job.get('title')} role at {job.get('company')}.

With {prefs.get('experience_years')} years of experience in {', '.join(prefs.get('keywords', [])[:3])}, I bring a proven track record of delivering results.

[Add Groq API key to generate a fully personalized cover letter]

Best regards,
{prefs.get('name', 'Your Name')}"""

    prompt = f"""Write a compelling, ATS-optimized cover letter (220-260 words).

CANDIDATE: {prefs.get('name')} | {prefs.get('experience_years')} years experience
SKILLS: {prefs.get('keywords')}
RESUME SNIPPET: {prefs.get('resume_text', '')[:400]}

JOB: {job.get('title')} at {job.get('company')}
JD: {job.get('description', '')[:500]}

Rules:
- Open with a strong impact hook (quantified achievement or bold claim)
- Connect 2-3 specific skills directly to JD requirements
- Mention company by name in body
- Close with confident CTA
- NO "I am writing to express my interest" openers
- NO generic fluff
- Output ONLY the letter body"""
    try:
        return _call_groq(prompt, api_key, max_tokens=600)
    except Exception:
        return "Error generating cover letter. Check your API key."


def _gen_cold_email(job, prefs, api_key):
    if not api_key:
        return f"""Subject: {job.get('title')} — {prefs.get('name')}

Hi [Hiring Manager Name],

I noticed the {job.get('title')} role at {job.get('company')} and wanted to reach out directly.

[Add Groq API key for a fully personalized cold email]

Best,
{prefs.get('name', 'Your Name')}"""

    prompt = f"""Write a cold outreach email for a job application. Make it punchy, human, and compelling (150-180 words).

CANDIDATE: {prefs.get('name')} | {prefs.get('experience_years')} yrs | Skills: {prefs.get('keywords')}
JOB: {job.get('title')} at {job.get('company')}

Rules:
- Subject line that gets opened (not "Interested in your role")
- Opening that shows you've researched the company
- One specific achievement with a number
- Clear ask (15-min call / review my profile)
- Format: Subject: [line] then body
- Output ONLY the email"""
    try:
        return _call_groq(prompt, api_key, max_tokens=400)
    except Exception:
        return "Error generating email. Check your API key."


def _gen_referral(job, prefs, api_key):
    if not api_key:
        return f"Hi [Name], I'm applying for {job.get('title')} at {job.get('company')} and would love a referral. [Add API key for personalized message]"

    prompt = f"""Write a referral request message (100-130 words). Professional but warm.

FROM: {prefs.get('name')} ({prefs.get('experience_years')} yrs, {prefs.get('keywords', [])[:3]})
TARGET: {job.get('title')} at {job.get('company')}

Rules:
- Acknowledge the relationship briefly
- Be specific about the role
- Include ONE relevant achievement
- Make it easy to say yes (offer to send resume, JD link)
- Output ONLY the message"""
    try:
        return _call_groq(prompt, api_key, max_tokens=300)
    except Exception:
        return "Error generating referral message."


def _gen_linkedin_dm(job, prefs, api_key):
    if not api_key:
        return f"Hi [Name], I saw the {job.get('title')} opening at {job.get('company')} and think my background in {prefs.get('keywords', ['finance'])[0]} is a strong match. Would love to connect! [Add API key for full message]"

    prompt = f"""Write a LinkedIn DM for job outreach. Keep it under 120 words. Conversational, not salesy.

FROM: {prefs.get('name')} | Skills: {prefs.get('keywords', [])[:3]}
JOB: {job.get('title')} at {job.get('company')}

Rules:
- Start with a genuine connection point (their work, company news)
- One-liner on your relevant experience
- Soft ask (happy to share my profile / would love your perspective)
- NO "I hope this message finds you well"
- Output ONLY the message"""
    try:
        return _call_groq(prompt, api_key, max_tokens=250)
    except Exception:
        return "Error generating LinkedIn DM."


# ── AI Career Coach ───────────────────────────────────────────
def generate_coach_insights(prefs: dict, tracker_data: list, applied_data: list, api_key: str) -> dict:
    total = len(applied_data) + len(tracker_data)
    statuses = {}
    for entry in tracker_data:
        s = entry.get("status", "Applied")
        statuses[s] = statuses.get(s, 0) + 1

    if not api_key:
        return _mock_coach_insights(total, statuses)

    prompt = f"""You are a brutally honest but supportive AI career coach. Analyze this job seeker's activity.

PROFILE:
- Target roles: {prefs.get('target_roles')}
- Experience: {prefs.get('experience_years')} years
- Skills: {prefs.get('keywords')}
- Target salary: {prefs.get('min_salary_lpa')}-{prefs.get('max_salary_lpa')} LPA

ACTIVITY:
- Total applications tracked: {total}
- Status breakdown: {statuses}
- Applied entries: {len(applied_data)}
- Manual tracked: {len(tracker_data)}

Respond ONLY with valid JSON:
{{
  "weekly_score": <integer 0-100>,
  "score_label": "Excellent | Good | Needs Work | Critical",
  "headline_insight": "Single most important insight (max 15 words)",
  "insights": [
    {{"type": "warning|success|info|danger", "title": "insight title", "body": "2-3 sentence actionable insight"}},
    {{"type": "warning|success|info|danger", "title": "insight title", "body": "2-3 sentence actionable insight"}},
    {{"type": "warning|success|info|danger", "title": "insight title", "body": "2-3 sentence actionable insight"}}
  ],
  "focus_roles": ["role1", "role2", "role3"],
  "this_week_actions": ["specific action 1", "specific action 2", "specific action 3"],
  "conversion_rate": <float, response rate estimate 0-1>,
  "benchmark_comparison": "1 sentence comparing to average job seeker"
}}"""

    try:
        return _parse_json(_call_groq(prompt, api_key, max_tokens=800))
    except Exception:
        return _mock_coach_insights(total, statuses)


def _mock_coach_insights(total, statuses):
    interviews = statuses.get("Interview", 0)
    rate = round(interviews / max(total, 1), 2)
    return {
        "weekly_score": min(100, 30 + total * 5),
        "score_label": "Needs Work" if total < 5 else "Good",
        "headline_insight": "Increase application volume to get market feedback faster.",
        "insights": [
            {"type": "info", "title": "Volume is your friend", "body": "Job seekers who apply to 15+ roles/week get first responses 60% faster. You're tracking fewer. Set a daily target of 3-5 applications."},
            {"type": "warning", "title": "Diversify your portals", "body": "Don't rely on a single platform. LinkedIn, Naukri, and Instahyre reach different hiring managers. Use the Job Discovery feature."},
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
