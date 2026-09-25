import os
import json
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.app.config import DATABASE_URL, SQLITE_DB_PATH, log_event
from backend.app.models import (
    Base, User, Profile, Consent, Resume, GitHubAccount, GitHubRepository,
    Skill, UserSkill, SkillEvidence, Assessment, AssessmentQuestion,
    AssessmentAttempt, AssessmentAnswer, AssessmentResult, Roadmap,
    RoadmapNode, UserProgress, LearningResource, Job, JobSkill, JobMatch, Application
)

# Connect to PostgreSQL or SQLite based on DATABASE_URL
if DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres"):
    pg_url = DATABASE_URL
    if pg_url.startswith("postgres://"):
        pg_url = pg_url.replace("postgres://", "postgresql://", 1)
    
    # Ensure compatible driver
    try:
        engine = create_engine(pg_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
    except Exception:
        # Fallback to psycopg2 driver
        if "postgresql+psycopg2://" not in pg_url:
            pg_url = pg_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            engine = create_engine(pg_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
        else:
            raise
else:
    # SQLite fallback
    db_path = Path(SQLITE_DB_PATH).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DATA_DIR = Path(__file__).resolve().parent / "data"

def seed_initial_data(db: Session):
    """Populates canonical reference data (Skills, Questions, Resources, Jobs) if empty."""
    # 1. Seed Skills from taxonomy
    if db.query(Skill).count() == 0:
        roles_file = DATA_DIR / "roles_and_skills.json"
        if roles_file.exists():
            with open(roles_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                skills_data = data.get("skills", {})
                prereqs_data = data.get("prerequisites", [])
                
                # Build prereq lookup
                prereq_map = {}
                for p in prereqs_data:
                    prereq_map.setdefault(p["to"], []).append(p["from"])
                    
                for name, meta in skills_data.items():
                    s = Skill(
                        name=name,
                        category=meta.get("category", "General"),
                        tier=meta.get("tier", "Core"),
                        description=f"{name} technical competency",
                        prerequisites_json=json.dumps(prereq_map.get(name, []))
                    )
                    db.add(s)
            db.commit()
            log_event("DATABASE", "Seeded canonical skills table.")

    # 2. Seed Questions
    if db.query(AssessmentQuestion).count() == 0:
        q_file = DATA_DIR / "assessment_bank.json"
        if q_file.exists():
            with open(q_file, "r", encoding="utf-8") as f:
                questions = json.load(f).get("questions", [])
                for q in questions:
                    ans = q.get("correct_answer", "A")
                    c_idx = "ABCD".find(ans[0].upper()) if isinstance(ans, str) and ans else q.get("correct_index", 0)
                    if c_idx < 0:
                        c_idx = 0
                    aq = AssessmentQuestion(
                        id=q["id"],
                        skill_name=q["skill"],
                        question_type=q["type"],
                        difficulty=q.get("level", q.get("difficulty", "Intermediate")),
                        question_text=q["question"],
                        code_snippet=q.get("code"),
                        options_json=json.dumps(q.get("options", [])),
                        correct_index=c_idx,
                        explanation=q.get("explanation")
                    )
                    db.add(aq)
            db.commit()
            log_event("DATABASE", "Seeded assessment question bank.")

    # 3. Seed Learning Resources
    if db.query(LearningResource).count() == 0:
        res_file = DATA_DIR / "verified_resources.json"
        if res_file.exists():
            with open(res_file, "r", encoding="utf-8") as f:
                res_dict = json.load(f).get("resources", {})
                for skill_name, r_list in res_dict.items():
                    for r in r_list:
                        lr = LearningResource(
                            skill_name=skill_name,
                            title=r["title"],
                            provider=r["provider"],
                            level=r.get("difficulty", "Intermediate"),
                            url=r["url"],
                            resource_type=r.get("type", "Documentation"),
                            estimated_time=r.get("duration", "4-6 Hours"),
                            verified=True
                        )
                        db.add(lr)
            db.commit()
            log_event("DATABASE", "Seeded accredited learning resources.")

    # 4. Seed Jobs
    if db.query(Job).count() == 0:
        jobs_file = DATA_DIR / "sample_jobs.json"
        if jobs_file.exists():
            with open(jobs_file, "r", encoding="utf-8") as f:
                jobs_list = json.load(f).get("jobs", [])
                for j in jobs_list:
                    job = Job(
                        id=j["id"],
                        role_title=j["title"],
                        company_name=j["company"],
                        location=j.get("location", "Bangalore / Remote"),
                        required_skills_json=json.dumps(j.get("required_skills", [])),
                        portal_url=j.get("apply_url", "https://careers.google.com"),
                        provider_source="DatasetJobProvider",
                        is_active=True
                    )
                    db.add(job)
                    for sk in j.get("required_skills", []):
                        db.add(JobSkill(
                            job_id=j["id"],
                            skill_name=sk,
                            is_core=True,
                            required_level="Intermediate"
                        ))
            db.commit()
            log_event("DATABASE", "Seeded sample jobs & requirements.")

from sqlalchemy import text

def init_db():
    """Initializes schema and runs seeding."""
    log_event("DATABASE", f"Initializing tables using engine: {engine.url.drivername}...")
    Base.metadata.create_all(bind=engine)
    
    # Auto-migrate legacy columns if present
    with engine.connect() as conn:
        try:
            conn.execute(text("SELECT is_active FROM users LIMIT 1"))
        except Exception:
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                conn.commit()
            except Exception:
                pass
                
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()
    log_event("DATABASE", "Database schema and tables verified successfully.")
