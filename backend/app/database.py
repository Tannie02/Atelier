from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Needed for SQLite in multi-threaded FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def run_db_migrations():
    """Ensures newly added columns (user_id) exist in SQLite tables without data loss."""
    with engine.connect() as conn:
        for table in ["clothing_items", "outfit_recommendations", "outfit_feedback"]:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER;"))
                conn.commit()
            except Exception:
                pass  # Column already exists

def get_db():
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Run schema migrations
run_db_migrations()
