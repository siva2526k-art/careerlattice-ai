import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Float, Table, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

# 1. USER
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    consent = relationship("Consent", back_populates="user", uselist=False, cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    github_accounts = relationship("GitHubAccount", back_populates="user", cascade="all, delete-orphan")
    user_skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="user", cascade="all, delete-orphan")
    roadmaps = relationship("Roadmap", back_populates="user", cascade="all, delete-orphan")
    user_progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    job_matches = relationship("JobMatch", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")

# 2. PROFILE
class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    headline = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    target_role = Column(String(100), default="Junior Backend Developer")
    years_of_experience = Column(Float, default=0.0)
    education = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    
    user = relationship("User", back_populates="profile")

# 3. CONSENT
class Consent(Base):
    __tablename__ = "consents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    terms_version = Column(String(50), default="v1.0")
    privacy_version = Column(String(50), default="v1.0")
    accepted = Column(Boolean, default=False, nullable=False)
    accepted_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    
    user = relationship("User", back_populates="consent")

# 4. RESUME
class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, default=0)
    extracted_skills_json = Column(Text, nullable=False) # JSON list
    raw_text = Column(Text, nullable=True)
    parsed_data_json = Column(Text, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    
    user = relationship("User", back_populates="resumes")

# 5. GITHUB ACCOUNT
class GitHubAccount(Base):
    __tablename__ = "github_accounts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    github_handle = Column(String(255), nullable=False, index=True)
    access_token = Column(String(255), nullable=True)
    profile_url = Column(String(255), nullable=True)
    connected_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    
    user = relationship("User", back_populates="github_accounts")
    repositories = relationship("GitHubRepository", back_populates="github_account", cascade="all, delete-orphan")

# 6. GITHUB REPOSITORY
class GitHubRepository(Base):
    __tablename__ = "github_repositories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    github_account_id = Column(String(36), ForeignKey("github_accounts.id", ondelete="CASCADE"), nullable=False)
    repo_name = Column(String(255), nullable=False)
    repo_url = Column(String(255), nullable=True)
    is_selected = Column(Boolean, default=True)
    language = Column(String(100), nullable=True)
    stars_count = Column(Integer, default=0)
    manifest_findings_json = Column(Text, nullable=True)
    ast_findings_json = Column(Text, nullable=True)
    analyzed_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    github_account = relationship("GitHubAccount", back_populates="repositories")

# 7. SKILL (Canonical Taxonomy)
class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False)
    tier = Column(String(50), default="Core")
    description = Column(Text, nullable=True)
    prerequisites_json = Column(Text, default="[]") # JSON list of skill names

# 8. USER SKILL
class UserSkill(Base):
    __tablename__ = "user_skills"
    __table_args__ = (UniqueConstraint("user_id", "skill_name", name="uq_user_skill"),)
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(100), nullable=False, index=True)
    self_level = Column(String(50), nullable=True) # Beginner, Developing, Intermediate, Advanced
    evidence_status = Column(String(50), default="NOT_VERIFIED") # VERIFIED, PARTIAL, NOT_VERIFIED
    final_level = Column(String(50), default="Beginner")
    confidence = Column(String(50), default="Low") # High, Medium, Low
    evidence_json = Column(Text, nullable=True, default="{}")
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    
    user = relationship("User", back_populates="user_skills")
    evidence_records = relationship("SkillEvidence", back_populates="user_skill", cascade="all, delete-orphan")

# 9. SKILL EVIDENCE
class SkillEvidence(Base):
    __tablename__ = "skill_evidence"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_skill_id = Column(String(36), ForeignKey("user_skills.id", ondelete="CASCADE"), nullable=False)
    evidence_type = Column(String(50), nullable=False) # RESUME, GITHUB, ASSESSMENT, SELF
    source_reference = Column(String(255), nullable=True)
    details_json = Column(Text, nullable=False) # JSON payload with rationale, files, scores
    recorded_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    user_skill = relationship("UserSkill", back_populates="evidence_records")

# 10. ASSESSMENT
class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    target_level = Column(String(50), default="Intermediate")
    status = Column(String(50), default="COMPLETED") # IN_PROGRESS, COMPLETED, ABANDONED
    total_score = Column(Integer, default=0)
    max_score = Column(Integer, default=10)
    started_at = Column(DateTime(timezone=True), default=get_utc_now)
    completed_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    user = relationship("User", back_populates="assessments")
    attempts = relationship("AssessmentAttempt", back_populates="assessment", cascade="all, delete-orphan")
    result = relationship("AssessmentResult", back_populates="assessment", uselist=False, cascade="all, delete-orphan")

