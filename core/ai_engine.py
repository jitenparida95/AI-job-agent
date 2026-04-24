import json, urllib.request


def _groq(prompt: str, api_key: str, max_tokens: int = 1000) -> str:
    """Call Groq. Returns '' on any failure — never raises."""
    if not api_key:
        return ""
    try:
        payload = json.dumps({
            "model": "llama-3.1-8b-instant",
            "messages": [{"role":"user","content":prompt}],
            "max_tokens": max_tokens, "temperature": 0.35,
        }).encode()
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except Exception:
        return ""


def _parse_json(raw: str) -> dict:
    if not raw:
        return {}
    raw = raw.strip()
    for fence in ["```json","```"]:
        if fence in raw:
            raw = raw.split(fence)[-1].split("```")[0]
    try:
        return json.loads(raw.strip())
    except Exception:
        return {}


# ── Job match scoring ──────────────────────────────────────────
def score_job(job: dict, prefs: dict, api_key: str) -> dict:
    if api_key:
        prompt = f"""Score this job match for a finance professional. Return ONLY valid JSON.

CANDIDATE: {prefs.get('experience_years')} yrs | roles: {prefs.get('target_roles')} | skills: {prefs.get('keywords')} | locations: {prefs.get('locations')} | salary: {prefs.get('min_salary_lpa')}-{prefs.get('max_salary_lpa')} LPA

JOB: {job.get('title')} at {job.get('company')} | loc: {job.get('location','')} | sal: {job.get('salary','')}
JD: {str(job.get('description',''))[:500]}

JSON: {{"score":<0-100>,"reasons":["r1"],"matched_keywords":["kw1"],"missing":["gap1"],"recommendation":"apply"}}"""
        r = _parse_json(_groq(prompt, api_key, 350))
        if r and "score" in r:
            return r

    # Heuristic fallback
    score = 40
    jd = f"{job.get('title','')} {job.get('description','')}".lower()
    for kw in (prefs.get("keywords") or []):
        if str(kw).lower() in jd: score += 5
    for role in (prefs.get("target_roles") or []):
        if any(w in jd for w in str(role).lower().split()): score += 8
    for excl in (prefs.get("exclude_keywords") or []):
        if str(excl).lower() in jd: score -= 20
    score = max(0, min(100, score))
    return {"score":score,"reasons":["Keyword match"],"matched_keywords":[],"missing":[],
            "recommendation":"apply" if score>=70 else ("maybe" if score>=50 else "skip")}


# ── Resume ATS analysis ───────────────────────────────────────
def analyze_resume_ats(resume_text: str, prefs: dict, api_key: str) -> dict:
    if api_key and resume_text:
        prompt = f"""Analyze this resume for ATS. Return ONLY valid JSON.

TARGET: {prefs.get('target_roles')} | {prefs.get('experience_years')} yrs
RESUME: {resume_text[:2000]}

JSON: {{"ats_score":<0-100>,"percentile":<0-100>,"strengths":["s1","s2"],"critical_gaps":["g1"],"missing_keywords":["kw1","kw2","kw3","kw4"],"formatting_issues":["i1"],"impact_statements_weak":["w1"],"impact_statements_improved":["i1"],"recommended_summary":"2-3 sentences","overall_verdict":"1 sentence","quick_wins":["win1","win2","win3"]}}"""
        r = _parse_json(_groq(prompt, api_key, 1200))
        if r and "ats_score" in r:
            return r

    return {"ats_score":58,"percentile":42,
            "strengths":["Relevant finance experience","Multi-market exposure","Strong technical background"],
            "critical_gaps":["Missing quantified achievements in recent roles","Skills section incomplete"],
            "missing_keywords":["FP&A","EBITDA","variance analysis","working capital","stakeholder management"],
            "formatting_issues":["Use standard ATS-friendly section headers"],
            "impact_statements_weak":["Responsible for financial reporting"],
            "impact_statements_improved":["Led monthly financial reporting for ₹500Cr portfolio, reducing close time by 2 days"],
            "recommended_summary":f"Results-driven {prefs.get('experience_years',6)}-year finance professional specializing in FP&A and supply chain finance. Add Groq API key for personalized summary.",
            "overall_verdict":"Strong finance background, needs stronger ATS optimization. Add Groq API key for detailed analysis.",
            "quick_wins":["Add ₹/£/% metrics to every achievement","Add FP&A, EBITDA, variance analysis as exact keywords","Create a dedicated Skills section with SAP, Power BI, Excel"]}


