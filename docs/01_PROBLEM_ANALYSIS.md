# 📑 Phase 1 & 2: Comprehensive Problem & Market Analysis

## Problem Statement Code: SE-02
**Title**: AI Skill-to-Career Readiness Platform  
**Target Ministry**: Ministry of Skill Development and Entrepreneurship (MSDE) / AICTE / NSDC

---

## 1. Deep Problem Formulation

### 1.1 The Exact Dilemma
In India, over 1.5 million engineers graduate annually, yet industry employability reports (such as Wheebox India Skills Report and NASSCOM studies) consistently indicate that **fewer than 45–50% of engineering graduates are directly employable** in technical roles without substantial corporate re-training.

Students spend 200–500+ hours in uncurated learning ("tutorial hell") attempting to bridge this gap. However:
1. **They lack an objective baseline**: Resumes are filled with buzzwords learned superficially from 10-hour crash courses.
2. **They lack prerequisite awareness**: They attempt advanced frameworks (e.g., Kubernetes, LangChain) without mastering foundational concepts (Linux networking, Python concurrency).
3. **They face academic lag**: University curricula change every 3–5 years, whereas industry technology shifts within 6–12 months.
4. **They learn from unverified, clickbait sources**: Free video playlists often present outdated practices, incomplete projects, and no verifiable problem-solving assessments.

### 1.2 The Root Causes
* **Information Asymmetry**: Corporate job descriptions list inflated 20-item wish lists for entry-level roles, confusing students about what is truly mandatory versus optional.
* **Non-Standard Terminology**: Students write *"built REST APIs in Express"*, while ATS systems look for *"Node.js, Express.js, Microservices, API Security"*. Without an ontological bridge, students get filtered out.
* **Incentive Misalignment in EdTech**: Commercial platforms (Udemy, Coursera) monetize video watch time and certificate sales rather than minimizing the student's *time-to-competence*.

---

## 2. Stakeholder Analysis

```
                    ┌────────────────────────────┐
                    │     Government & NEP 2020  │
                    │   (AICTE, MSDE, NASSCOM)   │
                    └─────────────┬──────────────┘
                                  │ Directives & Frameworks
                                  ▼
┌─────────────────────────┐  Lattice AI   ┌─────────────────────────┐
│       Students          │◄─────────────►│    College TPOs &       │
│ (Tier-2/3 Undergrads)   │               │       Deans             │
└───────────┬─────────────┘               └───────────┬─────────────┘
            │                                         │
            │ Competent Candidates                    │ Aligned Curriculum
            ▼                                         ▼
┌───────────────────────────────────────────────────────────────────┐
│                   Hiring Industry & Corporates                    │
└───────────────────────────────────────────────────────────────────┘
```

* **Students**: Gain an honest, transparent roadmap that cuts out irrelevant topics and saves hundreds of wasted hours.
* **Training & Placement Officers (TPOs)**: Gain institutional visibility into departmental skill deficits to organize high-ROI bootcamps.
* **Recruiters & Enterprises**: Receive candidates whose listed competencies are backed by actual code inspection rather than empty resume buzzwords.
* **Government Bodies**: Measure and accelerate the real-world adoption of high-quality national educational assets (NPTEL, SWAYAM, SIDH).

---

## 3. Existing Solution Analysis & The "Solution Gap"

| Solution | Model | Technology | Strengths | Fatal Limitations |
| :--- | :--- | :--- | :--- | :--- |
| **roadmap.sh** | Open-source community roadmaps | Markdown, React Flow, JSON | Clean visual presentation, high developer trust | Completely static; zero personalization; no awareness of student resume or GitHub code |
| **LinkedIn Career Explorer** | Commercial professional network | Proprietary economic graph, collaborative filtering | Millions of real-time job listings | Closed ecosystem; pushes paid subscriptions; black-box scoring with no actionable prerequisite tree |
| **Skill India Digital Hub (SIDH)** | Government skills portal | Relational SQL databases, job boards | National reach, official Qualification Packs (QP/NOS) | No automated resume parsing; no dynamic learning pathways or real-time codebase verification |
| **Lightcast / SkyHive** | Enterprise labor market intelligence | NLP knowledge graphs, enterprise APIs | World-class skill taxonomies and market trends | Expensive B2B enterprise pricing; inaccessible to individual college students and budget institutions |
| **Standard Hackathon ATS Parsers** | Typical student projects | Basic TF-IDF or raw OpenAI API prompt | Easy to build in a few hours | Superficial string matching; zero prerequisite logic; hallucinated course links; easily tricked by keyword stuffing |

### Why Has This Problem Not Been Solved Well Yet?
1. **The Keyword Fallacy**: Treating skills as independent strings rather than nodes in a directed dependency graph.
2. **The "Resume Trust" Gap**: Accepting resume text as ground truth without validating candidate code repositories.
3. **The Unbounded LLM Trap**: Relying on unconstrained generative AI models that hallucinate broken links, dead libraries, and nonsensical prerequisite sequences.
