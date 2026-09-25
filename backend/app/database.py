import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.app.config import log_event
from backend.app.db_session import SessionLocal, init_db as session_init_db
from backend.app.models import (
    User, Profile, Consent, Resume, GitHubAccount, GitHubRepository,
    Skill, UserSkill, SkillEvidence, Assessment, AssessmentQuestion,
    AssessmentAttempt, AssessmentAnswer, AssessmentResult, Roadmap,
    RoadmapNode, UserProgress, LearningResource, Job, JobSkill, JobMatch, Application
)

def init_db():
    """Initializes schema and tables."""
    session_init_db()

# ==========================================
# 1. USER & PROFILE QUERIES
# ==========================================
def create_user(email: str, password_hash: str, full_name: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=email.lower().strip(),
            password_hash=password_hash,
            full_name=full_name.strip()
        )
        db.add(user)
        # Create initial profile
        profile = Profile(
            user_id=user_id,
            headline="Aspiring Cloud & Backend Developer",
            target_role="Junior Backend Developer"
        )
        db.add(profile)
        db.commit()
        log_event("AUTH", f"Created user {email} (ID: {user_id}) with profile in database.")
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat() if user.created_at else datetime.now(timezone.utc).isoformat()
        }
    finally:
        db.close()

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.lower().strip()).first()
        if user:
            return {
                "id": user.id,
                "email": user.email,
                "password_hash": user.password_hash,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        return None
    finally:
        db.close()

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        return None
    finally:
        db.close()

# ==========================================
# 2. CONSENT
# ==========================================
def record_consent(user_id: str, accepted: bool) -> bool:
    db = SessionLocal()
    try:
        consent = db.query(Consent).filter(Consent.user_id == user_id).first()
        if not consent:
            consent = Consent(
                user_id=user_id,
                terms_version="v1.0",
                privacy_version="v1.0",
                accepted=accepted,
                accepted_at=datetime.now(timezone.utc)
            )
            db.add(consent)
        else:
            consent.accepted = accepted
            consent.accepted_at = datetime.now(timezone.utc)
        db.commit()
        log_event("AUTH", f"User {user_id} consent recorded: {accepted}")
        return accepted
    finally:
        db.close()

def get_user_consent(user_id: str) -> bool:
    db = SessionLocal()
    try:
        consent = db.query(Consent).filter(Consent.user_id == user_id).first()
        return bool(consent and consent.accepted)
    finally:
        db.close()

# ==========================================
# 3. RESUME
# ==========================================
def save_user_resume_data(user_id: str, filename: str, data: Dict[str, Any]):
    db = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.user_id == user_id).first()
        extracted_skills = data.get("extracted_skills", [])
        if not resume:
            resume = Resume(
                user_id=user_id,
                filename=filename,
                file_size=len(json.dumps(data)),
                extracted_skills_json=json.dumps(extracted_skills),
                raw_text=data.get("raw_text", ""),
                parsed_data_json=json.dumps(data),
                uploaded_at=datetime.now(timezone.utc)
            )
            db.add(resume)
        else:
            resume.filename = filename
            resume.extracted_skills_json = json.dumps(extracted_skills)
            resume.parsed_data_json = json.dumps(data)
            resume.uploaded_at = datetime.now(timezone.utc)
        db.commit()
        log_event("RESUME", f"Saved resume for user {user_id} ({filename})")
    finally:
        db.close()

def get_user_resume_data(user_id: str) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.uploaded_at.desc()).first()
        if resume:
            parsed = json.loads(resume.parsed_data_json) if resume.parsed_data_json else {}
            if "extracted_skills" not in parsed:
                parsed["extracted_skills"] = json.loads(resume.extracted_skills_json)
            return {
                "filename": resume.filename,
                "data": parsed,
                "uploaded_at": resume.uploaded_at.isoformat() if resume.uploaded_at else None
            }
        return None
    finally:
        db.close()

# ==========================================
# 4. GITHUB ACCOUNT & REPOSITORIES
# ==========================================
def save_user_github(user_id: str, github_handle: str, selected_repos: List[str], evidence_summary: Dict[str, Any]):
    db = SessionLocal()
    try:
        account = db.query(GitHubAccount).filter(GitHubAccount.user_id == user_id).first()
        if not account:
            account = GitHubAccount(
                user_id=user_id,
                github_handle=github_handle,
                connected_at=datetime.now(timezone.utc)
            )
            db.add(account)
            db.flush()
        else:
            account.github_handle = github_handle
            account.connected_at = datetime.now(timezone.utc)
            
        # Update repository selections
        existing_repos = {r.repo_name: r for r in db.query(GitHubRepository).filter(GitHubRepository.github_account_id == account.id).all()}
        for r_name in selected_repos:
            if r_name in existing_repos:
                existing_repos[r_name].is_selected = True
                existing_repos[r_name].analyzed_at = datetime.now(timezone.utc)
            else:
                new_repo = GitHubRepository(
                    github_account_id=account.id,
                    repo_name=r_name,
                    is_selected=True,
                    manifest_findings_json=json.dumps(evidence_summary.get("skills_evidence", {})),
                    analyzed_at=datetime.now(timezone.utc)
                )
                db.add(new_repo)
                
        db.commit()
        log_event("GITHUB", f"Saved GitHub data for user {user_id} (@{github_handle}, {len(selected_repos)} repos)")
    finally:
        db.close()