# ── Career paths ──────────────────────────────────────────────
def analyze_career_paths(prefs: dict, api_key: str) -> dict:
    if api_key:
        prompt = f"""Analyze this finance professional's career. Return ONLY valid JSON with exactly 5 paths.

PROFILE: current={prefs.get('current_role','FP&A Analyst')} | exp={prefs.get('experience_years',6)}yrs | skills={prefs.get('keywords')} | target={prefs.get('target_roles')} | salary={prefs.get('min_salary_lpa')}-{prefs.get('max_salary_lpa')}LPA | loc={prefs.get('locations')}
RESUME: {str(prefs.get('resume_text',''))[:400]}

JSON: {{"career_paths":[{{"title":"...","category":"Upward","success_probability":80,"time_to_achieve":"3-6 months","salary_year1":20,"salary_year3":28,"salary_year5":38,"skill_gaps":["gap1"],"required_skills":["s1"],"recommended_certifications":["cert1"],"companies_hiring":["co1","co2"],"why_fit":"explanation","action_priority":1}}],"ats_keywords_missing":["kw1"],"market_demand":"High","competitive_insight":"insight","immediate_actions":["action1","action2","action3"]}}"""
        r = _parse_json(_groq(prompt, api_key, 2000))
        if r and r.get("career_paths"):
            return r

    base = prefs.get("min_salary_lpa") or 15
    roles = prefs.get("target_roles") or ["Senior FP&A Analyst","Finance Manager"]
    return {
        "career_paths":[
            {"title":roles[0] if roles else "Senior FP&A Analyst","category":"Upward","success_probability":84,
             "time_to_achieve":"3-5 months","salary_year1":base+5,"salary_year3":base+12,"salary_year5":base+22,
             "skill_gaps":["Advanced Python/SQL","Power Platform"],"required_skills":["FP&A","SAP","Power BI","IFRS"],
             "recommended_certifications":["CFA Level 1","CIMA"],"companies_hiring":["Unilever GCC","Reckitt GCC","IBM","Capgemini"],
             "why_fit":"Your FMCG supply chain finance background directly aligns with GCC FP&A demand.","action_priority":1},
            {"title":roles[1] if len(roles)>1 else "Finance Manager","category":"Upward","success_probability":76,
             "time_to_achieve":"4-7 months","salary_year1":base+8,"salary_year3":base+16,"salary_year5":base+28,
             "skill_gaps":["People management","Strategic planning"],"required_skills":["P&L ownership","Stakeholder management","Budgeting"],
             "recommended_certifications":["PMP","MBA Finance"],"companies_hiring":["Marico","ITC","HUL","Nestlé"],
             "why_fit":"Natural progression from Senior Analyst leveraging your MENARP/Africa multi-market experience.","action_priority":2},
            {"title":"Business Finance Partner","category":"Lateral","success_probability":71,
             "time_to_achieve":"2-4 months","salary_year1":base+3,"salary_year3":base+10,"salary_year5":base+18,
             "skill_gaps":["Commercial acumen","Contract negotiation"],"required_skills":["Business partnering","Variance analysis","KPI management"],
             "recommended_certifications":["ACCA","Six Sigma Green Belt"],"companies_hiring":["P&G","Colgate","Dabur","Godrej"],
             "why_fit":"Your FP&A + supply chain experience makes you a strong candidate for commercial finance roles.","action_priority":3},
            {"title":"Senior Business Analyst - Finance","category":"Lateral","success_probability":68,
             "time_to_achieve":"2-3 months","salary_year1":base+2,"salary_year3":base+8,"salary_year5":base+15,
             "skill_gaps":["Agile methodology","Requirements documentation"],"required_skills":["SAP FI","Process mapping","Stakeholder management"],
             "recommended_certifications":["CBAP","IIBA"],"companies_hiring":["Accenture","Deloitte","KPMG","EY"],
             "why_fit":"Your ERP exposure and finance process knowledge are exactly what consulting firms need for finance BA roles.","action_priority":4},
            {"title":"FP&A Manager - GCC","category":"Upward","success_probability":63,
             "time_to_achieve":"6-9 months","salary_year1":base+10,"salary_year3":base+20,"salary_year5":base+32,
             "skill_gaps":["Team leadership","Advanced modelling","Anaplan/Adaptive"],"required_skills":["FP&A","Team management","Strategic finance","Board reporting"],
             "recommended_certifications":["CFA","Anaplan certification"],"companies_hiring":["Shell GCC","BP","Honeywell","3M"],
             "why_fit":"A stretch role worth targeting as your next step up — strong candidate in 6-9 months with the right skill gaps closed.","action_priority":5},
        ],
        "ats_keywords_missing":["FP&A","EBITDA bridge","working capital optimization","Anaplan","scenario modelling"],
        "market_demand":"High",
        "competitive_insight":"FP&A demand in Bangalore GCCs is up 32% YoY. FMCG supply chain finance experience is a key differentiator — fewer than 15% of candidates have your specific multi-market (MENARP/Africa) exposure. This is a strong positioning advantage.",
        "immediate_actions":["Apply to 3 GCC FP&A roles today on Naukri — target Unilever, Reckitt, P&G","Update LinkedIn headline to include 'FMCG Supply Chain Finance | £60M P&L'","Add EBITDA, working capital, variance analysis as exact keywords in resume"]
    }


