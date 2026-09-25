import pytest
import os
import secrets
from backend.app.database import (
    init_db, create_user, get_user_by_email,
    record_consent, get_user_consent,
    save_user_resume_data, get_user_resume_data,
    save_user_skill_evidence, get_user_skills
)
from backend.app.auth import hash_password, verify_password, register_user, login_user
from backend.app.resume_parser import get_demo_resume_data, parse_resume_pdf
from backend.app.code_inspector import inspect_repository_artifacts, evaluate_selected_repositories
from backend.app.assessment_engine import load_question_bank, get_questions_for_skill, grade_assessment_submission
from backend.app.evidence_engine import calculate_evidence_proficiency, aggregate_candidate_evidence_matrix
from backend.app.graph_engine import build_prerequisite_graph, generate_personalized_roadmap
from backend.app.job_provider import DatasetJobProvider, evaluate_job_matches

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()

def test_password_hashing():
    raw = "SecurePassword123"
    hashed = hash_password(raw)
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_auth_registration_and_login():
    email = f"tester_{os.getpid()}@test.com"
    reg = register_user(email, "password123", "Test Candidate")
    assert "token" in reg
    assert reg["user"]["email"] == email

    login = login_user(email, "password123")
    assert "token" in login
    assert login["user"]["email"] == email

    with pytest.raises(ValueError):
        login_user(email, "wrongpassword")

def test_consent_recording():
    email = f"consent_test_{secrets.token_hex(4)}@test.com"
    user = create_user(email, "hash", "Consent User")
    assert get_user_consent(user["id"]) is False
    record_consent(user["id"], True)
    assert get_user_consent(user["id"]) is True

def test_resume_parser():
    demo = get_demo_resume_data()
    assert "Python" in demo["extracted_skills"]
    assert "FastAPI" in demo["extracted_skills"]
    assert "Docker" in demo["extracted_skills"]

def test_code_inspector():
    sample_files = {
        "requirements.txt": "fastapi==0.110.0\nuvicorn==0.28.0\npsycopg2-binary==2.9.9",
        "Dockerfile": "FROM python:3.11\nWORKDIR /app\nCOPY . .\nCMD ['uvicorn', 'main:app']",
        "main.py": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef root(): return {'status': 'ok'}"
    }
    artifacts = inspect_repository_artifacts(sample_files)
    assert artifacts["skills_detected"]["FastAPI"] == "Strong"
    assert artifacts["skills_detected"]["PostgreSQL"] == "Strong"
    assert artifacts["skills_detected"]["Python"] == "Strong"

def test_evidence_engine():
    # Strong code + good score -> VERIFIED
    gh_item = {"status": "VERIFIED", "supporting_files": ["main.py"]}
    prof_verified = calculate_evidence_proficiency("FastAPI", True, gh_item, "Advanced", 9)
    assert prof_verified["evidence_status"] == "VERIFIED"
    assert prof_verified["confidence"] == "High"

    # Partial code -> PARTIAL
    gh_partial = {"status": "PARTIAL", "supporting_files": ["Dockerfile"]}
    prof_partial = calculate_evidence_proficiency("Docker", True, gh_partial, "Intermediate", 6)
    assert prof_partial["evidence_status"] == "PARTIAL"

    # No code evidence -> NOT_VERIFIED
    prof_unverified = calculate_evidence_proficiency("AWS", True, None, "Beginner", 4)
    assert prof_unverified["evidence_status"] == "NOT_VERIFIED"
    assert "Not Verified" in prof_unverified["rationale"]

def test_prerequisite_graph_and_kahn_sort():
    G = build_prerequisite_graph()
    assert G.has_edge("Python", "FastAPI")
    assert G.has_edge("Linux", "Docker")

    # If student demonstrates Python, REST, FastAPI, the roadmap marks them demonstrated
    roadmap = generate_personalized_roadmap(
        target_role="Junior Backend Developer",
        verified_skills=["Python", "REST APIs", "FastAPI", "Git"],
        partial_skills=["Docker"]
    )
    assert roadmap["total_nodes"] > 0
    # Python should be demonstrated
    py_node = next(n for n in roadmap["nodes"] if n["skill_name"] == "Python")
    assert py_node["status"] == "demonstrated"

    # Without Linux, Docker should be locked because Linux is a prerequisite of Docker!
    docker_node = next(n for n in roadmap["nodes"] if n["skill_name"] == "Docker")
    assert docker_node["status"] == "locked"

    # Once Linux is verified, Docker's prerequisites are met, so it becomes active_gap!
    roadmap_with_linux = generate_personalized_roadmap(
        target_role="Junior Backend Developer",
        verified_skills=["Python", "REST APIs", "FastAPI", "Git", "Linux"],
        partial_skills=["Docker"]
    )
    docker_active = next(n for n in roadmap_with_linux["nodes"] if n["skill_name"] == "Docker")
    assert docker_active["status"] == "active_gap"

def test_assessment_engine():
    q_list = get_questions_for_skill("Python", starting_level="Intermediate", limit=2)
    assert len(q_list) > 0
    q1 = q_list[0]
    grading = grade_assessment_submission("Python", q1["id"], "C")
    assert "is_correct" in grading
    assert "score" in grading

def test_job_provider_and_matching():
    provider = DatasetJobProvider()
    jobs = evaluate_job_matches(
        role_title="Junior Backend Developer",
        verified_skills=["Python", "FastAPI", "PostgreSQL", "Docker", "Git", "REST APIs"],
        partial_skills=["Redis"],
        provider=provider
    )
    assert len(jobs) > 0
    top_job = jobs[0]
    assert top_job["match_percentage"] >= 80
    assert "Good Evidence Match" in top_job["match_status"]