# 11. ASSESSMENT QUESTION
class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_name = Column(String(100), nullable=False, index=True)
    question_type = Column(String(50), nullable=False) # MCQ, ASSERTION_REASON, CODE_OUTPUT, DEBUGGING, SCENARIO, ARCHITECTURE
    difficulty = Column(String(50), default="Intermediate")
    question_text = Column(Text, nullable=False)
    code_snippet = Column(Text, nullable=True)
    options_json = Column(Text, nullable=False) # JSON list
    correct_index = Column(Integer, default=0)
    explanation = Column(Text, nullable=True)

# 12. ASSESSMENT ATTEMPT
class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    attempt_number = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    assessment = relationship("Assessment", back_populates="attempts")
    answers = relationship("AssessmentAnswer", back_populates="attempt", cascade="all, delete-orphan")

# 13. ASSESSMENT ANSWER
class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id = Column(String(36), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(36), nullable=False)
    student_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    score_awarded = Column(Integer, default=0)
    evaluation_rationale = Column(Text, nullable=True)
    
    attempt = relationship("AssessmentAttempt", back_populates="answers")

# 14. ASSESSMENT RESULT
class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), unique=True, nullable=False)
    demonstrated_level = Column(String(50), nullable=False)
    score_ratio = Column(String(20), nullable=False) # e.g. "9 / 10"
    calibrated_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    assessment = relationship("Assessment", back_populates="result")

# 15. ROADMAP
class Roadmap(Base):
    __tablename__ = "roadmaps"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_role = Column(String(100), nullable=False)
    total_nodes = Column(Integer, default=0)
    cleared_nodes = Column(Integer, default=0)
    active_nodes = Column(Integer, default=0)
    locked_nodes = Column(Integer, default=0)
    generated_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    user = relationship("User", back_populates="roadmaps")
    nodes = relationship("RoadmapNode", back_populates="roadmap", cascade="all, delete-orphan")

# 16. ROADMAP NODE
class RoadmapNode(Base):
    __tablename__ = "roadmap_nodes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    roadmap_id = Column(String(36), ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    status = Column(String(50), default="LOCKED") # DEMONSTRATED, ACTIVE_GAP, LOCKED
    tier = Column(String(50), default="Core")
    action_text = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    roadmap = relationship("Roadmap", back_populates="nodes")

# 17. USER PROGRESS
class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = (UniqueConstraint("user_id", "skill_name", name="uq_user_progress_skill"),)
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    completion_status = Column(String(50), default="COMPLETED") # IN_PROGRESS, COMPLETED
    evidence_proof = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    
    user = relationship("User", back_populates="user_progress")

# 18. LEARNING RESOURCE
class LearningResource(Base):
    __tablename__ = "learning_resources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    skill_name = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    provider = Column(String(255), nullable=False)
    level = Column(String(50), default="Intermediate")
    url = Column(String(500), nullable=False)
    resource_type = Column(String(50), default="Documentation")
    estimated_time = Column(String(50), default="4-6 Hours")
    verified = Column(Boolean, default=True)

# 19. JOB
class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_title = Column(String(255), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    location = Column(String(255), default="Bangalore / Remote")
    required_skills_json = Column(Text, nullable=False) # JSON list
    portal_url = Column(String(500), nullable=False)
    provider_source = Column(String(100), default="JobSpy")
    is_active = Column(Boolean, default=True)
    
    skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    matches = relationship("JobMatch", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

# 20. JOB SKILL
class JobSkill(Base):
    __tablename__ = "job_skills"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    is_core = Column(Boolean, default=True)
    required_level = Column(String(50), default="Intermediate")
    
    job = relationship("Job", back_populates="skills")

# 21. JOB MATCH
class JobMatch(Base):
    __tablename__ = "job_matches"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_user_job_match"),)
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    match_percentage = Column(Integer, default=0)
    status_label = Column(String(100), default="In Progress")
    demonstrated_skills_json = Column(Text, default="[]")
    missing_skills_json = Column(Text, default="[]")
    evaluated_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    user = relationship("User", back_populates="job_matches")
    job = relationship("Job", back_populates="matches")

# 22. APPLICATION
class Application(Base):
    __tablename__ = "applications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="SAVED") # SAVED, APPLIED, REVIEWING
    applied_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