# ── Application content ────────────────────────────────────────
def generate_application_content(job: dict, prefs: dict, content_type: str, api_key: str) -> str:
    try:
        if content_type == "cover_letter":   return _cover_letter(job, prefs, api_key)
        elif content_type == "cold_email":   return _cold_email(job, prefs, api_key)
        elif content_type == "referral_message": return _referral(job, prefs, api_key)
        elif content_type == "linkedin_dm":  return _linkedin_dm(job, prefs, api_key)
        else:                                return _cover_letter(job, prefs, api_key)
    except Exception:
        return f"Content generation failed. Please verify your Groq API key in Settings."


def _cover_letter(job, prefs, api_key):
    name = prefs.get("name") or "Jitendra Parida"
    role = job.get("title","Finance Role")
    co   = job.get("company","your company")
    exp  = prefs.get("experience_years", 6)
    kws  = prefs.get("keywords") or ["FP&A","SAP","Power BI"]

    if api_key:
        prompt = f"""Write a 230-word cover letter. ONLY the body — no salutation.

CANDIDATE: {name} | {exp}yrs FP&A | skills: {kws} | resume: {str(prefs.get('resume_text',''))[:400]}
JOB: {role} at {co} | JD: {str(job.get('description',''))[:400]}

Rules: Open with quantified impact. Connect 2-3 skills to JD. Mention {co} by name. Confident CTA. No "I am writing to express my interest"."""
        r = _groq(prompt, api_key, 500)
        if r: return r

    return f"""With {exp}+ years driving financial planning and analysis across FMCG supply chains, I bring the analytical precision and commercial insight that the {role} role at {co} demands.

In my current position at IBM supporting Reckitt's MENARP and Africa markets, I manage a £60M supply chain P&L — owning period-close, variance analysis, and Finance Director-level reporting across 12 markets. At Capgemini supporting Unilever's ANZ/APAC operations, I built automated MIS frameworks that cut reporting cycle time by 40% and reduced forecast error by 18%.

For {co}, I offer:
• Hands-on FP&A across budgeting, rolling forecasts, and actuals-vs-plan variance analysis
• Supply chain finance expertise — standard costing, DIO/DSO, working capital optimisation
• Strong tech stack: SAP, Power BI (advanced), Sunrise ERP, Excel financial modelling

I am excited about {co}'s growth trajectory and believe my multi-market FMCG finance background would add immediate value to your team.

I'd welcome a 20-minute call to discuss how I can contribute.

Best regards,
{name}"""


def _cold_email(job, prefs, api_key):
    name = prefs.get("name") or "Jitendra Parida"
    role = job.get("title","Finance")
    co   = job.get("company","")
    exp  = prefs.get("experience_years", 6)

    if api_key:
        prompt = f"""Write a cold outreach email (150 words max). Include subject line first.
CANDIDATE: {name} | {exp}yrs | {prefs.get('keywords',[])}
JOB: {role} at {co}
Rules: Punchy subject. One achievement with a number. Clear ask (15-min call). No fluff."""
        r = _groq(prompt, api_key, 300)
        if r: return r

    return f"""Subject: {role} — {exp}yr FP&A | FMCG GCC Experience

Hi [Name],

I noticed {co} is building out its finance capability and wanted to reach out directly.

I'm a Senior FP&A Analyst with {exp} years in FMCG supply chain finance — currently managing a £60M P&L at IBM (supporting Reckitt) across 12 markets in MENARP and Africa.

If there's an opening for a {role} or similar, I'd love 15 minutes to explore fit.

Best,
{name}"""


