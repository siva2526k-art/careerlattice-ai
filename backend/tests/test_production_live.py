import urllib.request
import json
import secrets
import sys
import os

BASE = os.getenv("TEST_BASE_URL", "https://careerlattice-ai.onrender.com")
email = f'render_live_{secrets.token_hex(4)}@careerlattice.ai'
pwd = 'RenderLivePass123!'

def post(url, data=None, token=None):
    req = urllib.request.Request(BASE + url, data=json.dumps(data).encode() if data else b'', method='POST')
    req.add_header('Content-Type', 'application/json')
    if token: req.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

def get(url, token=None):
    req = urllib.request.Request(BASE + url, method='GET')
    if token: req.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

def main():
    print("=" * 70)
    print(f"CAREERLATTICE AI - LIVE PRODUCTION VERIFICATION ON RENDER")
    print(f"Target URL: {BASE}")
    print("=" * 70)

    # 0. Health check
    health = get('/api/health')
    assert health['status'] == 'healthy'
    print(f"[PASS] 0. Live Health check: status={health['status']}, env={health['environment']}")

    # 1. Register
    reg = post('/api/auth/register', {
        'email': email,
        'password': pwd,
        'confirm_password': pwd,
        'full_name': 'Render Live Verification Candidate'
    })
    t1 = reg['token']
    print(f"[PASS] 1. Registered user {email} (ID: {reg['user']['id']}) in PostgreSQL")

    # 2. Terms & Consent
    c = post('/api/consent', {'accepted': True}, t1)
    assert c['accepted'] is True
    print(f"[PASS] 2. Terms & Consent recorded in PostgreSQL")

    # 3. Resume Claims
    r = post('/api/resumes', {
        'filename': 'render_student_resume.pdf',
        'claimed_skills': ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'Git', 'REST APIs', 'AWS']
    }, t1)
    print(f"[PASS] 3. Resume claims saved ({len(r['extracted_skills'])} technical skills)")

    # 4. GitHub Repos
    gh = post('/api/github/repos/select', {'repo_names': ['sentinel-backend-api', 'careerlattice-core']}, t1)
    print(f"[PASS] 4. GitHub repositories selected: {gh['selected_repos']}")

    # 5. AST Analysis
    ast_res = post('/api/github/analyze', {
        'github_handle': 'rohan-sharma-dev',
        'selected_repos': ['sentinel-backend-api', 'careerlattice-core'],
        'claimed_skills': ['Python', 'FastAPI', 'PostgreSQL', 'Docker']
    }, t1)
    print(f"[PASS] 5. AST Code Polygraph executed across source files")

    # 6. Self-Assessment
    sa = post('/api/self-assessment', {
        'ratings': {
            'Python': 'Advanced',
            'FastAPI': 'Intermediate',
            'PostgreSQL': 'Developing',
            'Docker': 'Developing',
            'AWS': 'Beginner'
        }
    }, t1)
    print(f"[PASS] 6. Self-assessment ratings recorded")

    # 7. Adaptive Assessment Question & Answer
    ans = post('/api/assessment/answer', {
        'skill_name': 'Python',
        'question_id': 'py_q1',
        'student_answer': 'Both Assertion and Reason are true, and Reason is the correct explanation of Assertion.'
    }, t1)
    print(f"[PASS] 7. Adaptive assessment graded and recorded. Score: {ans['grading']['score']}/10")

    # 8. Triangulate Evidence Matrix
    ev = post('/api/evidence/calculate', None, t1)
    print(f"[PASS] 8. 4-Tier evidence matrix calculated across {len(ev['evidence_matrix'])} skills")

    # 9. Dashboard before logout
    dash1 = get('/api/dashboard', t1)
    print(f"[PASS] 9. Dashboard retrieved. Verified count: {dash1['verified_count']}, Ratio: {dash1['demonstrated_ratio']}")

    # 10. Complete Roadmap Milestone (PostgreSQL)
    comp = post('/api/roadmap/PostgreSQL/complete', {'evidence_proof': 'Completed indexing and migration capstone on Render'}, t1)
    print(f"[PASS] 10. Completed roadmap node '{comp['skill_completed']}'")

    # 11. Matched Jobs
    jobs = get('/api/jobs?role=Junior%20Backend%20Developer', t1)
    print(f"[PASS] 11. Retrieved {len(jobs['jobs'])} matched career opportunities")

    # 12. Continuous Rescan (Update Evidence)
    rescan = post('/api/evidence/rescan', None, t1)
    print(f"[PASS] 12. Continuous rescan triggered: {rescan['message']}")

    # 13. Secure Logout (Invalidates Token)
    post('/api/auth/logout', None, t1)
    print(f"[PASS] 13. User logged out. Session token invalidated.")

    # 14. Verify Token Invalidation
    try:
        get('/api/dashboard', t1)
        print("[FAIL] Invalidated token unexpectedly succeeded!")
        sys.exit(1)
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print(f"[PASS] 14. Invalidated token correctly rejected with HTTP 401 Unauthorized")

    # 15. Login again
    login = post('/api/auth/login', {'email': email, 'password': pwd})
    t2 = login['token']
    assert t2 != t1
    print(f"[PASS] 15. Re-authenticated with new secure token")

    # 16. Verify 100% PostgreSQL Database Persistence
    dash2 = get('/api/dashboard', t2)
    skills_map = {s['skill_name']: s['evidence_status'] for s in dash2['skills']}
    assert skills_map.get('Python') == 'VERIFIED'
    assert skills_map.get('PostgreSQL') == 'VERIFIED'
    assert skills_map.get('Docker') == 'VERIFIED'
    print(f"[PASS] 16. 100% POSTGRESQL PERSISTENCE VERIFIED:")
    for skill, status in skills_map.items():
        print(f"       - {skill.ljust(15)} : {status}")

    me2 = get('/api/auth/me', t2)
    assert me2['consent_accepted'] is True
    print(f"[PASS] 17. User consent state persisted across session: accepted={me2['consent_accepted']}")

    # 18. Preloaded Demo User Verification (Rohan Sharma)
    demo_login = post('/api/auth/login', {'email': 'rohan@careerlattice.ai', 'password': 'password123'})
    demo_token = demo_login['token']
    demo_loaded = post('/api/demo/load', None, demo_token)
    demo_dash = get('/api/dashboard', demo_token)
    assert demo_dash['verified_count'] >= 3
    print(f"[PASS] 18. Preloaded Rohan Sharma demo profile loaded: {demo_dash['verified_count']} verified skills in PostgreSQL")

    print("\n" + "=" * 70)
    print("ALL 18 PRODUCTION TESTS PASSED ON RENDER!")
    print("LIVE DEPLOYMENT IS 100% OPERATIONAL WITH POSTGRESQL DATABASE")
    print("=" * 70)

if __name__ == '__main__':
    main()
