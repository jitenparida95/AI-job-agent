"""config.py – Central configuration loader. App runs even if keys are missing."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ─── AI ─────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# Which provider to use (first available wins)
def get_active_ai_provider() -> str:
    if OPENAI_API_KEY:
        return "openai"
    if GROQ_API_KEY:
        return "groq"
    if ANTHROPIC_API_KEY:
        return "anthropic"
    return "mock"

# ─── PAYMENT ────────────────────────────────────────────────
RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
PRO_PRICE_INR: int = int(os.getenv("PRO_PRICE_INR", "499"))

# ─── APP ────────────────────────────────────────────────────
APP_SECRET: str = os.getenv("APP_SECRET", "dev_secret_change_me")
FREE_TRIAL_DAYS: int = int(os.getenv("FREE_TRIAL_DAYS", "7"))
DAILY_FREE_APPLY_LIMIT: int = int(os.getenv("DAILY_FREE_APPLY_LIMIT", "5"))
DAILY_PRO_APPLY_LIMIT: int = int(os.getenv("DAILY_PRO_APPLY_LIMIT", "50"))

# ─── FEATURE FLAGS ──────────────────────────────────────────
AI_ENABLED: bool = bool(OPENAI_API_KEY or GROQ_API_KEY or ANTHROPIC_API_KEY)
PAYMENT_ENABLED: bool = bool(RAZORPAY_KEY_ID or STRIPE_SECRET_KEY)

# ─── JOB PORTALS ────────────────────────────────────────────
SUPPORTED_PORTALS = ["naukri", "linkedin", "instahyre", "foundit", "wellfound", "remotive"]
DEFAULT_PORTALS = ["linkedin", "naukri", "foundit"]
