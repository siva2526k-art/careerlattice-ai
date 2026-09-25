import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends, Request
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
    save_user_roadmap, get_user_roadmap,
    complete_roadmap_node, get_verified_learning_resources, get_job_catalog
)
from backend.app.auth import register_user, login_user, validate_session_token, logout_user
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
    confirm_password: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class ConsentRequest(BaseModel):
    accepted: bool
    terms_version: str = "v1.0"
    privacy_version: str = "v1.0"

class UpdateSkillsRequest(BaseModel):
    skills: List[str]

class GitHubConnectRequest(BaseModel):
    username_or_token: str
    is_token: bool = False

class RepoSelectRequest(BaseModel):
    repo_names: Optional[List[str]] = None
    selected_repos: Optional[List[str]] = None
    github_handle: Optional[str] = "rohan-sharma-dev"
    claimed_skills: Optional[List[str]] = None

class GitHubAnalyzeRequest(BaseModel):
    github_handle: str = "rohan-sharma-dev"
    selected_repos: List[str] = []
    claimed_skills: List[str] = []

class SelfAssessmentRequest(BaseModel):
    ratings: Dict[str, str] # skill_name -> Beginner / Developing / Intermediate / Advanced

class AssessmentAnswerRequest(BaseModel):
    skill_name: str
    question_id: str
    student_answer: str

class RoadmapRequest(BaseModel):
    target_role: str = "Junior Backend Developer"

class CompleteNodeRequest(BaseModel):
    evidence_proof: str = "Capstone project completed and pushed to repository"

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
        result = register_user(req.email, req.password, req.full_name, req.confirm_password)
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

@app.post("/api/auth/logout")
def api_logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        logout_user(token)
    return {"status": "success", "message": "Logged out successfully."}

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

@app.post("/api/resumes")
async def api_post_resumes(
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user)
):
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if not file:
            raise HTTPException(status_code=400, detail="Missing file parameter in upload.")
        pdf_bytes = await file.read()
        extracted = parse_resume_pdf(pdf_bytes, file.filename)
        save_user_resume_data(user["id"], file.filename, extracted)
        return {
            "status": "success",
            "filename": file.filename,
            "extracted_data": extracted
        }
    else:
        try:
            body = await request.json()
        except Exception:
            body = {}
        filename = body.get("filename", "resume.pdf")
        skills = body.get("claimed_skills", [])
        data = {
            "name": user.get("full_name", "Student"),
            "email": user.get("email", ""),
            "education": "Computer Science & Engineering",
            "extracted_skills": sorted(list(set(skills)))
        }
        save_user_resume_data(user["id"], filename, data)
        return {
            "status": "success",
            "filename": filename,
            "extracted_skills": data["extracted_skills"],
            "extracted_data": data
        }

@app.get("/api/resumes")
def api_get_resumes(user: Dict[str, Any] = Depends(get_current_user)):
    data = get_user_resume_data(user["id"])
    if not data:
        raise HTTPException(status_code=404, detail="No resume uploaded yet.")
    return data

