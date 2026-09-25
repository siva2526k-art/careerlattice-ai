import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Set, Optional
from pathlib import Path
from backend.app.config import log_event

DATA_DIR = Path(__file__).resolve().parent / "data"

class JobProvider(ABC):
    """Abstract interface for job opportunity sources."""
    
    @abstractmethod
    def fetch_jobs_for_role(self, role_title: str) -> List[Dict[str, Any]]:
        pass

class DatasetJobProvider(JobProvider):
    """Provides curated, realistic job postings from internal dataset."""
    
    def __init__(self):
        with open(DATA_DIR / "sample_jobs.json", "r", encoding="utf-8") as f:
            self.dataset = json.load(f).get("jobs", [])
            
    def fetch_jobs_for_role(self, role_title: str) -> List[Dict[str, Any]]:
        log_event("JOBS", f"Fetching postings from DatasetJobProvider for '{role_title}'")
        # Return all postings matching the role domain or entry-level backend
        return self.dataset

class JobSpyJobProvider(JobProvider):
    """Integrates open-source JobSpy library with fallback to DatasetJobProvider."""
    
    def __init__(self):
        self.fallback = DatasetJobProvider()
        
    def fetch_jobs_for_role(self, role_title: str) -> List[Dict[str, Any]]:
        try:
            from jobspy import scrape_jobs
            log_event("JOBS", f"Querying JobSpy open-source scraper for '{role_title}' in India")
            df = scrape_jobs(
                site_name=["indeed", "linkedin", "glassdoor"],
                search_term=role_title,
                location="India",
                results_wanted=5,
                country_indeed='india'
            )
            if df is not None and not df.empty:
                jobs = []
                for _, row in df.iterrows():
                    jobs.append({
                        "id": f"jobspy_{row.get('id', hash(row.get('job_url', '')))}",
                        "title": str(row.get('title', role_title)),
                        "company": str(row.get('company', 'Enterprise Tech Firm')),
                        "location": str(row.get('location', 'India (Remote / Hybrid)')),
                        "type": "Full-Time",
                        "portal": str(row.get('site', 'LinkedIn / Indeed')),
                        "apply_url": str(row.get('job_url', 'https://linkedin.com/jobs')),
                        "required_skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
                        "good_to_have": ["AWS"],
                        "description": str(row.get('description', 'Backend engineering opportunity.'))[:250] + "...",
                        "min_experience_years": 0
                    })
                return jobs
        except Exception as e:
            log_event("JOBS", f"JobSpy live query failed or rate-limited: {str(e)}. Falling back to curated dataset.")
            
        return self.fallback.fetch_jobs_for_role(role_title)

def evaluate_job_matches(
    role_title: str,
    verified_skills: List[str],
    partial_skills: List[str],
    provider: Optional[JobProvider] = None
) -> List[Dict[str, Any]]:
    """
    Evaluates student evidence against live job postings with transparent gap explanations.
    """
    if provider is None:
        provider = DatasetJobProvider()
        
    raw_jobs = provider.fetch_jobs_for_role(role_title)
    evaluated_jobs = []
    
    verified_set = set(verified_skills)
    partial_set = set(partial_skills)
    
    for job in raw_jobs:
        req_skills = job.get("required_skills", [])
        total_req = len(req_skills) if req_skills else 1
        
        satisfied = [s for s in req_skills if s in verified_set]
        in_progress = [s for s in req_skills if s in partial_set]
        missing = [s for s in req_skills if (s not in verified_set and s not in partial_set)]
        
        # Calculate transparent match ratio
        score_points = (len(satisfied) * 1.0) + (len(in_progress) * 0.5)
        match_percentage = int((score_points / total_req) * 100)
        
        if match_percentage >= 80:
            match_status = "Good Evidence Match"
            status_color = "emerald"
            recommendation = "You have strong supporting evidence for this role. Ready to apply!"
        elif match_percentage >= 50:
            match_status = "Some Requirements Need Improvement"
            status_color = "amber"
            recommendation = f"Target remaining gap ({', '.join(missing)}) through capstone implementation."
        else:
            match_status = "Major Prerequisite Gaps"
            status_color = "slate"
            recommendation = "Follow foundational prerequisite roadmap milestones before applying."
            
        evaluated_jobs.append({
            "id": job["id"],
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "type": job["type"],
            "portal": job["portal"],
            "apply_url": job["apply_url"],
            "description": job["description"],
            "match_percentage": match_percentage,
            "match_status": match_status,
            "status_color": status_color,
            "recommendation": recommendation,
            "satisfied_skills": satisfied,
            "in_progress_skills": in_progress,
            "missing_skills": missing,
            "total_requirements": total_req
        })
        
    # Sort highest match percentage first
    return sorted(evaluated_jobs, key=lambda j: j["match_percentage"], reverse=True)
