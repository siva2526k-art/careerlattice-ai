# 🛠️ CareerLattice AI: Actual Prototype Technology Stack

> **Smart India Hackathon (SIH SE-02)** — *AI Skill-to-Career Readiness Platform*  
> **Production URL**: [https://careerlattice-ai.onrender.com](https://careerlattice-ai.onrender.com)  
> **Static Frontend**: [https://siva2526k-art.github.io/careerlattice-ai/](https://siva2526k-art.github.io/careerlattice-ai/)

---

## 🌟 Core / Key Technologies (At a Glance)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CAREERLATTICE AI CORE                           │
├─────────────────────┬──────────────────────────┬───────────────────────┤
│    BACKEND & API    │   DATABASE & STORAGE     │      FRONTEND         │
│  FastAPI (Python)   │  PostgreSQL 16 (Render)  │    Vanilla HTML5      │
│  Uvicorn Server     │  SQLAlchemy 2.0 ORM      │    CSS3 Styling       │
│  Pydantic V2        │  Alembic Migrations      │    Vanilla JS ES6+    │
│  Bearer Token Auth  │  SQLite Local Fallback   │    SPA Navigation     │
├─────────────────────┼──────────────────────────┼───────────────────────┤
│     AI & LLM        │     CODE POLYGRAPH       │   GRAPH & ROADMAP     │
│  Google Gemini 1.5  │  Python AST (Tree Walk)  │  NetworkX DiGraph     │
│  Flash (Adaptive Q) │  GitHub API + HTTPX      │  Topological Sort     │
│  Scenario Engine    │  Manifest Detection      │  nx.ancestors() Traversal
└─────────────────────┴──────────────────────────┴───────────────────────┘
```

### 1. **Backend Engine**: Python + FastAPI + Uvicorn
- **Why it matters**: Asynchronous, high-performance REST API with automatic OpenAPI Swagger documentation (`/docs`), strict Pydantic payload validation, and native CORS support.
- **Production Server**: Uvicorn running on Render.

### 2. **Production Database**: PostgreSQL 16 + SQLAlchemy 2.0
- **Why it matters**: Cloud-hosted PostgreSQL 16 database on Render providing real relational integrity, cascading foreign keys, and persistent state across:
  - Users, Consents, Resumes, and GitHub Accounts
  - Code-Grounding Polygraph Evidence Records
  - Adaptive Assessments, Roadmaps, and Job Match Catalogs
- **Local Fallback**: SQLite for offline and local testing without external database dependencies.

### 3. **AI & Adaptive Assessment**: Google Gemini 1.5 Flash
- **Why it matters**: Generates dynamic, situational assessment scenarios for claimed student skills on the fly to test real-world application rather than memorized trivia.

### 4. **Code-Grounding Polygraph**: Python AST (`ast.parse`, `ast.walk`) + GitHub API
- **Why it matters**: Directly analyzes student code repositories via AST inspection and manifest parsing (`requirements.txt`, `Dockerfile`, `package.json`, `tsconfig.json`) to confirm whether claimed skills are genuinely implemented in real code.

### 5. **Skill Graph & Prerequisite Ordering**: NetworkX `DiGraph` + Topological Sorting
- **Why it matters**: Constructs a prerequisite Directed Acyclic Graph (DAG), traverses prerequisite chains using `nx.ancestors()`, and sorts missing skills into an optimal learning roadmap with Kahn's topological sort.

### 6. **Zero-Dependency Lightweight Frontend**: Vanilla HTML5, CSS3 & ES6+ JavaScript
- **Why it matters**: High-performance Single Page Application (SPA) architecture with zero heavy build steps or bulky bundle overhead. Compatible with modern web standards and deployable anywhere (Render, GitHub Pages, Localhost).

---

## 📋 Complete Actual Prototype Technology Matrix

| Area | Actual Technology / Term | Implementation Role & Usage |
|:---|:---|:---|
| **Frontend** | **Vanilla HTML5** | Semantic structure, screen sections, modal dialogs, and accessible input elements |
| **Styling** | **CSS3** | Modern dark-mode aesthetic, CSS variables, glassmorphic cards, responsive flex/grid layouts |
| **Frontend logic** | **Vanilla JavaScript ES6+** | Client state machine, REST API bridge, interactive DOM manipulation, event listeners |
| **UI architecture** | **SPA-style navigation** | Seamless single-page application tab and screen routing with history management |
| **Backend** | **Python + FastAPI** | Asynchronous RESTful API services, dependency injection, and router modularity |
| **API server** | **Uvicorn** | High-throughput ASGI server hosting the production and local application |
| **Validation** | **Pydantic** | Strict schema validation, type annotations, and request/response models |
| **Database ORM** | **SQLAlchemy 2.0** | Declarative models, relational mappings, and transactional session management |
| **Database migration** | **Alembic** | Version-controlled database schema evolution and migration tooling |
| **Production DB** | **PostgreSQL 16** | Cloud relational database hosted on Render with persistent connection pooling |
| **Local DB fallback** | **SQLite** | Zero-configuration file-based relational storage for local development |
| **Authentication** | **Bearer Token Authentication** | HTTP Authorization header session tokens with per-user data isolation |
| **Password security** | **PBKDF2-HMAC-SHA256** | Cryptographic 100,000-iteration key derivation function for credential hashing |
| **Salt generation** | **Python `secrets`** | Cryptographically secure random salt generation per registered account |
| **Resume PDF parsing** | **PyMuPDF / Fitz** | High-speed binary PDF text stream extraction with zero visual hallucination |
| **Resume skill extraction** | **Regex / Regular Expressions** | Boundary-enforced taxonomy keyword matching across AI, SOC, and core engineering |
| **GitHub integration** | **GitHub API + HTTPX** | Asynchronous HTTP requests fetching public repos, branches, and manifest files |
| **Code analysis** | **Python AST (`ast.parse`, `ast.walk`)** | Abstract Syntax Tree traversal inspecting imports, decorators, and async functions |
| **Evidence engine** | **Rule-based / deterministic evidence aggregation** | 4-tier confidence scoring (Verified, Partial, Not Verified) combining resume, code, and quiz |
| **Skill graph** | **NetworkX `DiGraph`** | Directed Acyclic Graph encoding hierarchical skill prerequisites |
| **Graph traversal** | **`nx.ancestors()`** | Graph traversal identifying all unmastered foundational ancestors |
| **Roadmap ordering** | **Topological sorting** | Ordering gap skills into structured, achievable sequential learning milestones |
| **AI** | **Google Gemini 1.5 Flash** | Large language model API powering dynamic situational assessment generation |
| **Adaptive assessment** | **Dynamic scenario questions via Gemini** | Tailored scenario-based multiple-choice evaluation for student competencies |
| **Job matching** | **Set intersection / exact skill matching** | Deterministic comparison between student verified skills and live role requirements |
| **API testing** | **Pytest-style test modules / E2E tests** | 16-test unit/module suite (`pytest`) and 18-test live production verification suite |
| **CORS** | **FastAPI CORS middleware** | Cross-Origin Resource Sharing allowing both GitHub Pages and local frontend requests |
| **Deployment** | **Render** | Production Web Service and managed PostgreSQL 16 instance with automated CI/CD |
| **Frontend hosting** | **GitHub Pages** | Static alternative edge frontend hosting with automated git branch deployment |

---

## 🧪 Verification & Test Coverage

All technologies listed above are verified through our automated continuous verification suites:
1. `backend/tests/test_all_modules.py`: **9/9 tests passed**
2. `backend/tests/test_api_endpoints.py`: **7/7 tests passed**
3. `backend/tests/run_e2e_live_test.py`: **17/17 acceptance criteria passed**
4. `backend/tests/test_production_live.py`: **18/18 live cloud tests passed on Render**
