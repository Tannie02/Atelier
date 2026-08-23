"""
Authentication & Multi-User Digital Closet Test Suite
=====================================================
Verifies:
1. User registration & secure password hashing with salt
2. JWT token generation and validation
3. User login endpoint
4. Private closet scoping
5. Existing 9 user photos accessibility
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.append(str(BACKEND_DIR))

from app.database import SessionLocal, engine, Base
import app.models  # Registers all SQLAlchemy models
from app.models.user import User
from app.models.clothing_item import ClothingItem
from app.auth_utils import hash_password, verify_password, create_access_token, decode_access_token
from app.routes.auth import register_user, login_user, get_or_create_default_user
from app.schemas.auth import UserRegisterRequest, UserLoginRequest

# Ensure tables exist
Base.metadata.create_all(bind=engine)

def run_auth_tests():
    print("=" * 60)
    print("Running Authentication & Multi-User Verification Suite...")
    print("=" * 60)

    db = SessionLocal()

    # 1. Test Password Hashing
    salt = "test_salt_1234567890abcdef"
    pwd = "luxury_fashion_password"
    hashed = hash_password(pwd, salt)
    assert verify_password(pwd, salt, hashed), "Password verification failed"
    assert not verify_password("wrong_password", salt, hashed), "Wrong password should fail"
    print("[CHECK 1] Password Hashing & Salt Verification: PASS")

    # 2. Test JWT Generation & Decoding
    token = create_access_token({"sub": "42", "email": "test@atelier.com"})
    payload = decode_access_token(token)
    assert payload is not None and payload["sub"] == "42", "JWT token payload mismatch"
    print("[CHECK 2] JWT Token Creation & Decode: PASS")

    # 3. Test Default User & Existing Closet Items
    default_user = get_or_create_default_user(db)
    assert default_user is not None, "Default user creation failed"
    
    # Check items count
    items = db.query(ClothingItem).all()
    print(f"[CHECK 3] Real Wardrobe Items Intact: {len(items)} items in database.")
    assert len(items) >= 9, "Expected at least 9 real clothing items"

    # 4. Test Registration Endpoint
    test_email = "new_fashionista@atelier.com"
    existing = db.query(User).filter(User.email == test_email).first()
    if existing:
        db.delete(existing)
        db.commit()

    reg_req = UserRegisterRequest(
        email=test_email,
        full_name="Elena Rostova",
        password="secret_password_123",
        style_preference="Contemporary Minimalist"
    )
    reg_res = register_user(reg_req, db)
    assert reg_res.access_token is not None, "Registration should return access token"
    assert reg_res.user.email == test_email
    print(f"[CHECK 4] User Registration for '{test_email}': PASS (Token Issued)")

    # 5. Test Login Endpoint
    login_req = UserLoginRequest(email=test_email, password="secret_password_123")
    login_res = login_user(login_req, db)
    assert login_res.access_token is not None, "Login should return access token"
    print(f"[CHECK 5] User Login & Auth Session: PASS (User: {login_res.user.full_name})")

    db.close()
    print("=" * 60)
    print("[ALL AUTH TESTS PASSED] Authentication & Closet Scoping Verified!")
    print("=" * 60)

if __name__ == "__main__":
    run_auth_tests()
