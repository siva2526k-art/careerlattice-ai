import hashlib
import os
import secrets
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from backend.app.database import create_user, get_user_by_email, get_user_by_id
from backend.app.config import log_event

ITERATIONS = 100_000

def hash_password(password: str) -> str:
    """Secure password hashing using PBKDF2-HMAC-SHA256 with a 16-byte salt."""
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
    return f"{salt.hex()}:{key.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verifies a plain password against the stored salt:hash string."""
    try:
        salt_hex, key_hex = hashed.split(":")
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
        return secrets.compare_digest(key, new_key)
    except Exception as e:
        log_event("AUTH", f"Password verification failed with error: {str(e)}")
        return False

# In-memory session token store (token -> {user_id, email, expires_at})
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

def create_session_token(user_id: str, email: str) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    ACTIVE_SESSIONS[token] = {
        "user_id": user_id,
        "email": email,
        "expires_at": expires_at
    }
    log_event("AUTH", f"Issued session token for {email}")
    return token

def validate_session_token(token: str) -> Optional[Dict[str, Any]]:
    session = ACTIVE_SESSIONS.get(token)
    if not session:
        return None
    if datetime.now(timezone.utc) > session["expires_at"]:
        del ACTIVE_SESSIONS[token]
        return None
    return get_user_by_id(session["user_id"])

def register_user(email: str, password: str, full_name: str) -> Dict[str, Any]:
    email = email.lower().strip()
    full_name = full_name.strip()
    
    # Validation
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValueError("Invalid email format.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    if len(full_name) < 2:
        raise ValueError("Full name must be at least 2 characters long.")
    
    if get_user_by_email(email):
        raise ValueError("User with this email already exists.")
        
    pw_hash = hash_password(password)
    user = create_user(email, pw_hash, full_name)
    token = create_session_token(user["id"], user["email"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "created_at": user["created_at"]
        }
    }

def login_user(email: str, password: str) -> Dict[str, Any]:
    email = email.lower().strip()
    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        log_event("AUTH", f"Invalid login attempt for {email}")
        raise ValueError("Invalid email or password.")
        
    token = create_session_token(user["id"], user["email"])
    log_event("AUTH", f"Successful login for {email}")
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "created_at": user["created_at"]
        }
    }
