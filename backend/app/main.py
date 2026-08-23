import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text

from app.database import engine, Base, SessionLocal
from app.config import UPLOAD_DIR, PROJECT_DIR
from app.routes.auth import router as auth_router, get_or_create_default_user
from app.routes.wardrobe import router as wardrobe_router
from app.routes.recommend import router as recommend_router
from app.routes.feedback import router as feedback_router
from app.routes.weather import router as weather_router
from app.ml.clip_service import clip_service

# Safe SQLite migration to add user_id column if missing
def run_migrations():
    with engine.connect() as conn:
        for table in ["clothing_items", "outfit_recommendations", "outfit_feedback"]:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER;"))
                conn.commit()
            except Exception:
                pass  # Column already exists

# Initialize tables
Base.metadata.create_all(bind=engine)
run_migrations()

# Ensure default user exists and existing items are linked
try:
    db = SessionLocal()
    get_or_create_default_user(db)
    db.close()
except Exception as e:
    print(f"[Main] Notice during user init: {e}")

app = FastAPI(
    title="ATELIER API",
    description="AI Personal Stylist & Smart Digital Closet Engine",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(wardrobe_router)
app.include_router(recommend_router)
app.include_router(feedback_router)
app.include_router(weather_router)

# Mount Uploads directory
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Mount Frontend static files
FRONTEND_DIR = PROJECT_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend_static")

@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "status": "online", 
        "app": "ATELIER API", 
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "auth": "enabled",
        "clip_loaded": clip_service._is_loaded
    }
