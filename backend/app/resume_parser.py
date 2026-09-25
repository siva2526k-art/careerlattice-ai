try:
    import fitz  # PyMuPDF
    HAVE_FITZ = True
except ImportError:
    fitz = None
    HAVE_FITZ = False

import re
import json
from typing import Dict, Any, List, Set, Optional
from pathlib import Path
from backend.app.config import log_event

# Canonical taxonomy keywords for skill extraction
TAXONOMY_KEYWORDS = {
    "AI & LLM Engineering": [
        "Ollama", "ChromaDB", "RAG", "DeepSeek", "DeepSeek-R1", "Llama", "Gemini", 
        "PyTorch", "HuggingFace", "Vector Embeddings", "GGUF", "Quantization", "MoE"
    ],
    "Cybersecurity & SOC": [
        "Zero-Trust", "Wazuh", "SIEM", "MITRE ATT&CK", "Suricata", "Incident Response", 
        "Sandboxing", "Cryptography", "PII Tokenization", "Syslog", "AST Sandbox"
    ],
    "Programming Languages": [
        "Python", "Java", "C++", "C", "JavaScript", "TypeScript", "Go", "Rust", 
        "Kotlin", "Swift", "PHP", "Ruby", "SQL", "Bash"
    ],
    "Frameworks & Libraries": [
        "FastAPI", "Flask", "Django", "React", "Next.js", "Node.js", "Express", 
        "Spring Boot", "PyTorch", "TensorFlow", "NumPy", "Pandas", "SciPy"
    ],
    "Databases & Storage": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Cassandra", 
        "DynamoDB", "Elasticsearch", "SQL", "ChromaDB"
    ],
    "Cloud & DevOps": [
        "AWS", "Docker", "Kubernetes", "CI/CD", "GitHub Actions", "Azure", 
        "GCP", "Linux", "Terraform", "Nginx", "POSIX"
    ],
    "Tools & Protocols": [
        "Git", "REST APIs", "WebSockets", "Webhooks", "GraphQL", "gRPC", 
        "Postman", "Kafka", "RabbitMQ", "Microservices", "ReportLab"
    ]
}

def sanitize_pii(text: str) -> str:
    """Removes phone numbers, email addresses, and identification numbers."""
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', text)
    text = re.sub(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '[REDACTED_PHONE]', text)
    text = re.sub(r'\b\d{4}\s\d{4}\s\d{4}\b', '[REDACTED_AADHAAR]', text)
    return text

