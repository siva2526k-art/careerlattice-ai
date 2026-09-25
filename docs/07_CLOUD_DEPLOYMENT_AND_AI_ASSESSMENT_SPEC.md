# ☁️ Cloud Deployment & AI Assessment Engine Specification

> **Platform Deployment**: Render.com (Web Service)  
> **Cloud Database**: Supabase (PostgreSQL)  
> **AI Assessment Engine**: Google Gemini API (`gemini-1.5-flash`)  
> **Job Aggregator**: Open-Source JobSpy (Embedded)

---

## 1. Cloud Infrastructure Overview

```
                                  [ INTERNET / JUDGES ]
                                             │
                                             ▼ HTTPS
                       [ Render Web Service: FastAPI + React SPA ]
                                             │
               ┌─────────────────────────────┼─────────────────────────────┐
               ▼                             ▼                             ▼
    [ Supabase PostgreSQL ]        [ Google Gemini AI ]          [ Open-Source JobSpy ]
    • User Authentication          • Technical Scenarios         • Scrapes LinkedIn, Indeed
    • Profile & Skill Evidence     • Code Answer Evaluation      • Zero API Key Required
    • AI Evaluated Levels          • Proficiency Calibration     • Embedded directly
    • Saved Roadmaps & Sessions      (Beginner -> Advanced)        in Python backend
```

---

## 2. Supabase Database Schema (PostgreSQL DDL)

Execute this SQL schema inside your **Supabase SQL Editor**:

```sql
-- 1. Users Table (Authentication & Identity)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. User Profiles Table
CREATE TABLE IF NOT EXISTS public.user_profiles (
    user_id UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    target_role TEXT DEFAULT 'Junior Backend Cloud Developer',
    github_handle TEXT,
    resume_extracted_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. User Skill Evidence Matrix (Triangulated Findings)
CREATE TABLE IF NOT EXISTS public.user_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    evidence_status TEXT CHECK (evidence_status IN ('VERIFIED', 'PARTIAL', 'NOT_VERIFIED')),
    confidence_score FLOAT NOT NULL, -- 0.0 to 1.0
    detected_source TEXT NOT NULL, -- 'RESUME', 'GITHUB_AST', 'AI_ASSESSMENT'
    ai_evaluated_level TEXT CHECK (ai_evaluated_level IN ('Beginner', 'Developing', 'Intermediate', 'Advanced', 'None')),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id, skill_name)
);

-- 4. AI Adaptive Assessment Logs
CREATE TABLE IF NOT EXISTS public.ai_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    skill_tested TEXT NOT NULL,
    question_prompt TEXT NOT NULL,
    student_response TEXT NOT NULL,
    ai_feedback TEXT NOT NULL,
    assigned_score INT CHECK (assigned_score BETWEEN 1 AND 10),
    assigned_level TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. Saved Roadmaps & State Continuity
CREATE TABLE IF NOT EXISTS public.user_roadmaps (
    user_id UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    roadmap_nodes JSONB NOT NULL,
    current_active_milestone TEXT,
    capstone_status TEXT DEFAULT 'NOT_STARTED',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
```

---

## 3. The AI Technical Interviewer & Level Analysis Workflow

### Prompt Engineering Specification for Google Gemini (`gemini-1.5-flash`)

#### Task 1: Generate Adaptive Scenario Questions
* **Trigger**: Triggered when a skill has a status of **PARTIAL** or **NOT_VERIFIED** (e.g., Docker or AWS).
* **System Prompt**:
  ```
  You are an expert technical interviewer evaluating an entry-level candidate for the role of Junior Backend Cloud Developer.
  The candidate claimed experience with "{skill_name}".
  Our static code analysis found: "{ast_evidence_summary}".
  Generate 2 concise, practical technical questions testing real-world debugging or architectural reasoning (not basic syntax trivia).
  Return JSON: [{"question_id": 1, "question": "..."}, {"question_id": 2, "question": "..."}]
  ```

#### Task 2: Evaluate Answers & Calibrate Level
* **Input**: Candidate's submitted text/code response.
* **System Prompt**:
  ```
  You are a principal engineer grading a candidate's answer to the technical scenario: "{question}".
  Candidate Answer: "{student_response}".
  Evaluate the technical depth, practical understanding, and correctness.
  Assign:
  1. Score (1-10)
  2. Proficiency Level: "Beginner" (basic syntax only), "Developing" (understands concepts, misses production details), "Intermediate" (solid debugging & production patterns), or "Advanced".
  3. Actionable Rationale (1-2 sentences on what they need to learn next).
  Return JSON format: {"score": 7, "level": "Developing", "rationale": "..."}
  ```

---

## 4. Render Deployment Configuration (`render.yaml`)

```yaml
services:
  - type: web
    name: careerlattice-ai
    env: python
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
```

---

## 5. Live Presentation Flow for Judges

1. **Open Live URL**: `https://careerlattice-ai.onrender.com`
2. **Login / Register**: Data persists to Supabase in real time.
3. **Audit**: System deterministic parser pulls resume text + GitHub AST code.
4. **AI Assessment**: Gemini asks targeted questions $\rightarrow$ grades level into Supabase.
5. **Interactive Graph**: React Flow renders Green / Amber / Grey nodes with NPTEL links.
6. **Live Jobs**: Embedded JobSpy displays active openings on LinkedIn and Indeed.
