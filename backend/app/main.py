import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.app.config import log_event, PORT, ENVIRONMENT
from backend.app.database import (
    init_db, record_consent, get_user_consent,
    save_user_resume_data, get_user_resume_data,
    save_user_github, get_user_github,
    save_user_skill_evidence, get_user_skills,
    save_assessment_attempt, get_user_assessment_results,
    save_user_roadmap, get_user_roadmap
)
from backend.app.auth import register_user, login_user, validate_session_token
from backend.app.resume_parser import parse_resume_pdf, get_demo_resume_data
from backend.app.github_service import fetch_user_repositories, get_demo_repositories
from backend.app.code_inspector import evaluate_selected_repositories
from backend.app.assessment_engine import get_questions_for_skill, grade_assessment_submission, generate_gemini_dynamic_question
from backend.app.evidence_engine import aggregate_candidate_evidence_matrix
from backend.app.graph_engine import generate_personalized_roadmap
from backend.app.job_provider import evaluate_job_matches, DatasetJobProvider

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    log_event("SYSTEM", f"CareerLattice AI API initialized in {ENVIRONMENT} mode.")
    yield

# Initialize FastAPI App
app = FastAPI(
    title="CareerLattice AI API",
    description="Evidence-based Skill-to-Career Readiness Platform API (SIH SE-02)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency: Authenticate User via Bearer Token
def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required. Missing Bearer token.")
    token = authorization.split(" ")[1]
    user = validate_session_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")
    return user

# Pydantic Request Models
class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ConsentRequest(BaseModel):
    accepted: bool

class UpdateSkillsRequest(BaseModel):
    skills: List[str]

class GitHubConnectRequest(BaseModel):
    username_or_token: str
    is_token: bool = False

class GitHubAnalyzeRequest(BaseModel):
    github_handle: str
    selected_repos: List[str]
    claimed_skills: List[str]

class SelfAssessmentRequest(BaseModel):
    ratings: Dict[str, str] # skill_name -> Beginner / Developing / Intermediate / Advanced

class AssessmentAnswerRequest(BaseModel):
    skill_name: str
    question_id: str
    student_answer: str

class RoadmapRequest(BaseModel):
    target_role: str = "Junior Backend Developer"

# ==========================================
# 1. HEALTH & SYSTEM
# ==========================================
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CareerLattice AI Backend",
        "version": "1.0.0",
        "environment": ENVIRONMENT
    }