@app.get("/api/resumes/{resume_id}")
def api_get_resume_by_id(resume_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    data = get_user_resume_data(user["id"])
    if not data:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return data

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
@app.get("/api/github/connect")
def api_github_oauth_url():
    """Generates GitHub OAuth authorization URL or instructions."""
    client_id = os.getenv("GITHUB_CLIENT_ID", "")
    if client_id:
        return {
            "oauth_url": f"https://github.com/login/oauth/authorize?client_id={client_id}&scope=read:user,repo"
        }
    return {
        "oauth_url": None,
        "message": "GitHub OAuth app credentials (GITHUB_CLIENT_ID) not configured in environment. Use username or token flow."
    }

@app.get("/api/github/callback")
def api_github_callback(code: str):
    """Handles GitHub OAuth authorization callback."""
    return {
        "status": "success",
        "code_received": True,
        "message": "GitHub OAuth code received. Token exchange simulated or configured."
    }

@app.get("/api/github/repos")
async def api_get_github_repos(user: Dict[str, Any] = Depends(get_current_user)):
    gh_data = get_user_github(user["id"])
    handle = gh_data.get("github_handle", "rohan-sharma-dev") if gh_data else "rohan-sharma-dev"
    repos = await fetch_user_repositories(handle)
    if not repos:
        repos = get_demo_repositories()
    return {"repositories": repos}

@app.post("/api/github/repos/select")
def api_select_github_repos(req: RepoSelectRequest, user: Dict[str, Any] = Depends(get_current_user)):
    repos = req.repo_names or req.selected_repos or []
    save_user_github(user["id"], req.github_handle or "rohan-sharma-dev", repos, {})
    return {"status": "success", "selected_repos": repos}

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

@app.post("/api/self-assessment")
@app.post("/api/skills/self-assessment")
@app.post("/skills/self-assessment")
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
@app.post("/api/assessment/start")
@app.post("/assessment/start")
def api_get_assessment_questions(skill: str = "Python", level: str = "Intermediate", user: Dict[str, Any] = Depends(get_current_user)):
    questions = get_questions_for_skill(skill_name=skill, starting_level=level, limit=4)
    return {
        "assessment_id": f"assess_{skill.lower()}_{user['id'][:8]}",
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

@app.post("/api/assessment/{assessment_id}/answer")
@app.post("/assessment/{assessment_id}/answer")
def api_assessment_id_answer(assessment_id: str, req: AssessmentAnswerRequest, user: Dict[str, Any] = Depends(get_current_user)):
    return api_submit_assessment_answer(req=req, user=user)

@app.post("/api/assessment/{assessment_id}/submit")
@app.post("/assessment/{assessment_id}/submit")
def api_assessment_id_submit(assessment_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    return api_calculate_evidence(user=user)

@app.get("/api/assessment/{assessment_id}")
@app.get("/assessment/{assessment_id}")
def api_get_assessment_id(assessment_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    results = get_user_assessment_results(user["id"])
    return {"status": "success", "assessment_id": assessment_id, "results": results}

# ==========================================
# 8. EVIDENCE ANALYSIS & DASHBOARD (PAGE 7)
# ==========================================
@app.get("/api/evidence")
@app.get("/evidence")
def api_get_evidence(user: Dict[str, Any] = Depends(get_current_user)):
    return api_get_skills(user=user)

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
    verified = [s for s in skills if s["evidence_status"] == "VERIFIED"]
    partial = [s for s in skills if s["evidence_status"] == "PARTIAL"]
    unverified = [s for s in skills if s["evidence_status"] == "NOT_VERIFIED"]
    
    return {
        "user": user,
        "demonstrated_ratio": f"{len(verified)} / {len(skills)}" if skills else "0 / 0",
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

@app.get("/api/roadmap")
def api_get_saved_roadmap(role: str = "Junior Backend Developer", user: Dict[str, Any] = Depends(get_current_user)):
    saved = get_user_roadmap(user["id"])
    if saved and saved.get("target_role") == role:
        return saved
    return api_get_roadmap(RoadmapRequest(target_role=role), user)

@app.post("/api/roadmap/{node}/complete")
def api_complete_roadmap_node(node: str, req: CompleteNodeRequest = CompleteNodeRequest(), user: Dict[str, Any] = Depends(get_current_user)):
    result = complete_roadmap_node(user["id"], node, req.evidence_proof)
    return result

@app.get("/api/resources")
def api_get_resources(skill: Optional[str] = None, user: Dict[str, Any] = Depends(get_current_user)):
    resources = get_verified_learning_resources(skill)
    return {"status": "success", "count": len(resources), "resources": resources}

@app.post("/api/resources/{resource_id}/complete")
def api_complete_resource(resource_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    return {"status": "success", "resource_id": resource_id, "completed": True}

@app.get("/api/skills")
def api_get_skills(user: Dict[str, Any] = Depends(get_current_user)):
    skills = get_user_skills(user["id"])
    return {"status": "success", "skills": skills}

@app.get("/api/evidence/{skill}")
def api_get_skill_evidence(skill: str, user: Dict[str, Any] = Depends(get_current_user)):
    skills = get_user_skills(user["id"])
    match = [s for s in skills if s["skill_name"].lower() == skill.lower()]
    if match:
        return match[0]
    raise HTTPException(status_code=404, detail=f"No evidence record found for skill '{skill}'.")

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

@app.get("/api/jobs/{job_id}")
def api_get_job_detail(job_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    catalog = get_job_catalog()
    match = [j for j in catalog if j["id"] == job_id]
    if match:
        return match[0]
    raise HTTPException(status_code=404, detail="Job posting not found.")

@app.get("/api/jobs/{job_id}/match")
def api_get_job_match(job_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    skills = get_user_skills(user["id"])
    verified_names = [s["skill_name"] for s in skills if s["evidence_status"] == "VERIFIED"]
    partial_names = [s["skill_name"] for s in skills if s["evidence_status"] == "PARTIAL"]
    
    catalog = get_job_catalog()
    job = next((j for j in catalog if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")
        
    req_skills = set(job.get("required_skills", []))
    verified_met = [s for s in req_skills if s in verified_names]
    partial_met = [s for s in req_skills if s in partial_names]
    missing = [s for s in req_skills if s not in verified_names and s not in partial_names]
    
    match_score = int(((len(verified_met) * 1.0 + len(partial_met) * 0.5) / max(len(req_skills), 1)) * 100)
    
    return {
        "job_id": job_id,
        "role_title": job["title"],
        "company": job["company"],
        "match_percentage": match_score,
        "verified_met": verified_met,
        "partial_met": partial_met,
        "missing_gaps": missing,
        "status_label": "High Alignment" if match_score >= 80 else ("In Progress" if match_score >= 50 else "Prerequisite Gaps")
    }

# ==========================================
# 11. CONTINUOUS LEARNING LOOP (RESCAN)
# ==========================================
@app.post("/api/evidence/rescan")
@app.post("/api/github/rescan")
@app.post("/github/rescan")
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
