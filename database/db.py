"""database/db.py – Lightweight SQLite persistence layer."""
import sqlite3
import json
import hashlib
import os
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any, List

DB_PATH = Path(__file__).parent.parent / "data" / "careeros.db"
DB_PATH.parent.mkdir(exist_ok=True)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables if they don't exist."""
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT    UNIQUE NOT NULL,
            password_hash TEXT  NOT NULL,
            name        TEXT    DEFAULT '',
            plan        TEXT    DEFAULT 'free',
            trial_start TEXT    DEFAULT NULL,
            created_at  TEXT    DEFAULT (datetime('now')),
            prefs       TEXT    DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS applications (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            job_title   TEXT,
            company     TEXT,
            portal      TEXT,
            status      TEXT    DEFAULT 'applied',
            applied_at  TEXT    DEFAULT (datetime('now')),
            notes       TEXT    DEFAULT '',
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS resumes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            original    TEXT,
            optimized   TEXT,
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS daily_usage (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            action      TEXT    NOT NULL,
            usage_date  TEXT    DEFAULT (date('now')),
            count       INTEGER DEFAULT 0,
            UNIQUE(user_id, action, usage_date),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)


# ─── USER CRUD ──────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(email: str, password: str, name: str = "") -> Optional[Dict]:
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users (email, password_hash, name, trial_start) VALUES (?,?,?,?)",
                (email.lower().strip(), hash_password(password), name, datetime.now().isoformat())
            )
        return get_user_by_email(email)
    except sqlite3.IntegrityError:
        return None  # Email already exists


def get_user_by_email(email: str) -> Optional[Dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
        ).fetchone()
    return dict(row) if row else None


def authenticate_user(email: str, password: str) -> Optional[Dict]:
    user = get_user_by_email(email)
    if user and user["password_hash"] == hash_password(password):
        return user
    return None


def update_user(user_id: int, **kwargs) -> None:
    if not kwargs:
        return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [user_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE users SET {sets} WHERE id=?", vals)


def upgrade_user_to_pro(user_id: int) -> None:
    update_user(user_id, plan="pro")


def get_user_prefs(user_id: int) -> Dict:
    with get_conn() as conn:
        row = conn.execute("SELECT prefs FROM users WHERE id=?", (user_id,)).fetchone()
    if row:
        try:
            return json.loads(row["prefs"] or "{}")
        except Exception:
            return {}
    return {}


def save_user_prefs(user_id: int, prefs: Dict) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET prefs=? WHERE id=?",
            (json.dumps(prefs), user_id)
        )


# ─── APPLICATIONS ───────────────────────────────────────────

def log_application(user_id: int, job_title: str, company: str,
                    portal: str = "", status: str = "applied", notes: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO applications (user_id,job_title,company,portal,status,notes) VALUES (?,?,?,?,?,?)",
            (user_id, job_title, company, portal, status, notes)
        )
    _increment_daily_usage(user_id, "apply")


def get_applications(user_id: int) -> List[Dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM applications WHERE user_id=? ORDER BY applied_at DESC",
            (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def update_application_status(app_id: int, user_id: int, status: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE applications SET status=? WHERE id=? AND user_id=?",
            (status, app_id, user_id)
        )


# ─── RESUMES ────────────────────────────────────────────────

def save_resume(user_id: int, original: str, optimized: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO resumes (user_id, original, optimized) VALUES (?,?,?)",
            (user_id, original, optimized)
        )


def get_latest_resume(user_id: int) -> Optional[Dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM resumes WHERE user_id=? ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        ).fetchone()
    return dict(row) if row else None


# ─── DAILY USAGE / RATE LIMITING ────────────────────────────

def _increment_daily_usage(user_id: int, action: str) -> None:
    today = date.today().isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO daily_usage (user_id, action, usage_date, count)
            VALUES (?,?,?,1)
            ON CONFLICT(user_id, action, usage_date) DO UPDATE SET count = count + 1
        """, (user_id, action, today))


def get_daily_usage(user_id: int, action: str) -> int:
    today = date.today().isoformat()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT count FROM daily_usage WHERE user_id=? AND action=? AND usage_date=?",
            (user_id, action, today)
        ).fetchone()
    return row["count"] if row else 0


# Initialise on import
init_db()
