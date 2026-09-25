import pytest
import secrets
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"

def test_api_auth_and_flow():
    email = f"api_user_{secrets.token_hex(4)}@test.com"
    
    # 1. Register
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123",
        "full_name": "API Test User"
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Me
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["user"]["email"] == email
    assert me_res.json()["consent_accepted"] is False

    # 3. Consent
    consent_res = client.post("/api/consent", json={"accepted": True}, headers=headers)
    assert consent_res.status_code == 200
    assert consent_res.json()["accepted"] is True

    # 4. GitHub Connect & Analyze
    gh_res = client.post("/api/github/connect", json={"username_or_token": "rohan-sharma-dev"}, headers=headers)
    assert gh_res.status_code == 200
    repos = gh_res.json()["repositories"]
    assert len(repos) > 0

    analyze_res = client.post("/api/github/analyze", json={
        "github_handle": "rohan-sharma-dev",
        "selected_repos": [repos[0]["name"]],
        "claimed_skills": ["Python", "FastAPI", "Docker", "AWS"]
    }, headers=headers)
    assert analyze_res.status_code == 200
    assert "evidence" in analyze_res.json()

    # 5. Self-Assessment
    self_res = client.post("/api/self-assessment", json={
        "ratings": {"Python": "Advanced", "FastAPI": "Intermediate", "Docker": "Developing", "AWS": "Beginner"}
    }, headers=headers)
    assert self_res.status_code == 200

    # 6. Assessment Questions & Answer
    q_res = client.get("/api/assessment/questions?skill=Python&level=Intermediate", headers=headers)
    assert q_res.status_code == 200
    questions = q_res.json()["questions"]
    assert len(questions) > 0

    ans_res = client.post("/api/assessment/answer", json={
        "skill_name": "Python",
        "question_id": questions[0]["id"],
        "student_answer": "C"
    }, headers=headers)
    assert ans_res.status_code == 200

    # 7. Evidence Calculation
    ev_res = client.post("/api/evidence/calculate", headers=headers)
    assert ev_res.status_code == 200
    matrix = ev_res.json()["evidence_matrix"]
    assert len(matrix) > 0

    # 8. Dashboard
    dash_res = client.get("/api/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert "demonstrated_ratio" in dash_data

    # 9. Roadmap
    road_res = client.post("/api/roadmap", json={"target_role": "Junior Backend Developer"}, headers=headers)
    assert road_res.status_code == 200
    road_data = road_res.json()
    assert "nodes" in road_data
    assert road_data["total_nodes"] > 0

    # 10. Jobs
    jobs_res = client.get("/api/jobs?role=Junior Backend Developer", headers=headers)
    assert jobs_res.status_code == 200
    assert len(jobs_res.json()["jobs"]) > 0

    # 11. Rescan Loop
    rescan_res = client.post("/api/evidence/rescan", headers=headers)
    assert rescan_res.status_code == 200
    assert rescan_res.json()["status"] == "success"

def test_api_demo_loader():
    email = f"demo_loader_{secrets.token_hex(4)}@test.com"
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123",
        "full_name": "Demo Loader User"
    })
    token = reg_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    demo_res = client.post("/api/demo/load", headers=headers)
    assert demo_res.status_code == 200
    assert demo_res.json()["demo_user"] == "Rohan Sharma"

    dash_res = client.get("/api/dashboard", headers=headers)
    assert dash_res.status_code == 200
    assert dash_res.json()["verified_count"] > 0

def test_serve_index_html():
    res = client.get("/")
    assert res.status_code == 200
    assert "CareerLattice AI" in res.text

def test_database_persistence_across_sessions():
    """Mandatory Section 6 Test: Register -> Upload -> Assess -> Logout -> Login -> Verify Data Persists"""
    email = f"persist_{secrets.token_hex(4)}@careerlattice.ai"
    password = "SecurePassword123"
    
    # 1. Register
    reg = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Persistence Verification Student",
        "confirm_password": password
    })
    assert reg.status_code == 200
    token1 = reg.json()["token"]
    h1 = {"Authorization": f"Bearer {token1}"}
    
    # 2. Consent
    consent_res = client.post("/api/consent", json={"accepted": True}, headers=h1)
    assert consent_res.status_code == 200
    
    # 3. Resume Skills
    up_res = client.post("/api/resume/update-skills", json={"skills": ["Python", "FastAPI", "Docker", "PostgreSQL"]}, headers=h1)
    # If no resume exists yet, load sample or update
    demo_res = client.post("/api/demo/load", headers=h1)
    assert demo_res.status_code == 200
    
    # 4. Fetch dashboard before logout
    dash_before = client.get("/api/dashboard", headers=h1).json()
    assert dash_before["verified_count"] > 0
    skills_before = {s["skill_name"]: s["evidence_status"] for s in dash_before["skills"]}
    
    # 5. Complete a roadmap node
    comp_res = client.post("/api/roadmap/PostgreSQL/complete", json={"evidence_proof": "Completed B-Tree indexing lab"}, headers=h1)
    assert comp_res.status_code == 200
    
    # 6. Logout
    logout_res = client.post("/api/auth/logout", headers=h1)
    assert logout_res.status_code == 200
    
    # 7. Old token is now invalidated
    invalid_dash = client.get("/api/dashboard", headers=h1)
    assert invalid_dash.status_code == 401
    
    # 8. Login again
    login_res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    token2 = login_res.json()["token"]
    assert token2 != token1
    h2 = {"Authorization": f"Bearer {token2}"}
    
    # 9. Verify all data persisted across sessions!
    dash_after = client.get("/api/dashboard", headers=h2).json()
    assert dash_after["verified_count"] > 0
    skills_after = {s["skill_name"]: s["evidence_status"] for s in dash_after["skills"]}
    
    # Verify Python remained verified
    assert skills_after.get("Python") == "VERIFIED"
    # Verify PostgreSQL became verified after roadmap completion
    assert skills_after.get("PostgreSQL") == "VERIFIED"
    
    # Verify consent persisted
    me_res = client.get("/api/auth/me", headers=h2).json()
    assert me_res["consent_accepted"] is True
    
    # Verify roadmap persisted
    road_after = client.get("/api/roadmap", headers=h2).json()
    assert road_after["target_role"] is not None

