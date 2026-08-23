import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
import jwt

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "atelier-luxury-fashion-secret-key-2026-very-secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 14

def generate_salt() -> str:
    """Generates a random 32-character hexadecimal salt."""
    return secrets.token_hex(16)

def hash_password(password: str, salt: str) -> str:
    """
    Hashes a password with PBKDF2-HMAC-SHA256 (100,000 iterations).
    Produces secure password storage.
    """
    pwd_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100000)
    return key.hex()

def verify_password(plain_password: str, salt: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored salt and hash."""
    return hash_password(plain_password, salt) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JSON Web Token (JWT)."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT token. Returns payload dict or None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None
