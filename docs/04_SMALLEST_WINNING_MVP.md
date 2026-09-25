# 🎯 Phase 17 & Final Question: The Smallest Winning MVP

## What is the Smallest Technically Feasible Prototype That Proves the Core Innovation?

To win the hackathon with 100% stability, you do not need 50 career tracks or 10,000 skills. You need **one complete, flawless end-to-end slice**:

### The 1-Slice Prototype Scope
1. **Target Role**: *"Junior Backend Cloud Developer (Python & Cloud Infrastructure)"*.
2. **Pre-Seeded Graph**: Exactly **30 interconnected skill nodes** in Neo4j with strict `[:PREREQUISITE_OF]` edges.
3. **Ingestion Channel**:
   * A sample resume PDF parser (extracting 5–10 skills).
   * A lightweight GitHub parser that clones a single repo and searches `requirements.txt` and `.py` imports.
4. **Interactive UI**: A React Flow visual DAG showing:
   * **Green nodes**: Mastered & code-verified skills.
   * **Amber nodes**: Missing prerequisites injected by the graph.
   * **Grey nodes**: Locked advanced goals.
5. **Verified Learning Drawer**: Clicking any Amber node opens a sidebar showing verified NPTEL video timestamps and official documentation.

---

## The 30-Node Seed Graph (Demo Domain)

```
[Python Syntax & OOP] ──────► [Asyncio & Concurrency] ──┐
          │                                              │
          ▼                                              ▼
  [REST API Basics]   ──────►   [FastAPI Framework]   ──► [Microservices Architecture]
          │                              │                         ▲
          ▼                              ▼                         │
  [SQL & Relational DB] ─────►  [PostgreSQL Indexing] ──┐          │
                                         │              │          │
                                         ▼              ▼          │
                                  [Redis Caching] ──────┴──────────┘
                                         ▲
[Linux OS Fundamentals] ──► [Docker Containers] ──► [Kubernetes Orchestration]
```

---

## Sample Demo Data

### 1. Sample Student Resume (`Rohan_Sharma_Resume.pdf`)
* Claimed Skills: `Python`, `HTML/CSS`, `React`, `Docker`, `Microservices`, `Machine Learning`.

### 2. Sample Student GitHub (`rohan-sharma-dev/portfolio-api`)
* Actual Files: `app.py` (simple Flask routes with `sqlite3`).
* `requirements.txt`: `flask==2.3.0`, `requests`.
* Detected in AST: `Python`, `Flask`, `HTTP Basics`.
* Missing from Code: `Docker`, `Asyncio`, `Redis`, `Microservices`.

### 3. Generated Gap Output (JSON Payload)
```json
{
  "target_role": "Junior Backend Cloud Developer",
  "verified_skills": [
    {"name": "Python Syntax", "source": "GitHub AST", "confidence": 0.95},
    {"name": "REST API Basics", "source": "GitHub AST", "confidence": 0.90}
  ],
  "unverified_claimed_skills": [
    {"name": "Docker", "source": "Resume Text", "confidence": 0.30},
    {"name": "Microservices", "source": "Resume Text", "confidence": 0.25}
  ],
  "injected_prerequisites": [
    {"name": "Asyncio & Concurrency", "reason": "Mandatory prerequisite for high-throughput Microservices"},
    {"name": "PostgreSQL Indexing", "reason": "Database scaling fundamental before caching"}
  ],
  "roadmap_execution_order": [
    "Asyncio & Concurrency",
    "PostgreSQL Indexing",
    "Docker Containers",
    "Redis Caching",
    "Microservices Architecture"
  ]
}
```

---

## 24-Hour Implementation Priority Checklist

- [ ] **Hour 01–06**: Write `seed_graph.cypher` with the 30 nodes and relationships; test queries in Neo4j Browser.
- [ ] **Hour 07–12**: Build the FastAPI endpoint `/api/roadmap/generate` implementing Kahn's topological sort.
- [ ] **Hour 13–18**: Connect `@xyflow/react` to render the JSON graph with green/amber/grey node coloring.
- [ ] **Hour 19–22**: Build the lightweight GitHub AST parser using Python's native `ast` module and `requests`.
- [ ] **Hour 23–24**: Rehearse the 8-minute pitch and prepare an offline fallback video capture.