def get_user_github(user_id: str) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        account = db.query(GitHubAccount).filter(GitHubAccount.user_id == user_id).first()
        if account:
            repos = [r.repo_name for r in account.repositories if r.is_selected]
            # Merge findings
            findings = {}
            for r in account.repositories:
                if r.manifest_findings_json:
                    try:
                        f = json.loads(r.manifest_findings_json)
                        findings.update(f)
                    except Exception:
                        pass
            return {
                "github_handle": account.github_handle,
                "selected_repos": repos,
                "evidence_summary": {"skills_evidence": findings},
                "analyzed_at": account.connected_at.isoformat() if account.connected_at else None
            }
        return None
    finally:
        db.close()

# ==========================================
# 5. USER SKILLS & EVIDENCE
# ==========================================
def save_user_skill_evidence(
    user_id: str,
    skill_name: str,
    self_level: Optional[str],
    status: str,
    final_level: str,
    confidence: str,
    evidence: Dict[str, Any]
):
    db = SessionLocal()
    try:
        user_skill = db.query(UserSkill).filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_name == skill_name
        ).first()
        
        if not user_skill:
            user_skill = UserSkill(
                user_id=user_id,
                skill_name=skill_name,
                self_level=self_level,
                evidence_status=status,
                final_level=final_level,
                confidence=confidence,
                evidence_json=json.dumps(evidence),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(user_skill)
            db.flush()
        else:
            if self_level:
                user_skill.self_level = self_level
            user_skill.evidence_status = status
            user_skill.final_level = final_level
            user_skill.confidence = confidence
            user_skill.evidence_json = json.dumps(evidence)
            user_skill.updated_at = datetime.now(timezone.utc)
            
        # Append specific evidence record
        se = SkillEvidence(
            user_skill_id=user_skill.id,
            evidence_type="EVIDENCE_MATRIX",
            source_reference=f"Triangulated ({status})",
            details_json=json.dumps(evidence),
            recorded_at=datetime.now(timezone.utc)
        )
        db.add(se)
        db.commit()
    finally:
        db.close()

def get_user_skills(user_id: str) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
        result = []
        for us in user_skills:
            # Get latest evidence record details
            latest_ev = db.query(SkillEvidence).filter(
                SkillEvidence.user_skill_id == us.id
            ).order_by(SkillEvidence.recorded_at.desc()).first()
            
            ev_data = json.loads(latest_ev.details_json) if latest_ev else {
                "skill_name": us.skill_name,
                "evidence_status": us.evidence_status,
                "final_level": us.final_level,
                "confidence": us.confidence,
                "rationale": f"Calibrated {us.final_level} with {us.confidence} confidence."
            }
            
            result.append({
                "skill_name": us.skill_name,
                "self_level": us.self_level,
                "evidence_status": us.evidence_status,
                "final_level": us.final_level,
                "confidence": us.confidence,
                "evidence": ev_data,
                "updated_at": us.updated_at.isoformat() if us.updated_at else None
            })
        return result
    finally:
        db.close()

# ==========================================
# 6. ASSESSMENTS & ATTEMPTS
# ==========================================
def save_assessment_attempt(
    user_id: str,
    skill_name: str,
    question_id: str,
    q_type: str,
    answer: str,
    is_correct: bool,
    score: int
):
    db = SessionLocal()
    try:
        # Find or create active assessment container
        assessment = db.query(Assessment).filter(
            Assessment.user_id == user_id,
            Assessment.skill_name == skill_name,
            Assessment.status == "COMPLETED"
        ).order_by(Assessment.completed_at.desc()).first()
        
        if not assessment:
            assessment = Assessment(
                user_id=user_id,
                skill_name=skill_name,
                status="COMPLETED",
                total_score=score,
                max_score=10,
                completed_at=datetime.now(timezone.utc)
            )
            db.add(assessment)
            db.flush()
        else:
            assessment.total_score = max(assessment.total_score, score)
            
        # Record attempt and answer
        attempt = AssessmentAttempt(
            assessment_id=assessment.id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(attempt)
        db.flush()
        
        ans = AssessmentAnswer(
            attempt_id=attempt.id,
            question_id=question_id,
            student_answer=answer,
            is_correct=is_correct,
            score_awarded=score,
            evaluation_rationale=f"Evaluated type {q_type}: {'Correct' if is_correct else 'Incorrect'}"
        )
        db.add(ans)
        db.commit()
    finally:
        db.close()

def get_user_assessment_results(user_id: str, skill_name: Optional[str] = None) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        query = db.query(Assessment).filter(Assessment.user_id == user_id)
        if skill_name:
            query = query.filter(Assessment.skill_name == skill_name)
        assessments = query.all()
        results = []
        for a in assessments:
            results.append({
                "skill_name": a.skill_name,
                "score": a.total_score,
                "max_score": a.max_score,
                "status": a.status,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None
            })
        return results
    finally:
        db.close()

# ==========================================
# 7. ROADMAP & USER PROGRESS
# ==========================================
def save_user_roadmap(user_id: str, target_role: str, roadmap_nodes: List[Dict[str, Any]]):
    db = SessionLocal()
    try:
        roadmap = db.query(Roadmap).filter(Roadmap.user_id == user_id).first()
        cleared = len([n for n in roadmap_nodes if n.get("status") in ["demonstrated", "cleared"]])
        active = len([n for n in roadmap_nodes if n.get("status") in ["active", "active_gap"]])
        locked = len([n for n in roadmap_nodes if n.get("status") == "locked"])
        
        if not roadmap:
            roadmap = Roadmap(
                user_id=user_id,
                target_role=target_role,
                total_nodes=len(roadmap_nodes),
                cleared_nodes=cleared,
                active_nodes=active,
                locked_nodes=locked,
                generated_at=datetime.now(timezone.utc)
            )
            db.add(roadmap)
            db.flush()
        else:
            roadmap.target_role = target_role
            roadmap.total_nodes = len(roadmap_nodes)
            roadmap.cleared_nodes = cleared
            roadmap.active_nodes = active
            roadmap.locked_nodes = locked
            roadmap.generated_at = datetime.now(timezone.utc)
            
        # Update node items
        db.query(RoadmapNode).filter(RoadmapNode.roadmap_id == roadmap.id).delete()
        for n in roadmap_nodes:
            rn = RoadmapNode(
                roadmap_id=roadmap.id,
                skill_name=n.get("skill_name", n.get("title", "")),
                status=n.get("status", "LOCKED").upper(),
                tier=n.get("tier", "Core"),
                action_text=n.get("action_text", n.get("details", "")),
                is_completed=(n.get("status") in ["demonstrated", "cleared"])
            )
            db.add(rn)
        db.commit()
    finally:
        db.close()

def get_user_roadmap(user_id: str) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        roadmap = db.query(Roadmap).filter(Roadmap.user_id == user_id).first()
        if roadmap:
            nodes = []
            for n in roadmap.nodes:
                nodes.append({
                    "id": n.skill_name.lower().replace(" ", "_"),
                    "skill_name": n.skill_name,
                    "title": n.skill_name,
                    "status": n.status.lower(),
                    "tier": n.tier,
                    "action_text": n.action_text,
                    "is_completed": n.is_completed
                })
            return {
                "target_role": roadmap.target_role,
                "total_nodes": roadmap.total_nodes,
                "cleared_nodes": roadmap.cleared_nodes,
                "active_nodes": roadmap.active_nodes,
                "locked_nodes": roadmap.locked_nodes,
                "roadmap_nodes": nodes,
                "updated_at": roadmap.generated_at.isoformat() if roadmap.generated_at else None
            }
        return None
    finally:
        db.close()

def complete_roadmap_node(user_id: str, skill_name: str, evidence_proof: str = "Capstone project completed") -> Dict[str, Any]:
    """Marks a specific learning node as completed and records UserProgress."""
    db = SessionLocal()
    try:
        # Record UserProgress
        prog = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.skill_name == skill_name
        ).first()
        if not prog:
            prog = UserProgress(
                user_id=user_id,
                skill_name=skill_name,
                completion_status="COMPLETED",
                evidence_proof=evidence_proof,
                updated_at=datetime.now(timezone.utc)
            )
            db.add(prog)
        else:
            prog.completion_status = "COMPLETED"
            prog.evidence_proof = evidence_proof
            prog.updated_at = datetime.now(timezone.utc)
            
        # Update user skill to VERIFIED
        save_user_skill_evidence(
            user_id=user_id,
            skill_name=skill_name,
            self_level="Intermediate",
            status="VERIFIED",
            final_level="Intermediate",
            confidence="High",
            evidence={
                "status": "VERIFIED",
                "proof": evidence_proof,
                "rationale": f"Demonstrated via completed roadmap milestone: {evidence_proof}"
            }
        )
        db.commit()
        return {"status": "success", "skill_completed": skill_name}
    finally:
        db.close()

# ==========================================
# 8. LEARNING RESOURCES & JOBS
# ==========================================
def get_verified_learning_resources(skill_name: Optional[str] = None) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        query = db.query(LearningResource)
        if skill_name:
            query = query.filter(LearningResource.skill_name == skill_name)
        resources = query.all()
        return [{
            "id": r.id,
            "skill_name": r.skill_name,
            "title": r.title,
            "provider": r.provider,
            "level": r.level,
            "url": r.url,
            "resource_type": r.resource_type,
            "estimated_time": r.estimated_time,
            "verified": r.verified
        } for r in resources]
    finally:
        db.close()

def get_job_catalog() -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        jobs = db.query(Job).filter(Job.is_active == True).all()
        return [{
            "id": j.id,
            "title": j.role_title,
            "company": j.company_name,
            "location": j.location,
            "required_skills": json.loads(j.required_skills_json),
            "apply_url": j.portal_url,
            "provider": j.provider_source
        } for j in jobs]
    finally:
        db.close()
