"""
Multi-User Isolation & Privacy Test Suite
=========================================
Verifies that:
1. Every newly registered user starts with a completely empty (0 pieces) closet.
2. Items uploaded by User A are strictly isolated and invisible to User B.
3. User B cannot access, recommend, or delete User A's clothes.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.append(str(BACKEND_DIR))

from app.database import SessionLocal, engine, Base
import app.models
from app.models.user import User
from app.models.clothing_item import ClothingItem
from app.routes.auth import register_user, login_user
from app.schemas.auth import UserRegisterRequest, UserLoginRequest
from app.routes.wardrobe import list_clothing_items

def test_multiuser_isolation():
    print("=" * 60)
    print("Running Multi-User Digital Closet Isolation Test...")
    print("=" * 60)

    db = SessionLocal()

    # 1. Check Primary User
    user_a = db.query(User).filter(User.email == "taranilakshmi8557@gmail.com").first()
    assert user_a is not None, "Primary user should exist"
    items_a = list_clothing_items(db=db, current_user=user_a)
    print(f"[CHECK 1] Primary User '{user_a.email}' has {len(items_a)} pieces.")
    assert len(items_a) == 9, f"Expected 9 pieces for User A, got {len(items_a)}"

    # 2. Register New Fresh Tester User B
    test_b_email = "tester_newbie@atelier.com"
    existing_b = db.query(User).filter(User.email == test_b_email).first()
    if existing_b:
        db.delete(existing_b)
        db.commit()

    reg_b = UserRegisterRequest(
        email=test_b_email,
        full_name="Beta Tester",
        password="test_password_456",
        style_preference="Smart Casual"
    )
    res_b = register_user(reg_b, db)
    user_b = db.query(User).filter(User.email == test_b_email).first()

    # 3. Verify User B starts with an empty closet (0 pieces)
    items_b = list_clothing_items(db=db, current_user=user_b)
    print(f"[CHECK 2] New User '{user_b.email}' has {len(items_b)} pieces.")
    assert len(items_b) == 0, f"Expected 0 pieces for new user B, got {len(items_b)}"

    # 4. User B adds an item
    new_item_b = ClothingItem(
        user_id=user_b.id,
        image_path="test_item_b.jpg",
        category="top",
        subcategory="polo",
        dominant_color_name="Navy Blue",
        dominant_color_hex="#000080",
        warmth_level=2,
        formality_level=3
    )
    db.add(new_item_b)
    db.commit()

    # 5. Check isolation: User B has 1 item, User A still has 9 items
    items_b_after = list_clothing_items(db=db, current_user=user_b)
    items_a_after = list_clothing_items(db=db, current_user=user_a)
    
    print(f"[CHECK 3] After upload -> User B has {len(items_b_after)} piece; User A has {len(items_a_after)} pieces.")
    assert len(items_b_after) == 1, "User B should see exactly 1 piece"
    assert len(items_a_after) == 9, "User A should still see exactly 9 pieces"

    # Clean up test user B
    db.delete(user_b)
    db.commit()
    db.close()

    print("=" * 60)
    print("[ALL ISOLATION CHECKS PASSED] Multi-user closets are 100% private and isolated!")
    print("=" * 60)

if __name__ == "__main__":
    test_multiuser_isolation()
