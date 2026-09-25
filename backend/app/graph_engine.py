import json
import networkx as nx
from typing import Dict, Any, List, Set, Optional
from pathlib import Path
from backend.app.config import log_event

DATA_DIR = Path(__file__).resolve().parent / "data"

def load_roles_and_skills():
    with open(DATA_DIR / "roles_and_skills.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_verified_resources():
    with open(DATA_DIR / "verified_resources.json", "r", encoding="utf-8") as f:
        return json.load(f).get("resources", {})

def build_prerequisite_graph() -> nx.DiGraph:
    """Constructs the canonical prerequisite DAG using NetworkX."""
    data = load_roles_and_skills()
    G = nx.DiGraph()
    
    # Add all skill nodes with tier & category metadata
    for skill_name, meta in data.get("skills", {}).items():
        G.add_node(skill_name, **meta)
        
    # Add directed prerequisite edges: A -> B means A is prerequisite of B
    for edge in data.get("prerequisites", []):
        G.add_edge(edge["from"], edge["to"])
        
    return G

def generate_personalized_roadmap(
    target_role: str,
    verified_skills: List[str], # Skills with status == 'VERIFIED'
    partial_skills: List[str]   # Skills with status == 'PARTIAL'
) -> Dict[str, Any]:
    """
    Generates a personalized, prerequisite-aware learning roadmap for the target role.
    
    Key Principles:
    1. If the student ALREADY demonstrates a skill, do NOT force them to repeat it!
    2. Start the roadmap from unmastered prerequisite ancestors.
    3. Order nodes using Kahn's Topological Sorting algorithm (zero cyclical deadlocks).
    4. Attach curated, accredited public learning resources (NPTEL, SWAYAM, Docs).
    """
    log_event("ROADMAP", f"Generating personalized roadmap for role: '{target_role}' (verified: {len(verified_skills)}, partial: {len(partial_skills)})")
    
    roles_data = load_roles_and_skills()
    resources_data = load_verified_resources()
    
    role_info = roles_data.get("roles", {}).get(target_role)
    if not role_info:
        # Fallback to Junior Backend Developer if role not found
        target_role = "Junior Backend Developer"
        role_info = roles_data["roles"]["Junior Backend Developer"]
        
    required_skills = set(role_info["required_skills"])
    recommended_skills = set(role_info.get("recommended_skills", []))
    all_target_skills = required_skills | recommended_skills
    
    G = build_prerequisite_graph()
    
    # 1. Expand target skill set with all required prerequisite ancestors
    needed_skills: Set[str] = set()
    for s in all_target_skills:
        needed_skills.add(s)
        if s in G:
            ancestors = nx.ancestors(G, s)
            needed_skills.update(ancestors)

    # 2. Extract induced subgraph for the role
    subgraph_nodes = [s for s in needed_skills if s in G]
    subgraph = G.subgraph(subgraph_nodes).copy()
    
    # 3. Apply Kahn's Topological Sort to get canonical linear sequence
    try:
        ordered_sequence = list(nx.topological_sort(subgraph))
    except nx.NetworkXUnfeasible:
        # If cycles occur, fall back to simple node list
        ordered_sequence = list(subgraph.nodes())

    # 4. Classify node states:
    # - 'demonstrated' (Green): verified in student's code/assessment
    # - 'active_gap' (Amber): missing prerequisite or partial skill ready to learn
    # - 'locked' (Grey): advanced goal whose prerequisites are not yet cleared
    
    cleared_set = set(verified_skills)
    partial_set = set(partial_skills)
    
    roadmap_nodes = []
    first_active_found = False
    
    for skill in ordered_sequence:
        meta = G.nodes[skill]
        res_list = resources_data.get(skill, [
            {"title": f"{skill} Official Guide & Documentation", "provider": "Official Documentation", "url": "https://devdocs.io", "difficulty": "Intermediate", "type": "Documentation"}
        ])
        
        prereqs = list(G.predecessors(skill))
        prereqs_cleared = all((p in cleared_set) for p in prereqs)
        
        if skill in cleared_set:
            status = "demonstrated"
            badge = "🟢 Demonstrated / Mastered"
            action_text = "Mastered: Skill proven in repository implementation."
        elif prereqs_cleared:
            status = "active_gap"
            badge = "🟡 Active Prerequisite (Learn Next)" if not (skill in partial_set) else "🟡 In Progress (Partial Evidence)"
            action_text = f"Build and commit a practical project to achieve full verification."
            first_active_found = True
        else:
            status = "locked"
            badge = "⚪ Locked Goal"
            action_text = f"Complete prerequisites first: {', '.join([p for p in prereqs if p not in cleared_set])}."
            
        roadmap_nodes.append({
            "id": skill.lower().replace(" ", "_").replace("+", "p").replace("/", "_"),
            "skill_name": skill,
            "category": meta.get("category", "General"),
            "tier": meta.get("tier", "Core"),
            "status": status,
            "badge": badge,
            "prerequisites": prereqs,
            "action_text": action_text,
            "resources": res_list,
            "capstone_task": {
                "title": f"Production Implementation: {skill}",
                "build": f"Implement a containerized module or test suite showcasing {skill}.",
                "prove": "Commit and push your implementation to your GitHub repository.",
                "rescan": "Click 'Update My Evidence' to rescan and auto-clear this node."
            }
        })
        
    return {
        "target_role": target_role,
        "role_description": role_info["description"],
        "target_level": role_info["target_level"],
        "total_nodes": len(roadmap_nodes),
        "cleared_count": len([n for n in roadmap_nodes if n["status"] == "demonstrated"]),
        "active_count": len([n for n in roadmap_nodes if n["status"] == "active_gap"]),
        "locked_count": len([n for n in roadmap_nodes if n["status"] == "locked"]),
        "nodes": roadmap_nodes
    }
