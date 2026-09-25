import fitz  # PyMuPDF
import re
import json
from typing import Dict, Any, List, Set
from pathlib import Path
from backend.app.config import log_event

# Canonical taxonomy keywords for skill extraction
TAXONOMY_KEYWORDS = {
    "Programming Languages": ["Python", "Java", "C++", "C", "JavaScript", "TypeScript", "Go", "Rust", "Kotlin", "Swift", "PHP", "Ruby"],
    "Frameworks & Libraries": ["FastAPI", "Flask", "Django", "React", "Next.js", "Node.js", "Express", "Spring Boot", "PyTorch", "TensorFlow", "NumPy", "Pandas", "SciPy"],
    "Databases & Storage": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Cassandra", "DynamoDB", "Elasticsearch", "SQL"],
    "Cloud & DevOps": ["AWS", "Docker", "Kubernetes", "CI/CD", "GitHub Actions", "Azure", "GCP", "Linux", "Terraform", "Nginx"],
    "Tools & Protocols": ["Git", "REST APIs", "GraphQL", "gRPC", "Postman", "Kafka", "RabbitMQ", "Microservices"]
}

def sanitize_pii(text: str) -> str:
    """Removes phone numbers, email addresses, and identification numbers."""
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', text)
    text = re.sub(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '[REDACTED_PHONE]', text)
    text = re.sub(r'\b\d{4}\s\d{4}\s\d{4}\b', '[REDACTED_AADHAAR]', text)
    return text

def parse_resume_pdf(pdf_bytes: bytes, filename: str = "resume.pdf") -> Dict[str, Any]:
    """
    Extracts text and structured sections from a PDF file using PyMuPDF.
    Categorizes skills into programming languages, frameworks, databases, cloud, and tools.
    """
    log_event("RESUME", f"Starting extraction for {filename} ({len(pdf_bytes)} bytes)")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    
    clean_text = sanitize_pii(full_text)
    
    # Extract candidate name (usually first prominent line)
    lines = [line.strip() for line in full_text.split("\n") if line.strip()]
    extracted_name = lines[0] if lines else "Student Candidate"
    if len(extracted_name) > 40 or "@" in extracted_name or "http" in extracted_name:
        extracted_name = "Candidate"

    # Detect skills across categories
    detected_skills_by_category: Dict[str, List[str]] = {}
    all_detected_skills: Set[str] = set()

    for category, skills in TAXONOMY_KEYWORDS.items():
        found = []
        for skill in skills:
            # Word boundary regex search (case-insensitive for safety, exact word matching)
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, clean_text, re.IGNORECASE):
                found.append(skill)
                all_detected_skills.add(skill)
        detected_skills_by_category[category] = found

    # Detect Education keywords
    education_matches = []
    edu_keywords = ["B.Tech", "B.E.", "B.Sc", "M.Tech", "Computer Science", "Information Technology", "Physics", "Bachelor", "Master", "University", "College"]
    for kw in edu_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', clean_text, re.IGNORECASE):
            education_matches.append(kw)

    # Detect Project sections
    project_mentions = []
    project_keywords = ["API", "Microservices", "Autonomous", "Robot", "Simulator", "Dashboard", "Machine Learning", "Portfolio", "Pipeline"]
    for pw in project_keywords:
        if re.search(r'\b' + re.escape(pw) + r'\b', clean_text, re.IGNORECASE):
            project_mentions.append(pw)

    result = {
        "candidate_name": extracted_name,
        "filename": filename,
        "total_pages": len(doc),
        "education_signals": education_matches,
        "project_signals": project_mentions,
        "categorized_skills": detected_skills_by_category,
        "extracted_skills": sorted(list(all_detected_skills)),
        "word_count": len(clean_text.split()),
        "sanitized_preview": clean_text[:400] + ("..." if len(clean_text) > 400 else "")
    }
    
    log_event("RESUME", f"Extracted {len(all_detected_skills)} skills: {', '.join(sorted(list(all_detected_skills)))}")
    return result

def get_demo_resume_data() -> Dict[str, Any]:
    """Generates the standardized Rohan Sharma demo candidate profile."""
    return {
        "candidate_name": "Rohan Sharma",
        "filename": "Rohan_Sharma_Resume.pdf",
        "total_pages": 1,
        "education_signals": ["B.Tech", "Computer Science & Engineering", "Tier-3 Institute"],
        "project_signals": ["FastAPI REST Service", "Microservices Portfolio", "Docker Container"],
        "categorized_skills": {
            "Programming Languages": ["Python", "JavaScript", "SQL"],
            "Frameworks & Libraries": ["FastAPI", "React"],
            "Databases & Storage": ["PostgreSQL", "MongoDB", "SQL"],
            "Cloud & DevOps": ["Docker", "AWS", "Git", "Linux", "Kubernetes"],
            "Tools & Protocols": ["REST APIs", "Git"]
        },
        "extracted_skills": [
            "Python", "FastAPI", "SQL", "PostgreSQL", "MongoDB",
            "Docker", "AWS", "Kubernetes", "Git", "Linux", "REST APIs", "React"
        ],
        "word_count": 350,
        "sanitized_preview": "Rohan Sharma | 3rd Year B.Tech CSE | Aspirant Backend & Cloud Engineer..."
    }
