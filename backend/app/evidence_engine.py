from typing import Dict, Any, List, Optional
from backend.app.config import log_event

def calculate_evidence_proficiency(
    skill_name: str,
    resume_claimed: bool,
    github_evidence: Optional[Dict[str, Any]],
    self_level: Optional[str],
    assessment_score: Optional[int] = None, # 0 to 10
    has_practical_project: bool = False
) -> Dict[str, Any]:
    """
    Deterministic rule-based evidence aggregation layer.
    Combines:
    1. Resume evidence (Claimed vs Unclaimed)
    2. GitHub code evidence (Strong / Partial / Insufficient)
    3. Self-assessment (Beginner, Developing, Intermediate, Advanced)
    4. Adaptive assessment score (0 to 10)
    
    Produces:
    - evidence_status: 'VERIFIED', 'PARTIAL', 'NOT_VERIFIED'
    - final_level: 'Beginner', 'Developing', 'Intermediate', 'Advanced'
    - confidence: 'High', 'Medium', 'Low'
    - transparent_rationale: Detailed textual explanation of WHY this level was assigned.
    """
    
    # 1. Inspect GitHub signal
    gh_status = "NOT_VERIFIED"
    gh_files = []
    if github_evidence:
        gh_status = github_evidence.get("status", "NOT_VERIFIED")
        gh_files = github_evidence.get("supporting_files", [])

    # 2. Normalize assessment score
    score = assessment_score if assessment_score is not None else 5
    self_decl = self_level or "Developing"

    # 3. Rule-based level and status determination
    if gh_status == "VERIFIED" and (score >= 7 or has_practical_project):
        status = "VERIFIED"
        confidence = "High"
        final_level = "Advanced" if (self_decl == "Advanced" and score >= 8) else "Intermediate"
        rationale = f"Strong implementation evidence verified in code ({', '.join(gh_files) if gh_files else 'AST patterns'}), confirmed by solid assessment score ({score}/10)."

    elif gh_status == "VERIFIED" and score < 7:
        status = "VERIFIED"
        confidence = "Medium"
        final_level = "Developing"
        rationale = f"Code implementation detected in repositories, but theoretical or edge-case assessment ({score}/10) indicates room for deeper conceptual mastery."

    elif gh_status == "PARTIAL":
        status = "PARTIAL"
        confidence = "Medium"
        final_level = "Developing"
        rationale = f"Preliminary code artifacts detected in repository ({', '.join(gh_files)}), but production patterns (multi-stage builds, tests, or orchestration) are not yet demonstrated."

    else:
        # Insufficient GitHub evidence
        if score >= 8:
            status = "PARTIAL"
            confidence = "Medium"
            final_level = "Developing"
            rationale = f"Strong assessment performance ({score}/10) demonstrates conceptual knowledge, but practical repository code is not yet linked. Build and commit a project to achieve full verification."
        else:
            status = "NOT_VERIFIED"
            confidence = "Low" if score < 4 else "Medium"
            final_level = "Beginner" if score < 5 else "Developing"
            rationale = f"Insufficient practical code evidence found in submitted repositories. (Note: 'Not Verified' means insufficient evidence was found—not that you lack capability)."

    result = {
        "skill_name": skill_name,
        "resume_claimed": resume_claimed,
        "self_declared_level": self_decl,
        "github_code_evidence": gh_status,
        "supporting_files": gh_files,
        "assessment_score": score,
        "evidence_status": status,
        "final_level": final_level,
        "confidence": confidence,
        "rationale": rationale
    }

    log_event("EVIDENCE", f"Calculated proficiency for '{skill_name}': Status={status}, Level={final_level}, Confidence={confidence}")
    return result

def aggregate_candidate_evidence_matrix(
    claimed_skills: List[str],
    github_findings: Dict[str, Any],
    self_assessments: Dict[str, str],
    assessment_scores: Dict[str, int]
) -> List[Dict[str, Any]]:
    """
    Processes all candidate skills through the deterministic evidence engine.
    """
    matrix = []
    all_skills = set(claimed_skills) | set(self_assessments.keys())
    
    for skill in sorted(list(all_skills)):
        gh_item = github_findings.get(skill)
        self_lvl = self_assessments.get(skill, "Developing")
        score = assessment_scores.get(skill, 6)
        
        prof = calculate_evidence_proficiency(
            skill_name=skill,
            resume_claimed=(skill in claimed_skills),
            github_evidence=gh_item,
            self_level=self_lvl,
            assessment_score=score
        )
        matrix.append(prof)
        
    return matrix
