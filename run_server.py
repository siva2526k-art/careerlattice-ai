import sys
import os
from pathlib import Path

# Add project root to sys.path so 'backend' module is always discovered
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Starting CareerLattice AI Server from: {ROOT_DIR}")
    print("🌐 Web Application: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
