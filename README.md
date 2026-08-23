# 💎 ATELIER — AI Personal Stylist & Smart Digital Closet

<div align="center">


### *YOUR STYLE. YOUR RULES. YOUR AI.*

**A consumer-grade luxury fashion styling platform powered by Computer Vision, Deep Learning, and Real-Time Weather Adaptation.**

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-atelier--4y0w.onrender.com-amber?style=for-the-badge)](https://atelier-4y0w.onrender.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![Hugging Face](https://img.shields.io/badge/Hugging_Face-CLIP_ViT-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/openai/clip-vit-base-patch32)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.0+-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)

</div>

---

## 🌟 Key Features & AI Architecture

### 1. 📷 Zero-Shot Garment Digitization & Color Harmony
* **CLIP Zero-Shot Classification**: Automatically recognizes garment cuts and silhouettes (formal shirts, hoodies, chinos, denim, loafers, sneakers) across 21 fine-grained fashion categories using OpenAI's `clip-vit-base-patch32`.
* **K-Means Dominant Color Clustering**: Extracts signature color palettes, hex codes, and maps them to true-tone fashion colors using CIELAB Delta-E distance.
* **512-Dimensional Visual Style DNA**: Computes normalized image embedding vectors per item for downstream compatibility modeling.

### 2. ✨ Intelligent Weather-Adaptive Daily Lookbooks
* **Live Weather Integration**: Connects with Open-Meteo to fetch live temperature, precipitation, and humidity for any city globally with 1-click GPS detection.
* **Multi-Constraint Rules Engine**: Dynamically filters and layers outfits based on destination dress codes (Campus, Executive Formal, Night Out, Date Night, Active, Lounge) and thermal warmth thresholds.
* **Curated 3-Piece Outfit Generator**: Evaluates all candidate combinations using visual cosine similarity, color harmony theory, and neural scoring.

### 3. 🧠 Personal Taste Learning & Neural Compatibility Net
* **Interactive Feedback Loop**: Users rate curated looks with **❤️ Love It** ($y=1$) or **✕ Pass** ($y=0$).
* **PyTorch Neural Scorer (`OutfitCompatibilityNet`)**: Learns pairwise garment interactions using Hadamard products ($\mathbf{e}_t \odot \mathbf{e}_b$) and absolute difference vectors ($|\mathbf{e}_t - \mathbf{e}_b|$).
* **Hot-Reloading Inference**: Backend automatically detects new model checkpoint weights on the fly without server restarts.

### 4. 🔒 Multi-User Privacy & Security
* **Encrypted Authentication**: Secure password hashing with PBKDF2-HMAC-SHA256 (100,000 iterations) + per-user cryptographic salts.
* **JWT Session Tokens**: 14-day signed JSON Web Tokens for stateless authorization.
* **Private Closets**: Strict multi-tenant isolation ensuring each user's closet, history, and taste profile remain 100% private.

---

=======
## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend & API** | FastAPI, Uvicorn, SQLAlchemy, Pydantic v2, PyJWT |
| **Machine Learning** | PyTorch, Hugging Face Transformers (`CLIP`), Scikit-Learn (K-Means), Pillow, NumPy |
| **Frontend UI** | HTML5, Tailwind CSS, Vanilla JavaScript, Lucide Icons, Plus Jakarta Sans & Playfair Display |
| **Data & APIs** | SQLite (WAL Mode), Open-Meteo Global Weather API |
| **DevOps & Cloud** | Docker, Docker Compose, Render |

---

## 🚀 Local Quickstart

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/atelier.git
cd atelier
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Server
```bash
python run_app.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 🧪 Verification & Testing

Run the automated test suites:
```bash
# Verify Auth & Passwords
python test_auth.py

# Verify Multi-User Digital Closet Isolation
python test_multiuser_isolation.py

# Verify Full Recommender & ML Pipeline
python test_verification.py
```

---

## 📄 License
This project is open-source under the MIT License.

