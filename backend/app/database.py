import sqlite3
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.app.config import SQLITE_DB_PATH, log_event

def get_connection():
    conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # 2. Consent Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_consent (
        user_id TEXT PRIMARY KEY,
        terms_accepted INTEGER NOT NULL,
        consented_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 3. User Resumes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_resumes (
        user_id TEXT PRIMARY KEY,
        filename TEXT,
        extracted_data_json TEXT NOT NULL,
        uploaded_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 4. User GitHub Integrations & Repositories
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_github (
        user_id TEXT PRIMARY KEY,
        github_handle TEXT NOT NULL,
        selected_repos_json TEXT NOT NULL,
        evidence_summary_json TEXT,
        analyzed_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 5. User Skills (Evidence Triangulation)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_skills (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        skill_name TEXT NOT NULL,
        self_level TEXT,
        evidence_status TEXT NOT NULL, -- VERIFIED, PARTIAL, NOT_VERIFIED
        final_level TEXT NOT NULL,     -- Beginner, Developing, Intermediate, Advanced
        confidence TEXT NOT NULL,      -- High, Medium, Low
        evidence_json TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(user_id, skill_name),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 6. User Technical Assessments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_assessments (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        skill_name TEXT NOT NULL,
        question_id TEXT NOT NULL,
        question_type TEXT NOT NULL,
        student_answer TEXT NOT NULL,
        is_correct INTEGER NOT NULL,
        score INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 7. User Roadmaps & Active Target Role
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_roadmaps (
        user_id TEXT PRIMARY KEY,
        target_role TEXT NOT NULL,
        roadmap_nodes_json TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
    log_event("DATABASE", "Database initialized and verified.")

# Helper queries
def create_user(email: str, password_hash: str, full_name: str) -> Dict[str, Any]:
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (id, email, password_hash, full_name, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, email.lower().strip(), password_hash, full_name.strip(), now)
    )
    conn.commit()
    conn.close()
    log_event("AUTH", f"Created user {email} (ID: {user_id})")
    return {"id": user_id, "email": email, "full_name": full_name, "created_at": now}

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, full_name, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def record_consent(user_id: str, accepted: bool) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO user_consent (user_id, terms_accepted, consented_at) VALUES (?, ?, ?)",
        (user_id, 1 if accepted else 0, now)
    )
    conn.commit()
    conn.close()
    log_event("AUTH", f"User {user_id} consent recorded: {accepted}")
    return accepted

def get_user_consent(user_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT terms_accepted FROM user_consent WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return bool(row and row["terms_accepted"] == 1)

def save_user_resume_data(user_id: str, filename: str, data: Dict[str, Any]):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO user_resumes (user_id, filename, extracted_data_json, uploaded_at) VALUES (?, ?, ?, ?)",
        (user_id, filename, json.dumps(data), now)
    )
    conn.commit()
    conn.close()
    log_event("RESUME", f"Saved resume for user {user_id}")

def get_user_resume_data(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_resumes WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "filename": row["filename"],
            "data": json.loads(row["extracted_data_json"]),
            "uploaded_at": row["uploaded_at"]
        }
    return None

def save_user_github(user_id: str, github_handle: str, selected_repos: List[str], evidence_summary: Dict[str, Any]):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO user_github (user_id, github_handle, selected_repos_json, evidence_summary_json, analyzed_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, github_handle, json.dumps(selected_repos), json.dumps(evidence_summary), now)
    )
    conn.commit()
    conn.close()
    log_event("GITHUB", f"Saved GitHub data for user {user_id} (@{github_handle})")

def get_user_github(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_github WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "github_handle": row["github_handle"],
            "selected_repos": json.loads(row["selected_repos_json"]),
            "evidence_summary": json.loads(row["evidence_summary_json"]) if row["evidence_summary_json"] else {},
            "analyzed_at": row["analyzed_at"]
        }
    return None

def save_user_skill_evidence(user_id: str, skill_name: str, self_level: Optional[str], status: str, final_level: str, confidence: str, evidence: Dict[str, Any]):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    skill_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO user_skills (id, user_id, skill_name, self_level, evidence_status, final_level, confidence, evidence_json, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, skill_name) DO UPDATE SET
            self_level = COALESCE(excluded.self_level, user_skills.self_level),
            evidence_status = excluded.evidence_status,
            final_level = excluded.final_level,
            confidence = excluded.confidence,
            evidence_json = excluded.evidence_json,
            updated_at = excluded.updated_at
    """, (skill_id, user_id, skill_name, self_level, status, final_level, confidence, json.dumps(evidence), now))
    conn.commit()
    conn.close()

def get_user_skills(user_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_skills WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    skills = []
    for r in rows:
        skills.append({
            "skill_name": r["skill_name"],
            "self_level": r["self_level"],
            "evidence_status": r["evidence_status"],
            "final_level": r["final_level"],
            "confidence": r["confidence"],
            "evidence": json.loads(r["evidence_json"]),
            "updated_at": r["updated_at"]
        })
    return skills

def save_assessment_attempt(user_id: str, skill_name: str, question_id: str, q_type: str, answer: str, is_correct: bool, score: int):
    attempt_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_assessments (id, user_id, skill_name, question_id, question_type, student_answer, is_correct, score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (attempt_id, user_id, skill_name, question_id, q_type, answer, 1 if is_correct else 0, score, now))
    conn.commit()
    conn.close()

def get_user_assessment_results(user_id: str, skill_name: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if skill_name:
        cursor.execute("SELECT * FROM user_assessments WHERE user_id = ? AND skill_name = ?", (user_id, skill_name))
    else:
        cursor.execute("SELECT * FROM user_assessments WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_user_roadmap(user_id: str, target_role: str, roadmap_nodes: List[Dict[str, Any]]):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO user_roadmaps (user_id, target_role, roadmap_nodes_json, updated_at) VALUES (?, ?, ?, ?)",
        (user_id, target_role, json.dumps(roadmap_nodes), now)
    )
    conn.commit()
    conn.close()

def get_user_roadmap(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_roadmaps WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "target_role": row["target_role"],
            "roadmap_nodes": json.loads(row["roadmap_nodes_json"]),
            "updated_at": row["updated_at"]
        }
    return None