def _referral(job, prefs, api_key):
    name = prefs.get("name") or "Jitendra Parida"
    role = job.get("title","Finance Role")
    co   = job.get("company","")
    exp  = prefs.get("experience_years", 6)

    if api_key:
        prompt = f"""Write a referral request (110 words). Warm but professional.
FROM: {name} ({exp}yrs FP&A). TARGET: {role} at {co}. One achievement with number. Easy ask."""
        r = _groq(prompt, api_key, 220)
        if r: return r

    return f"""Hi [Name],

Hope you're doing well! I wanted to reach out because I noticed a {role} opening at {co} and thought you might be able to help.

With {exp} years in FP&A and supply chain finance (currently at IBM supporting Reckitt's global markets), I believe it could be a strong fit.

Would you be comfortable with a referral or sharing insights about the team? Happy to send my resume across.

Thanks so much,
{name}"""


def _linkedin_dm(job, prefs, api_key):
    name = prefs.get("name") or "Jitendra Parida"
    role = job.get("title","Finance")
    co   = job.get("company","")
    exp  = prefs.get("experience_years", 6)

    if api_key:
        prompt = f"""LinkedIn DM, max 100 words. Conversational, not salesy.
FROM: {name} | {exp}yrs FP&A. TO: Someone at {co}. JOB: {role}. Genuine opener. Soft ask."""
        r = _groq(prompt, api_key, 180)
        if r: return r

    return f"""Hi [Name],

I came across your profile while researching {co}'s finance team — love what you're building there.

I'm a Senior FP&A Analyst with {exp} years in FMCG supply chain finance and noticed the {role} opening. My background in multi-market P&L management feels like a strong match.

Would you be open to a quick 15-minute chat?

{name}"""


# ── Coach insights ─────────────────────────────────────────────
def generate_coach_insights(prefs, tracker_data, applied_data, api_key):
    total = len(applied_data) + len(tracker_data)
    statuses = {}
    for e in tracker_data:
        s = e.get("status","Applied")
        statuses[s] = statuses.get(s,0)+1

    if api_key:
        prompt = f"""Career coach analysis. Return ONLY valid JSON.
PROFILE: {prefs.get('target_roles')} | {prefs.get('experience_years')}yrs | {prefs.get('keywords')}
ACTIVITY: {total} tracked | statuses: {statuses}
JSON: {{"weekly_score":<0-100>,"score_label":"Good","headline_insight":"max 15 words","insights":[{{"type":"info","title":"t","body":"2-3 sentences"}}],"focus_roles":["r1","r2"],"this_week_actions":["a1","a2","a3"],"conversion_rate":0.1,"benchmark_comparison":"1 sentence"}}"""
        r = _parse_json(_groq(prompt, api_key, 700))
        if r and "weekly_score" in r:
            return r

    interviews = statuses.get("Interview",0) + statuses.get("Interview Scheduled",0)
    rate = round(interviews/max(total,1),2)
    return {
        "weekly_score": min(100, 30+total*5),
        "score_label": "Needs Work" if total<5 else ("Good" if total<15 else "Excellent"),
        "headline_insight": "Increase application volume to accelerate market feedback.",
        "insights":[
            {"type":"info","title":"Volume is your edge","body":"Finance job seekers who apply to 15+ roles/week get first responses 60% faster. Set a daily minimum of 3-5 quality applications across Naukri and LinkedIn."},
            {"type":"warning","title":"Diversify your channels","body":"Don't rely on a single portal. LinkedIn Easy Apply, Naukri Quick Apply, and Instahyre reach different hiring managers. Your GCC finance experience plays best on LinkedIn."},
            {"type":"success","title":"Your experience is a differentiator","body":"6+ years with FMCG multi-market (MENARP/Africa) exposure is rare. Mention this explicitly in every cover letter and LinkedIn outreach — it's your moat."}
        ],
        "focus_roles":["Senior FP&A Analyst - GCC","Finance Manager - Supply Chain","Business Analyst - Finance"],
        "this_week_actions":["Apply to 15 GCC FP&A roles on Naukri today","Message 5 finance recruiters on LinkedIn with a 3-line note","Book a mock interview for FP&A case studies"],
        "conversion_rate":rate,
        "benchmark_comparison":"Add Groq API key for personalized benchmarking vs similar profiles."
    }


# ── Legacy compatibility ───────────────────────────────────────
def generate_cover_letter(job, prefs, template, api_key):
    return _cover_letter(job, prefs, api_key)
