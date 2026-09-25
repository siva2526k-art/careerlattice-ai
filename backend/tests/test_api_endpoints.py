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
