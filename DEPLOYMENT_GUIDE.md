# ATELIER — Production Deployment Guide 🚀

This guide explains how to deploy **ATELIER** to production for live customers and beta testers.

---

## 📋 Readiness Checklist (All Passed)

- [x] **Full-Stack Self-Contained**: FastAPI serves both the high-performance ML API and static frontend assets without CORS bottlenecks.
- [x] **Zero Cloud API Key Dependencies**: Weather queries use Open-Meteo (open-source, 10,000+ free calls/day, no rate-limiting keys).
- [x] **Multi-User Privacy Isolation**: Every user gets a private digital closet; new users start with 0 pieces.
- [x] **Encrypted Authentication**: Passwords hashed with PBKDF2-HMAC-SHA256 (100,000 rounds) + JWT token sessions.
- [x] **Containerized**: `Dockerfile` and `docker-compose.yml` pre-configured.

---

## Option 1: Deploy on Render (Recommended & Easiest Free/Low-Cost Cloud)

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Launch ATELIER platform"
   git remote add origin https://github.com/yourusername/atelier.git
   git push -u origin main
   ```
2. Go to **[render.com](https://render.com)** $\rightarrow$ Click **New +** $\rightarrow$ **Web Service**.
3. Connect your GitHub repository.
4. Set the following settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run_app.py`
5. Click **Create Web Service**. Render will build the environment and give you a live URL (e.g. `https://atelier-studio.onrender.com`)!

---

## Option 2: Deploy on Railway (Ultra Fast with Docker)

1. Install Railway CLI or connect via **[railway.app](https://railway.app)**.
2. Click **New Project** $\rightarrow$ **Deploy from GitHub Repo**.
3. Railway automatically detects the `Dockerfile` and starts the app.
4. Add a Persistent Volume mounted at `/app/backend/uploads` so user uploaded clothes persist permanently across redeploys.

---

## Option 3: Deploy on a VPS (DigitalOcean / Linode / AWS EC2) with Docker

1. Clone repo to server:
   ```bash
   git clone https://github.com/yourusername/atelier.git /opt/atelier
   cd /opt/atelier
   ```
2. Run with Docker Compose:
   ```bash
   docker compose up -d --build
   ```
3. Your app is now live at `http://your-server-ip:8000`.

---

## 🔒 Recommended Production Environment Variables

| Variable | Default Value | Recommended Production Setting |
| :--- | :--- | :--- |
| `JWT_SECRET_KEY` | `atelier-luxury-fashion-secret-key-2026-very-secure` | Generate random 64-char key (`openssl rand -hex 32`) |
| `PORT` | `8000` | Injected automatically by cloud host |
| `HOST` | `0.0.0.0` | `0.0.0.0` |
| `ENV` | `production` | `production` |
