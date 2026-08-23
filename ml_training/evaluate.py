"""
Outfit Scorer Model Evaluator 🧪
================================
Run test evaluations on your trained PyTorch checkpoint.

Usage:
------
python evaluate.py
"""

import sys
from pathlib import Path

# Add project paths
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent
BACKEND_DIR = PROJECT_DIR / "backend"
sys.path.append(str(BACKEND_DIR))
sys.path.append(str(CURRENT_DIR))

import torch
import numpy as np
from app.database import SessionLocal
from app.models.clothing_item import ClothingItem
from model import OutfitCompatibilityNet

def evaluate_model():
    checkpoint_path = CURRENT_DIR / "checkpoints" / "best_scorer.pt"
    if not checkpoint_path.exists():
        print(f"❌ Checkpoint not found at {checkpoint_path}!")
        print("Please train your model first using: python ml_training/train.py")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Loading checkpoint from {checkpoint_path}...")
    model = OutfitCompatibilityNet(emb_dim=512, hidden_dim=256).to(device)
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()

    db = SessionLocal()
    items = db.query(ClothingItem).all()
    
    tops = [i for i in items if i.category == "top" and i.clip_embedding]
    bottoms = [i for i in items if i.category == "bottom" and i.clip_embedding]
    shoes = [i for i in items if i.category == "footwear" and i.clip_embedding]

    print("\n" + "=" * 70)
    print("[EVALUATION] EVALUATING TRAINED OUTFIT SCORER ON WARDROBE SAMPLES")
    print("=" * 70)

    if not tops or not bottoms or not shoes:
        print("Notice: Not enough wardrobe items in DB. Evaluating on sample feature vectors...")
        # Evaluate on sample vectors
        t = torch.randn(1, 512).to(device)
        t = t / t.norm(dim=-1, keepdim=True)
        b = t + torch.randn(1, 512).to(device) * 0.1
        b = b / b.norm(dim=-1, keepdim=True)
        s = t + torch.randn(1, 512).to(device) * 0.1
        s = s / s.norm(dim=-1, keepdim=True)

        with torch.no_grad():
            score = model(t, b, s).item() * 100.0
        print(f"Sample Matched Combo Score: {score:.1f}%")
        return

    print(f"Evaluating across {len(tops)} Tops x {len(bottoms)} Bottoms x {len(shoes)} Shoes:")
    
    count = 0
    for t in tops[:3]:
        for b in bottoms[:3]:
            for s in shoes[:2]:
                t_t = torch.tensor(t.clip_embedding).unsqueeze(0).to(device)
                b_t = torch.tensor(b.clip_embedding).unsqueeze(0).to(device)
                s_t = torch.tensor(s.clip_embedding).unsqueeze(0).to(device)

                with torch.no_grad():
                    score = model(t_t, b_t, s_t).item() * 100.0

                print(
                    f"  - [{score:5.1f}% Match] Top: {t.dominant_color_name} {t.subcategory} + "
                    f"Bottom: {b.dominant_color_name} {b.subcategory} + "
                    f"Shoes: {s.dominant_color_name} {s.subcategory}"
                )
                count += 1
                if count >= 8:
                    break

    db.close()
    print("=" * 70)

if __name__ == "__main__":
    evaluate_model()