def test_endpoint_aliases_and_subresources():
    email = f"alias_{secrets.token_hex(4)}@careerlattice.ai"
    password = "AliasPassword123"
    reg = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Alias Test Student",
        "confirm_password": password
    })
    token = reg.json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    
    # 1. /api/skills/self-assessment alias
    self_res = client.post("/api/skills/self-assessment", json={
        "ratings": {"Python": "Advanced", "Docker": "Developing"}
    }, headers=h)
    assert self_res.status_code == 200
    
    # 2. /api/assessment/start alias
    start_res = client.post("/api/assessment/start?skill=Python&level=Intermediate", headers=h)
    assert start_res.status_code == 200
    assert "questions" in start_res.json()
    assess_id = start_res.json()["assessment_id"]
    
    # 3. /api/assessment/{id}/answer alias
    q = start_res.json()["questions"][0]
    ans_res = client.post(f"/api/assessment/{assess_id}/answer", json={
        "skill_name": "Python",
        "question_id": q["id"],
        "student_answer": q["options"][0]
    }, headers=h)
    assert ans_res.status_code == 200
    
    # 4. /api/assessment/{id}/submit alias
    submit_res = client.post(f"/api/assessment/{assess_id}/submit", headers=h)
    assert submit_res.status_code == 200
    
    # 5. /api/assessment/{id} GET
    get_assess = client.get(f"/api/assessment/{assess_id}", headers=h)
    assert get_assess.status_code == 200
    
    # 6. /api/evidence GET and /api/evidence/{skill}
    ev_all = client.get("/api/evidence", headers=h)
    assert ev_all.status_code == 200
    assert "skills" in ev_all.json()
    
    ev_py = client.get("/api/evidence/Python", headers=h)
    assert ev_py.status_code == 200
    assert ev_py.json()["skill_name"] == "Python"
    
    # 7. /api/resources GET
    res_list = client.get("/api/resources", headers=h)
    assert res_list.status_code == 200
    assert res_list.json()["count"] > 0
    
    # 8. /api/github/rescan alias
    rescan_alias = client.post("/api/github/rescan", headers=h)
    assert rescan_alias.status_code == 200
    
    # 9. /api/jobs GET and /api/jobs/{id}/match
    jobs_res = client.get("/api/jobs", headers=h)
    assert jobs_res.status_code == 200
    first_job = jobs_res.json()["jobs"][0]
    job_id = first_job["id"]
    
    match_res = client.get(f"/api/jobs/{job_id}/match", headers=h)
    assert match_res.status_code == 200
    assert "match_percentage" in match_res.json()

def test_github_repo_url_parsing_and_sivabalan():
    email = f"siva_{secrets.token_hex(4)}@test.com"
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123",
        "full_name": "Sivabalan T"
    })
    token = reg_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test connecting with full repository URL as pasted by user
    gh_url = "https://github.com/siva2526k-art/hackatronix2.0"
    gh_res = client.post("/api/github/connect", json={"username_or_token": gh_url}, headers=headers)
    assert gh_res.status_code == 200
    data = gh_res.json()
    assert data["github_handle"] == "siva2526k-art"
    assert data["target_repo"] == "hackatronix2.0"
    repo_names = [r["name"] for r in data["repositories"]]
    assert "hackatronix2.0" in repo_names
    assert "SENTINEL" in repo_names

    # Test AST analysis with Sivabalan repos
    analyze_res = client.post("/api/github/analyze", json={
        "github_handle": "siva2526k-art",
        "selected_repos": ["hackatronix2.0", "SENTINEL", "careerlattice-ai"],
        "claimed_skills": ["Python", "FastAPI", "React", "Docker", "ChromaDB", "Zero-Trust", "Wazuh"]
    }, headers=headers)
    assert analyze_res.status_code == 200
    evidence = analyze_res.json()["evidence"]["skills_evidence"]
    assert evidence["Python"]["status"] == "VERIFIED"
    assert evidence["FastAPI"]["status"] == "VERIFIED"
    assert evidence["ChromaDB"]["status"] == "VERIFIED"
    assert evidence["Zero-Trust"]["status"] == "VERIFIED"