# ==========================================
# 2. AUTHENTICATION (PAGE 1)
# ==========================================
@app.post("/api/auth/register")
def api_register(req: RegisterRequest):
    try:
        result = register_user(req.email, req.password, req.full_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
def api_login(req: LoginRequest):
    try:
        result = login_user(req.email, req.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/api/auth/me")
def api_get_me(user: Dict[str, Any] = Depends(get_current_user)):
    consent = get_user_consent(user["id"])
    return {
        "user": user,
        "consent_accepted": consent
    }

# ==========================================
# 3. TERMS & CONDITIONS (PAGE 2)
# ==========================================
@app.post("/api/consent")
def api_record_consent(req: ConsentRequest, user: Dict[str, Any] = Depends(get_current_user)):
    record_consent(user["id"], req.accepted)
    return {"status": "success", "accepted": req.accepted}

# ==========================================
# 4. RESUME UPLOAD (PAGE 3)
# ==========================================
@app.post("/api/resume/upload")
async def api_upload_resume(
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")
    
    pdf_bytes = await file.read()
    if len(pdf_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 10MB.")
        
    extracted = parse_resume_pdf(pdf_bytes, file.filename)
    save_user_resume_data(user["id"], file.filename, extracted)
    
    return {
        "status": "success",
        "filename": file.filename,
        "extracted_data": extracted
    }

@app.post("/api/resume/update-skills")
def api_update_skills(req: UpdateSkillsRequest, user: Dict[str, Any] = Depends(get_current_user)):
    resume_data = get_user_resume_data(user["id"])
    if not resume_data:
        raise HTTPException(status_code=404, detail="No resume uploaded yet.")
    
    resume_data["data"]["extracted_skills"] = sorted(list(set(req.skills)))
    save_user_resume_data(user["id"], resume_data["filename"], resume_data["data"])
    return {"status": "success", "updated_skills": resume_data["data"]["extracted_skills"]}

# ==========================================
# 5. GITHUB CONNECTION & AST (PAGE 4)
# ==========================================
@app.post("/api/github/connect")
async def api_github_connect(req: GitHubConnectRequest, user: Dict[str, Any] = Depends(get_current_user)):
    repos = await fetch_user_repositories(req.username_or_token, req.is_token)
    if not repos:
        # If user not found, provide demo repository options
        repos = get_demo_repositories()
    return {
        "status": "success",
        "github_handle": req.username_or_token,
        "repositories": repos
    }

@app.post("/api/github/analyze")
def api_github_analyze(req: GitHubAnalyzeRequest, user: Dict[str, Any] = Depends(get_current_user)):
    evidence = evaluate_selected_repositories(req.selected_repos, req.claimed_skills)
    save_user_github(user["id"], req.github_handle, req.selected_repos, evidence)
    return {
        "status": "success",
        "evidence": evidence
    }

# ==========================================
# 6. SELF ASSESSMENT (PAGE 5)
# ==========================================
@app.post("/api/self-assessment")
def api_self_assessment(req: SelfAssessmentRequest, user: Dict[str, Any] = Depends(get_current_user)):
    # Save self ratings
    for skill, level in req.ratings.items():
        save_user_skill_evidence(
            user_id=user["id"],
            skill_name=skill,
            self_level=level,
            status="PARTIAL",
            final_level=level,
            confidence="Medium",
            evidence={"self_assessed": level}
        )
    return {"status": "success", "saved_ratings": req.ratings}

# ==========================================
# 7. ADAPTIVE TECHNICAL ASSESSMENT (PAGE 6)
# ==========================================
@app.get("/api/assessment/questions")
def api_get_assessment_questions(skill: str, level: str = "Intermediate", user: Dict[str, Any] = Depends(get_current_user)):
    questions = get_questions_for_skill(skill_name=skill, starting_level=level, limit=4)
    return {
        "skill": skill,
        "questions": questions
    }

@app.post("/api/assessment/answer")
def api_submit_assessment_answer(req: AssessmentAnswerRequest, user: Dict[str, Any] = Depends(get_current_user)):
    grading = grade_assessment_submission(req.skill_name, req.question_id, req.student_answer)
    save_assessment_attempt(
        user_id=user["id"],
        skill_name=req.skill_name,
        question_id=req.question_id,
        q_type=grading["question_type"],
        answer=req.student_answer,
        is_correct=grading["is_correct"],
        score=grading["score"]
    )
    return {
        "status": "success",
        "grading": grading
    }

# ==========================================
# 8. EVIDENCE ANALYSIS & DASHBOARD (PAGE 7)
# ==========================================
@app.post("/api/evidence/calculate")
def api_calculate_evidence(user: Dict[str, Any] = Depends(get_current_user)):
    resume_info = get_user_resume_data(user["id"])
    claimed = resume_info["data"]["extracted_skills"] if resume_info else ["Python", "FastAPI", "Docker", "PostgreSQL", "Git", "REST APIs", "AWS", "Kubernetes"]
    
    github_info = get_user_github(user["id"])
    gh_findings = github_info["evidence_summary"].get("skills_evidence", {}) if github_info else {}
    
    # Retrieve self-assessments
    existing_skills = get_user_skills(user["id"])
    self_map = {s["skill_name"]: s["self_level"] for s in existing_skills if s.get("self_level")}
    
    # Retrieve assessment results
    attempts = get_user_assessment_results(user["id"])
    scores_map = {}
    for a in attempts:
        scores_map[a["skill_name"]] = max(scores_map.get(a["skill_name"], 0), a["score"])
        
    matrix = aggregate_candidate_evidence_matrix(claimed, gh_findings, self_map, scores_map)
    
    # Save into DB
    for item in matrix:
        save_user_skill_evidence(
            user_id=user["id"],
            skill_name=item["skill_name"],
            self_level=item["self_declared_level"],
            status=item["evidence_status"],
            final_level=item["final_level"],
            confidence=item["confidence"],
            evidence=item
        )
        
    return {
        "status": "success",
        "evidence_matrix": matrix
    }

@app.get("/api/dashboard")
def api_get_dashboard(user: Dict[str, Any] = Depends(get_current_user)):
    skills = get_user_skills(user["id"])
    if not skills:
        # Auto-compute if not yet computed
        api_calculate_evidence(user)
        skills = get_user_skills(user["id"])
        
    verified = [s for s in skills if s["evidence_status"] == "VERIFIED"]
    partial = [s for s in skills if s["evidence_status"] == "PARTIAL"]
    unverified = [s for s in skills if s["evidence_status"] == "NOT_VERIFIED"]
    
    return {
        "user": user,
        "demonstrated_ratio": f"{len(verified)} / {len(skills)}",
        "verified_count": len(verified),
        "partial_count": len(partial),
        "unverified_count": len(unverified),
        "skills": skills
    }

# ==========================================
# 9. ROADMAP ENGINE (PAGE 8)
# ==========================================
@app.post("/api/roadmap")
def api_get_roadmap(req: RoadmapRequest, user: Dict[str, Any] = Depends(get_current_user)):
    skills = get_user_skills(user["id"])
    verified_names = [s["skill_name"] for s in skills if s["evidence_status"] == "VERIFIED"]
    partial_names = [s["skill_name"] for s in skills if s["evidence_status"] == "PARTIAL"]
    
    roadmap = generate_personalized_roadmap(req.target_role, verified_names, partial_names)
    save_user_roadmap(user["id"], req.target_role, roadmap["nodes"])
    return roadmap

# ==========================================
# 10. JOB MATCHING ENGINE (PAGE 9)
# ==========================================
@app.get("/api/jobs")
def api_get_jobs(role: str = "Junior Backend Developer", user: Dict[str, Any] = Depends(get_current_user)):
    skills = get_user_skills(user["id"])
    verified_names = [s["skill_name"] for s in skills if s["evidence_status"] == "VERIFIED"]
    partial_names = [s["skill_name"] for s in skills if s["evidence_status"] == "PARTIAL"]
    
    matched_jobs = evaluate_job_matches(
        role_title=role,
        verified_skills=verified_names,
        partial_skills=partial_names,
        provider=DatasetJobProvider()
    )
    return {
        "target_role": role,
        "total_jobs_found": len(matched_jobs),
        "jobs": matched_jobs
    }

# ==========================================
# 11. CONTINUOUS LEARNING LOOP (RESCAN)
# ==========================================
@app.post("/api/evidence/rescan")
def api_evidence_rescan(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Simulates / triggers the 'Update My Evidence' loop:
    Student pushes Docker & AWS project -> AST inspector verifies new files ->
    Skill transitions to VERIFIED -> Roadmap unlocks -> Job match increases to 100%!
    """
    log_event("EVIDENCE", f"Triggering evidence rescan for user {user['id']}")
    
    # Mark Docker and AWS as verified via new repository commit
    save_user_skill_evidence(
        user_id=user["id"],
        skill_name="Docker",
        self_level="Intermediate",
        status="VERIFIED",
        final_level="Intermediate",
        confidence="High",
        evidence={
            "status": "VERIFIED",
            "supporting_files": ["Dockerfile (Multi-Stage)", "docker-compose.yml"],
            "rationale": "Verified via recent commit: Containerized FastAPI service with healthchecks."
        }
    )
    save_user_skill_evidence(
        user_id=user["id"],
        skill_name="AWS",
        self_level="Developing",
        status="PARTIAL",
        final_level="Developing",
        confidence="Medium",
        evidence={
            "status": "PARTIAL",
            "supporting_files": ["ecs-task-definition.json"],
            "rationale": "Verified via recent commit: AWS ECS task configuration detected."
        }
    )
    return {
        "status": "success",
        "message": "Repository rescanned. New implementation evidence detected for Docker and AWS.",
        "skills_updated": ["Docker", "AWS"]
    }

# ==========================================
# 12. DEMO SEED LOADER (1-Click Rohan Sharma Profile)
# ==========================================
@app.post("/api/demo/load")
def api_load_demo_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """Pre-loads the complete standard Rohan Sharma candidate flow."""
    # 1. Accept consent
    record_consent(user["id"], True)
    
    # 2. Load Resume
    demo_resume = get_demo_resume_data()
    save_user_resume_data(user["id"], demo_resume["filename"], demo_resume)
    
    # 3. Load GitHub
    demo_repos = get_demo_repositories()
    selected = [r["name"] for r in demo_repos if r.get("selected_by_default")]
    evidence = evaluate_selected_repositories(selected, demo_resume["extracted_skills"])
    save_user_github(user["id"], "rohan-sharma-dev", selected, evidence)
    
    # 4. Self-Assessments
    self_map = {
        "Python": "Advanced",
        "FastAPI": "Intermediate",
        "SQL": "Intermediate",
        "PostgreSQL": "Developing",
        "Docker": "Developing",
        "AWS": "Beginner",
        "Kubernetes": "Beginner",
        "Git": "Intermediate",
        "REST APIs": "Intermediate"
    }
    
    # 5. Populate Evidence
    matrix = aggregate_candidate_evidence_matrix(
        claimed_skills=demo_resume["extracted_skills"],
        github_findings=evidence["skills_evidence"],
        self_assessments=self_map,
        assessment_scores={"Python": 9, "FastAPI": 8, "Docker": 6, "PostgreSQL": 7}
    )
    
    for item in matrix:
        save_user_skill_evidence(
            user_id=user["id"],
            skill_name=item["skill_name"],
            self_level=item["self_declared_level"],
            status=item["evidence_status"],
            final_level=item["final_level"],
            confidence=item["confidence"],
            evidence=item
        )
        
    return {
        "status": "success",
        "message": "Demo profile loaded successfully.",
        "demo_user": "Rohan Sharma"
    }

# Static file serving (Root index.html)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

@app.get("/")
def serve_index():
    index_file = ROOT_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "CareerLattice AI Backend Running"}
