"""
Outfit Picker — Main Application Launcher
=========================================
Starts the FastAPI backend web server and mounts the frontend interface.

Usage:
------
python run_app.py
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add backend to python path
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.append(str(BACKEND_DIR))

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    reload_mode = os.environ.get("ENV", "production").lower() != "production"

    print("=" * 60)
    print("✨ Starting ATELIER AI Personal Stylist Platform...")
    print(f"📍 Server Listening at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    print(f"📖 API Documentation: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
    print("=" * 60)
    
    uvicorn.run("app.main:app", host=host, port=port, reload=reload_mode, app_dir=str(BACKEND_DIR))