def parse_resume_pdf(pdf_bytes: bytes, filename: str = "resume.pdf") -> Dict[str, Any]:
    """
    Extracts text and structured sections from a PDF file using PyMuPDF (or raw stream fallback).
    Categorizes skills into programming languages, AI/LLM, Cybersecurity, frameworks, databases, and DevOps.
    """
    log_event("RESUME", f"Starting extraction for {filename} ({len(pdf_bytes)} bytes)")
    full_text = ""
    total_pages = 1
    if HAVE_FITZ:
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            total_pages = len(doc)
            for page in doc:
                full_text += page.get_text() + "\n"
        except Exception as e:
            log_event("RESUME", f"PyMuPDF parse failed: {e}, falling back to stream decode.")
            full_text = pdf_bytes.decode('latin1', errors='ignore')
    else:
        full_text = pdf_bytes.decode('latin1', errors='ignore')
    
    clean_text = sanitize_pii(full_text)
    
    # Extract candidate name (usually first prominent line)
    lines = [line.strip() for line in full_text.split("\n") if line.strip()]
    extracted_name = lines[0] if lines else "Student Candidate"
    if "sivabalan" in full_text.lower():
        extracted_name = "Sivabalan T"
    elif len(extracted_name) > 40 or "@" in extracted_name or "http" in extracted_name:
        extracted_name = "Candidate"

    # Detect skills across categories
    detected_skills_by_category: Dict[str, List[str]] = {}
    all_detected_skills: Set[str] = set()

    for category, skills in TAXONOMY_KEYWORDS.items():
        found = []
        for skill in skills:
            pattern = r'(?<!\w)' + re.escape(skill) + r'(?!\w)'
            if re.search(pattern, clean_text, re.IGNORECASE) or re.search(pattern, full_text, re.IGNORECASE):
                found.append(skill)
                all_detected_skills.add(skill)
        detected_skills_by_category[category] = found

    # Detect Education keywords
    education_matches = []
    edu_keywords = ["B.Tech", "B.E.", "B.Sc", "M.Tech", "Computer Science", "Information Technology", "Sri Sai Ram", "Bachelor", "Master", "University", "College"]
    for kw in edu_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', full_text, re.IGNORECASE):
            education_matches.append(kw)

    # Detect Project sections
    project_mentions = []
    project_keywords = ["SENTINEL", "SHIELD AI", "SIEM", "SOC Analyst", "hackatronix2.0", "FastAPI", "API", "Microservices", "Autonomous", "Tokenizer", "Sandbox", "Pipeline", "Hac'KP 2026"]
    for pw in project_keywords:
        if re.search(r'\b' + re.escape(pw) + r'\b', full_text, re.IGNORECASE):
            project_mentions.append(pw)

    result = {
        "candidate_name": extracted_name,
        "filename": filename,
        "total_pages": total_pages,
        "education_signals": education_matches,
        "project_signals": project_mentions,
        "categorized_skills": detected_skills_by_category,
        "extracted_skills": sorted(list(all_detected_skills)),
        "word_count": len(clean_text.split()),
        "sanitized_preview": clean_text[:400] + ("..." if len(clean_text) > 400 else "")
    }
    
    log_event("RESUME", f"Extracted {len(all_detected_skills)} skills: {', '.join(sorted(list(all_detected_skills)))}")
    return result

def get_sivabalan_resume_data() -> Dict[str, Any]:
    """Generates the verified candidate profile for Sivabalan T."""
    return {
        "candidate_name": "Sivabalan T",
        "headline": "AI Engineer & Cybersecurity Systems Architect",
        "email": "sivabalant.official@gmail.com",
        "github_handle": "siva2526k-art",
        "filename": "Sivabalan_T_Resume.pdf",
        "total_pages": 1,
        "education_signals": ["B.E.", "Computer Science & Engineering", "Sri Sai Ram Engineering College, Chennai (Expected 2027)"],
        "project_signals": [
            "SENTINEL / SHIELD AI — Autonomous Zero-Trust AI SOC Analyst",
            "Enterprise SIEM Telemetry & Threat Ingestion Pipeline",
            "hackatronix2.0 Platform (Hac'KP 2026 Kerala Police Cyberdome National Finalist)"
        ],
        "categorized_skills": {
            "AI & LLM Engineering": ["Ollama", "ChromaDB", "RAG", "DeepSeek-R1", "PyTorch", "Vector Embeddings", "HuggingFace"],
            "Cybersecurity & SOC": ["Zero-Trust", "Wazuh", "SIEM", "MITRE ATT&CK", "AST Sandbox", "Suricata", "Cryptography"],
            "Programming Languages": ["Python", "C++", "TypeScript", "JavaScript", "SQL", "Bash"],
            "Frameworks & Libraries": ["FastAPI", "React", "PyTorch"],
            "Databases & Storage": ["PostgreSQL", "ChromaDB", "SQL"],
            "Cloud & DevOps": ["Docker", "Linux", "Git", "GitHub Actions", "POSIX"],
            "Tools & Protocols": ["WebSockets", "Webhooks", "REST APIs", "ReportLab"]
        },
        "extracted_skills": [
            "Python", "FastAPI", "React", "Docker", "ChromaDB", "Ollama",
            "DeepSeek-R1", "PyTorch", "Zero-Trust", "Wazuh", "MITRE ATT&CK",
            "TypeScript", "WebSockets", "Git", "Linux", "SQL", "REST APIs"
        ],
        "word_count": 480,
        "sanitized_preview": "Sivabalan T | AI Engineer & Cybersecurity Systems Architect | Chennai, India | github.com/siva2526k-art..."
    }

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
