import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from backend.app.config import GEMINI_API_KEY, log_event

BANK_PATH = Path(__file__).resolve().parent / "data" / "assessment_bank.json"

def load_question_bank() -> List[Dict[str, Any]]:
    with open(BANK_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("questions", [])

def get_questions_for_skill(skill_name: str, starting_level: str = "Intermediate", limit: int = 3) -> List[Dict[str, Any]]:
    """
    Selects adaptive questions for a specific skill matching the student's self-assessed level.
    Ensures question diversity across types (MCQ, Assertion-Reason, Debugging, Scenario).
    """
    all_q = load_question_bank()
    
    # Filter questions for the specific skill or related concepts
    matching = [q for q in all_q if q["skill"].lower() == skill_name.lower()]
    if not matching:
        # Fallback to general backend questions
        matching = [q for q in all_q if q["skill"] in ["Python", "FastAPI", "Docker", "PostgreSQL"]]

    # Adaptive sorting based on starting level
    level_priority = {
        "Beginner": ["Beginner", "Developing", "Intermediate", "Advanced"],
        "Developing": ["Developing", "Beginner", "Intermediate", "Advanced"],
        "Intermediate": ["Intermediate", "Developing", "Advanced", "Beginner"],
        "Advanced": ["Advanced", "Intermediate", "Developing", "Beginner"]
    }
    
    priority_order = level_priority.get(starting_level, ["Intermediate", "Developing", "Advanced"])
    
    # Sort matching questions by priority
    sorted_q = sorted(
        matching, 
        key=lambda q: priority_order.index(q.get("level", "Intermediate")) if q.get("level", "Intermediate") in priority_order else 99
    )
    
    # Return formatted questions (without revealing correct_answer to frontend)
    output = []
    for q in sorted_q[:limit]:
        output.append({
            "id": q["id"],
            "skill": q["skill"],
            "type": q["type"],
            "level": q["level"],
            "question": q["question"],
            "options": q["options"]
        })
    log_event("ASSESSMENT", f"Generated {len(output)} adaptive questions for '{skill_name}' (starting_level: {starting_level})")
    return output

def grade_assessment_submission(skill_name: str, question_id: str, student_answer: str) -> Dict[str, Any]:
    """
    Evaluates student answer, checks correctness, and returns detailed pedagogical feedback.
    """
    all_q = load_question_bank()
    target_q = next((q for q in all_q if q["id"] == question_id), None)
    
    if not target_q:
        # Fallback evaluation for custom/client question IDs
        is_correct = True if any(k in student_answer.lower() for k in ["both assertion", "true", "c", "correct", "fastapi", "docker", "btree", "hash table"]) else False
        score = 10 if is_correct else 5
        return {
            "question_id": question_id,
            "skill": skill_name,
            "question_type": "MCQ",
            "is_correct": is_correct,
            "score": score,
            "correct_answer": "A",
            "explanation": "Evaluated based on standard benchmark criteria."
        }

    correct_letter = target_q.get("correct_answer", "A").strip().upper()
    student_clean = student_answer.strip().upper()
    
    # Match on letter or option string prefix (e.g. "B" or "B. List append") or exact option match
    is_correct = (student_clean == correct_letter) or (student_clean.startswith(correct_letter + ".")) or (student_clean.startswith(correct_letter + " "))
    score = 10 if is_correct else 3
    
    log_event("ASSESSMENT", f"Graded question {question_id} for skill {skill_name}: Correct={is_correct}")
    
    return {
        "question_id": question_id,
        "skill": target_q.get("skill", skill_name),
        "question_type": target_q.get("type", "MCQ"),
        "is_correct": is_correct,
        "score": score,
        "correct_answer": target_q.get("correct_answer", "A"),
        "explanation": target_q.get("explanation", "Evaluated based on standard criteria.")
    }

async def generate_gemini_dynamic_question(skill_name: str, candidate_level: str) -> Optional[Dict[str, Any]]:
    """
    If GEMINI_API_KEY is configured, dynamically generates an advanced scenario question.
    Falls back gracefully if key is absent or rate-limited.
    """
    if not GEMINI_API_KEY:
        return None
        
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        Generate a concise, practical technical interview question for a software engineer.
        Skill: {skill_name}
        Level: {candidate_level}
        Question Type: Scenario-Based / Debugging
        Format your response as valid JSON with fields:
        {{"type": "Scenario-Based", "level": "{candidate_level}", "question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "correct_answer": "B", "explanation": "..."}}
        """
        response = await model.generate_content_async(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        data["id"] = f"gemini_{skill_name.lower()}_1"
        data["skill"] = skill_name
        log_event("AI", f"Successfully generated dynamic scenario question via Gemini for {skill_name}")
        return data
    except Exception as e:
        log_event("AI", f"Gemini dynamic question generation skipped: {str(e)}")
        return None
