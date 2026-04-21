import os, json, re
import streamlit as st


def _call_groq(prompt: str, api_key: str) -> str:
    """Call Groq Llama 3.1 for fast inference."""
    import urllib.request
    payload = json.dumps({
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
        "temperature": 0.3,
    }).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def score_job(job: dict, prefs: dict, api_key: str) -> dict:
    """
    Returns {score: int, reasons: list, matched_keywords: list, missing: list}
    """
    jd = f"{job.get('title','')} {job.get('description','')}"

    if api_key:
        prompt = f"""
You are an expert FP&A recruiter. Score how well this job matches the candidate.

CANDIDATE PROFILE:
- Name: {prefs.get('name')}
- Target roles: {prefs.get('target_roles')}
- Experience: {prefs.get('experience_years')} years
- Key skills: {prefs.get('keywords')}
- Salary range: {prefs.get('min_salary_lpa')}-{prefs.get('max_salary_lpa')} LPA
- Preferred locations: {prefs.get('locations')}
- Exclude if JD contains: {prefs.get('exclude_keywords')}

JOB:
Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location','')}
Salary: {job.get('salary','')}
Description: {job.get('description','')[:800]}

Respond ONLY with valid JSON, no markdown:
{{
  "score": <0-100 integer>,
  "reasons": ["reason1", "reason2"],
  "matched_keywords": ["kw1", "kw2"],
  "missing": ["gap1"],
  "recommendation": "apply" | "skip" | "maybe"
}}
"""
        try:
            raw = _call_groq(prompt, api_key)
            raw = raw.strip().strip("```json").strip("```").strip()
            return json.loads(raw)
        except Exception as e:
            pass  # fall through to heuristic
    # Heuristic fallback
    score =    40
    matched = []
    missing = []
    jd_lower = jd.lower()

    if "fp&a" in jd_lower:
        score +=    15

    if "finance" in jd_lower:
        score +=    10

    if "analyst" in jd_lower:
        score +=    5

    if "developer" in jd_lower or "engineer" in jd_lower:
        score -=    15

    score = max(0, min(100, score))

    rec = "apply" if score >= 70 else ("maybe" if score >= 50 else "skip")

    return {
        "score": score,
        "reasons": [f"Matched {len(matched)} keywords"],
        "matched_keywords": matched,
        "missing": missing[:4],
        "recommendation": rec
    }

def generate_cover_letter(job: dict, prefs: dict, template: str, api_key: str) -> str:
    """Generate a personalised cover letter for the job."""
    if not api_key:
        return template.replace("{COMPANY}", job.get("company","[Company]")).replace("{ROLE}", job.get("title","[Role]"))

    prompt = f"""
Write a concise, punchy cover letter (200-250 words) for this job application.

CANDIDATE: {prefs.get('name')}
EXPERIENCE: {prefs.get('experience_years')} years in FP&A, FMCG supply chain finance
KEY STRENGTHS: {prefs.get('keywords')}
TEMPLATE/STYLE GUIDE: {template[:400] if template else 'Professional, direct, FP&A-focused. Lead with impact metric. No fluff.'}

JOB:
Role: {job.get('title')}
Company: {job.get('company')}
JD snippet: {job.get('description','')[:500]}

Rules:
- Open with one strong impact statement (e.g. £60M portfolio, Finance Director influence)
- Connect 2-3 specific skills to JD requirements
- Close with a clear CTA
- No "I am writing to express my interest" openers
- Output ONLY the letter body, no subject line
"""
    try:
        return _call_groq(prompt, api_key)
    except:
        return f"Dear Hiring Manager,\n\nI am excited to apply for the {job.get('title')} role at {job.get('company')}...\n\nBest regards,\n{prefs.get('name')}"
