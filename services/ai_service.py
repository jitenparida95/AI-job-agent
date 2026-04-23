"""services/ai_service.py – AI calls with graceful fallback to mock responses."""
import time
import re
from typing import Optional
import config

# ─── MOCK RESPONSES (used when no API key available) ────────

_MOCK_RESUME = """
PROFESSIONAL SUMMARY
Results-driven professional with a proven track record of delivering impactful outcomes across financial analysis, business strategy, and cross-functional collaboration. Adept at translating data into actionable insights.

SKILLS
• Financial Modeling & Forecasting  • Business Intelligence & Analytics
• Stakeholder Management            • Advanced Excel & Power BI
• SQL & Python for Data Analysis    • Strategic Planning

EXPERIENCE
[Your optimized experience will appear here – add an API key to enable AI rewriting]

EDUCATION
[Your education details]
"""

_MOCK_COVER_LETTER = """Dear Hiring Manager,

I am writing to express my strong interest in this opportunity. With my background in financial analysis and business strategy, I am confident I can add immediate value to your team.

Throughout my career, I have consistently delivered measurable results through data-driven decision-making and cross-functional collaboration. I am excited by the prospect of bringing this expertise to your organization.

I would welcome the opportunity to discuss how my background aligns with your needs.

Best regards,
[Your Name]

---
⚠️ This is a template response. Add your OpenAI/Groq API key in Settings to get AI-personalized content.
"""

_MOCK_COACH_RESPONSES = [
    "Focus on tailoring your resume to each job description using keywords from the posting.",
    "Apply to 10–15 roles per week for best results. Quality applications with personalized cover letters outperform bulk applying.",
    "Follow up 7 days after applying with a brief, professional email to the hiring manager.",
    "Your LinkedIn profile should mirror your resume and include a strong summary section.",
    "Prepare 3 strong STAR-format stories for behavioral interview questions.",
]
_mock_coach_idx = 0


# ─── OPENAI CALLER ──────────────────────────────────────────

def _call_openai(system: str, user: str, max_tokens: int = 1000) -> str:
    try:
        import openai
        client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"OpenAI error: {e}")


# ─── GROQ CALLER ────────────────────────────────────────────

def _call_groq(system: str, user: str, max_tokens: int = 1000) -> str:
    try:
        from groq import Groq
        client = Groq(api_key=config.GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Groq error: {e}")


# ─── ANTHROPIC CALLER ───────────────────────────────────────

def _call_anthropic(system: str, user: str, max_tokens: int = 1000) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        raise RuntimeError(f"Anthropic error: {e}")


# ─── UNIFIED CALL ────────────────────────────────────────────

def call_ai(system: str, user: str, max_tokens: int = 1000,
            fallback: Optional[str] = None) -> tuple[str, bool]:
    """
    Returns (text, is_real_ai).
    Never raises – always returns something useful.
    """
    provider = config.get_active_ai_provider()

    try:
        if provider == "openai":
            return _call_openai(system, user, max_tokens), True
        elif provider == "groq":
            return _call_groq(system, user, max_tokens), True
        elif provider == "anthropic":
            return _call_anthropic(system, user, max_tokens), True
    except Exception:
        pass  # Fall through to mock

    return (fallback or "AI response unavailable. Please add an API key in Settings."), False


# ─── DOMAIN FUNCTIONS ────────────────────────────────────────

def optimize_resume(resume_text: str, job_description: str = "",
                    mode: str = "full") -> tuple[str, bool]:
    system = (
        "You are an expert resume writer. Rewrite the resume to be ATS-optimized, "
        "impactful, and tailored to the job description if provided. "
        "Use strong action verbs. Keep formatting clean with sections in CAPS."
    )
    jd_part = f"\n\nJOB DESCRIPTION:\n{job_description}" if job_description.strip() else ""
    if mode == "targeted":
        system += " Only rewrite the Summary and Skills sections."

    user = f"RESUME:\n{resume_text}{jd_part}"
    return call_ai(system, user, max_tokens=1500, fallback=_MOCK_RESUME)


def generate_cover_letter(resume_text: str, job_description: str = "",
                           company: str = "") -> tuple[str, bool]:
    system = (
        "You are an expert career coach. Write a compelling, personalized cover letter "
        "in a professional yet warm tone. 3 paragraphs max. No fluff."
    )
    user = (
        f"RESUME:\n{resume_text}\n\n"
        f"JOB DESCRIPTION:\n{job_description or 'Not provided'}\n\n"
        f"COMPANY: {company or 'Not specified'}"
    )
    return call_ai(system, user, max_tokens=600, fallback=_MOCK_COVER_LETTER)


def generate_cold_email(resume_text: str, job_description: str = "",
                        company: str = "") -> tuple[str, bool]:
    system = (
        "Write a short, punchy cold outreach email (under 150 words) to get a referral "
        "or interview. Subject line included. Professional and direct."
    )
    user = f"MY BACKGROUND:\n{resume_text[:800]}\n\nROLE/COMPANY: {company or job_description[:200]}"
    fallback = (
        "Subject: Exploring opportunities at [Company]\n\n"
        "Hi [Name],\n\nI came across [Company] and was impressed by [specific thing]. "
        "My background in [your field] aligns well with your team's work.\n\n"
        "Would you be open to a 15-minute call?\n\nBest, [Your Name]"
    )
    return call_ai(system, user, max_tokens=300, fallback=fallback)


def generate_referral_message(resume_text: str, job_description: str = "") -> tuple[str, bool]:
    system = "Write a concise LinkedIn referral request message. Under 100 words. Polite, specific."
    user = f"MY BACKGROUND:\n{resume_text[:500]}\n\nROLE:\n{job_description[:300]}"
    fallback = (
        "Hi [Name], I hope you're well! I noticed [Company] is hiring for [Role] and "
        "thought my background in [field] could be a great fit. "
        "Would you be willing to refer me or share any insights about the role? "
        "I'd really appreciate it! Thanks so much."
    )
    return call_ai(system, user, max_tokens=200, fallback=fallback)


def ask_career_coach(question: str, context: str = "") -> tuple[str, bool]:
    global _mock_coach_idx
    system = (
        "You are an expert AI career coach specialising in the Indian job market. "
        "Give concise, actionable advice. Max 200 words."
    )
    user = f"{context}\n\nQUESTION: {question}" if context else question
    mock = _MOCK_COACH_RESPONSES[_mock_coach_idx % len(_MOCK_COACH_RESPONSES)]
    _mock_coach_idx += 1
    return call_ai(system, user, max_tokens=400, fallback=mock)


def score_job_match(resume_text: str, job_description: str) -> tuple[int, str, bool]:
    """Returns (score 0-100, explanation, is_real_ai)."""
    system = (
        "You are a job matching algorithm. Score how well the resume matches the job description "
        "on a scale of 0-100. Respond ONLY with JSON: {\"score\": N, \"reason\": \"...\"}"
    )
    user = f"RESUME:\n{resume_text[:1000]}\n\nJOB:\n{job_description[:800]}"
    text, real = call_ai(system, user, max_tokens=150, fallback='{"score": 72, "reason": "Good match based on skills alignment."}')
    try:
        import json
        data = json.loads(text)
        return int(data.get("score", 72)), data.get("reason", ""), real
    except Exception:
        # Try extracting a number
        nums = re.findall(r'\b(\d{1,3})\b', text)
        score = int(nums[0]) if nums else 72
        return min(score, 100), text, real
