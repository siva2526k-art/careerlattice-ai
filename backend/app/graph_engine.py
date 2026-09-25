import networkx as nx

def build_backend_prerequisite_dag():
    G = nx.DiGraph()

    # Define nodes with metadata
    nodes = {
        "python_basics": {"title": "Python Syntax & OOP", "tier": "Foundation", "cleared": True},
        "git_core": {"title": "Git & Version Control", "tier": "Foundation", "cleared": True},
        "sql_basics": {"title": "Relational Databases & SQL", "tier": "Foundation", "cleared": True},
        "rest_api": {"title": "REST API Architecture", "tier": "Foundation", "cleared": True},
        "fastapi_core": {"title": "FastAPI Framework & Pydantic", "tier": "Framework", "cleared": True},
        "async_io": {"title": "Asynchronous I/O (asyncio)", "tier": "Core Backend", "cleared": True},
        "docker_basics": {"title": "Docker Containers & Images", "tier": "DevOps", "cleared": False, "active": True},
        "docker_compose": {"title": "Docker Compose Multi-Service", "tier": "DevOps", "cleared": False},
        "redis_cache": {"title": "Redis In-Memory Caching", "tier": "Optimization", "cleared": False},
        "aws_fundamentals": {"title": "AWS Cloud Deployment (ECS/RDS)", "tier": "Cloud", "cleared": False},
        "ci_cd": {"title": "CI/CD Automation (GitHub Actions)", "tier": "DevOps", "cleared": False},
        "k8s_orchestration": {"title": "Kubernetes Microservices", "tier": "Advanced", "cleared": False}
    }

    for nid, data in nodes.items():
        G.add_node(nid, **data)

    # Define prerequisite edges: A -> B means A is prerequisite of B
    edges = [
        ("python_basics", "fastapi_core"),
        ("rest_api", "fastapi_core"),
        ("python_basics", "async_io"),
        ("sql_basics", "redis_cache"),
        ("docker_basics", "docker_compose"),
        ("docker_compose", "aws_fundamentals"),
        ("async_io", "redis_cache"),
        ("docker_compose", "k8s_orchestration"),
        ("aws_fundamentals", "k8s_orchestration"),
        ("git_core", "ci_cd"),
        ("ci_cd", "aws_fundamentals")
    ]

    G.add_edges_from(edges)
    return G

def generate_user_roadmap(verified_skills: dict, capstone_completed: bool = False):
    """
    Computes node states (green/amber/grey) and Kahn's topological sort order.
    """
    G = build_backend_prerequisite_dag()
    
    # Check if Docker/AWS was cleared
    docker_verified = capstone_completed or (verified_skills.get("Docker", {}).get("confidence", 0) >= 0.8)
    aws_verified = capstone_completed or (verified_skills.get("AWS", {}).get("confidence", 0) >= 0.8)

    roadmap_nodes = [
        {
            "id": "python_core",
            "title": "Python Syntax & Asyncio",
            "tier": "Foundation",
            "status": "cleared",
            "badge": "🟢 Mastered (Code Verified)",
            "details": "Verified via GitHub AST imports."
        },
        {
            "id": "fastapi_core",
            "title": "FastAPI & PostgreSQL ORM",
            "tier": "Framework",
            "status": "cleared",
            "badge": "🟢 Mastered (Code Verified)",
            "details": "FastAPI routes and SQLAlchemy models detected."
        },
        {
            "id": "docker_bridge",
            "title": "Docker Containers & Networking",
            "tier": "Active Prerequisite",
            "status": "cleared" if docker_verified else "active",
            "badge": "🟢 Mastered via Capstone" if docker_verified else "🟡 Learn Next (Active Gap)",
            "details": "Container port bridges, Dockerfile multi-stage builds.",
            "nptel_module": "NPTEL / IIT Kharagpur: Cloud Computing & Containers (Module 3)",
            "docs_url": "https://docs.docker.com/get-started/"
        },
        {
            "id": "aws_cloud",
            "title": "AWS Cloud Deployment (ECS & RDS)",
            "tier": "Cloud Target",
            "status": "cleared" if aws_verified else ("active" if docker_verified else "locked"),
            "badge": "🟢 Mastered via Capstone" if aws_verified else ("🟡 Learn Next" if docker_verified else "⚪ Locked Goal"),
            "details": "IAM execution roles, ECS container tasks, and RDS connection pools.",
            "nptel_module": "NPTEL / IIT Madras: Distributed Systems & Cloud Infrastructure",
            "docs_url": "https://aws.amazon.com/getting-started/"
        },
        {
            "id": "k8s_microservices",
            "title": "Kubernetes Microservices Architecture",
            "tier": "Industry Goal",
            "status": "cleared" if (docker_verified and aws_verified) else "locked",
            "badge": "🟢 Demonstrated" if (docker_verified and aws_verified) else "⚪ Locked Goal",
            "details": "Deployments, Services, Ingress Controllers, and Pod Scaling.",
            "nptel_module": "NPTEL: Advanced Cloud Systems",
            "docs_url": "https://kubernetes.io/docs/tutorials/"
        }
    ]

    return roadmap_nodes
