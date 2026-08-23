from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.clothing_item import ClothingItem
from app.models.outfit import OutfitRecommendation
from app.schemas.auth import (
    UserRegisterRequest, UserLoginRequest, 
    UserProfileResponse, TokenResponse
)
from app.auth_utils import (
    generate_salt, hash_password, verify_password, 
    create_access_token, decode_access_token
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def get_or_create_default_user(db: Session) -> User:
    """Ensures at least one primary user exists for seamless demo onboarding & migrations."""
    user = db.query(User).filter(User.email == "demo@atelier.com").first()
    if not user:
        # Check if any user exists
        first_user = db.query(User).first()
        if first_user:
            return first_user

        salt = generate_salt()
        hashed = hash_password("atelier2026", salt)
        user = User(
            email="demo@atelier.com",
            full_name="Taran",
            hashed_password=hashed,
            salt=salt,
            style_preference="Contemporary Minimalist"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Link any existing unassigned clothing items to this user
        unassigned = db.query(ClothingItem).filter(ClothingItem.user_id.is_(None)).all()
        for item in unassigned:
            item.user_id = user.id
        db.commit()

    return user

def get_current_user(
    authorization: Optional[str] = Header(None), 
    db: Session = Depends(get_db)
) -> User:
    """Strict authentication dependency requiring a valid JWT token for multi-user isolation."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in to access your digital closet."
        )

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please sign in again."
        )

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user session."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found. Please create an account or sign in."
        )

    return user

def get_strict_current_user(
    authorization: Optional[str] = Header(None), 
    db: Session = Depends(get_db)
) -> User:
    """Strict authentication dependency requiring a valid JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required. Please sign in."
        )

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please sign in again."
        )

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found."
        )

    return user

@router.post("/register", response_model=TokenResponse)
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """Registers a new user account and returns a JWT access token."""
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    salt = generate_salt()
    hashed = hash_password(req.password, salt)

    new_user = User(
        email=req.email.lower(),
        full_name=req.full_name.strip(),
        hashed_password=hashed,
        salt=salt,
        style_preference=req.style_preference or "Minimalist Chic"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate JWT
    token = create_access_token({"sub": str(new_user.id), "email": new_user.email})

    profile = UserProfileResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        style_preference=new_user.style_preference,
        total_closet_pieces=0,
        total_looks_curated=0,
        created_at=new_user.created_at
    )

    return TokenResponse(access_token=token, user=profile)

@router.post("/login", response_model=TokenResponse)
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticates user credentials and returns a JWT access token."""
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.salt, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token({"sub": str(user.id), "email": user.email})

    closet_count = db.query(ClothingItem).filter(ClothingItem.user_id == user.id).count()
    look_count = db.query(OutfitRecommendation).filter(OutfitRecommendation.user_id == user.id).count()

    profile = UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        style_preference=user.style_preference,
        total_closet_pieces=closet_count,
        total_looks_curated=look_count,
        created_at=user.created_at
    )

    return TokenResponse(access_token=token, user=profile)

@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns profile information for the authenticated user."""
    closet_count = db.query(ClothingItem).filter(ClothingItem.user_id == user.id).count()
    look_count = db.query(OutfitRecommendation).filter(OutfitRecommendation.user_id == user.id).count()

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        style_preference=user.style_preference,
        total_closet_pieces=closet_count,
        total_looks_curated=look_count,
        created_at=user.created_at
    )
