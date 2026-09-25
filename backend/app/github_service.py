import httpx
import re
from typing import Dict, Any, List, Optional
from backend.app.config import GITHUB_TOKEN, log_event

GITHUB_API_BASE = "https://api.github.com"

async def fetch_user_repositories(username_or_token: str, is_token: bool = False) -> List[Dict[str, Any]]:
    """
    Fetches accessible repositories for a given GitHub username or OAuth/personal token.
    Filters out forks by default to focus on original student work.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CareerLattice-AI-AST-Inspector"
    }
    
    token = username_or_token if is_token else GITHUB_TOKEN
    if token:
        headers["Authorization"] = f"Bearer {token}"

    log_event("GITHUB", f"Fetching repositories for '{username_or_token}' (token_provided: {bool(token)})")

    async with httpx.AsyncClient(timeout=10.0) as client:
        if is_token:
            url = f"{GITHUB_API_BASE}/user/repos?sort=updated&per_page=30"
        else:
            url = f"{GITHUB_API_BASE}/users/{username_or_token}/repos?sort=updated&per_page=30"
            
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                repos_raw = resp.json()
                cleaned_repos = []
                for r in repos_raw:
                    cleaned_repos.append({
                        "name": r.get("name"),
                        "full_name": r.get("full_name"),
                        "description": r.get("description") or "No description provided",
                        "language": r.get("language") or "Other",
                        "stars": r.get("stargazers_count", 0),
                        "fork": r.get("fork", False),
                        "default_branch": r.get("default_branch", "main"),
                        "html_url": r.get("html_url")
                    })
                log_event("GITHUB", f"Successfully retrieved {len(cleaned_repos)} repositories")
                return cleaned_repos
            elif resp.status_code == 404:
                log_event("GITHUB", f"User or token '{username_or_token}' not found on GitHub")
                return []
            else:
                log_event("GITHUB", f"GitHub API responded with status {resp.status_code}: {resp.text[:100]}")
                return []
        except Exception as e:
            log_event("GITHUB", f"Network error contacting GitHub API: {str(e)}")
            return []

def get_demo_repositories() -> List[Dict[str, Any]]:
    """Returns sample repository list for demo mode (e.g. Rohan Sharma)."""
    return [
        {
            "name": "fastapi-microservice-backend",
            "full_name": "rohan-sharma-dev/fastapi-microservice-backend",
            "description": "Asynchronous REST API with PostgreSQL ORM, Pydantic validation & Docker container.",
            "language": "Python",
            "stars": 4,
            "fork": False,
            "default_branch": "main",
            "selected_by_default": True
        },
        {
            "name": "ecommerce-portfolio-api",
            "full_name": "rohan-sharma-dev/ecommerce-portfolio-api",
            "description": "Flask REST API with SQLite database models and JWT token authentication.",
            "language": "Python",
            "stars": 2,
            "fork": False,
            "default_branch": "main",
            "selected_by_default": True
        },
        {
            "name": "react-frontend-dashboard",
            "full_name": "rohan-sharma-dev/react-frontend-dashboard",
            "description": "Responsive dashboard SPA built with React and Tailwind CSS.",
            "language": "JavaScript",
            "stars": 1,
            "fork": False,
            "default_branch": "main",
            "selected_by_default": False
        },
        {
            "name": "college-os-lab-assignments",
            "full_name": "rohan-sharma-dev/college-os-lab-assignments",
            "description": "Operating system CPU scheduling and semaphore practice exercises in C.",
            "language": "C",
            "stars": 0,
            "fork": False,
            "default_branch": "main",
            "selected_by_default": False
        }
    ]
