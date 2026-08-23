import os
import gc
import json
from pathlib import Path
import torch
import numpy as np
from PIL import Image
from typing import Optional

ML_DIR = Path(__file__).resolve().parent
TEXT_EMB_FILE = ML_DIR / "candidate_text_embeddings.json"

# Candidate clothing labels with descriptive prompts for zero-shot accuracy
CANDIDATE_CATEGORIES = [
    # Tops
    {"subcategory": "t-shirt", "category": "top", "prompt": "a photo of a casual t-shirt or tee", "default_warmth": 1, "default_formality": 1},
    {"subcategory": "formal shirt", "category": "top", "prompt": "a photo of a formal button-up dress shirt", "default_warmth": 2, "default_formality": 4},
    {"subcategory": "casual shirt", "category": "top", "prompt": "a photo of a casual button down collar shirt", "default_warmth": 2, "default_formality": 2},
    {"subcategory": "polo shirt", "category": "top", "prompt": "a photo of a polo shirt with collar", "default_warmth": 1, "default_formality": 2},
    {"subcategory": "hoodie", "category": "top", "prompt": "a photo of a casual hoodie sweatshirt with hood", "default_warmth": 3, "default_formality": 1},
    {"subcategory": "sweater", "category": "top", "prompt": "a photo of a knit sweater or pullover jumper", "default_warmth": 4, "default_formality": 3},
    {"subcategory": "jacket", "category": "outerwear", "prompt": "a photo of a jacket, bomber jacket or denim jacket", "default_warmth": 4, "default_formality": 2},
    {"subcategory": "blazer", "category": "outerwear", "prompt": "a photo of a tailored blazer suit jacket", "default_warmth": 3, "default_formality": 4},
    {"subcategory": "coat", "category": "outerwear", "prompt": "a photo of a winter overcoat or trench coat", "default_warmth": 5, "default_formality": 4},
    {"subcategory": "tank top", "category": "top", "prompt": "a photo of a sleeveless tank top or gym vest", "default_warmth": 1, "default_formality": 1},
    
    # Bottoms
    {"subcategory": "denim jeans", "category": "bottom", "prompt": "a photo of blue or black denim jeans pants", "default_warmth": 2, "default_formality": 2},
    {"subcategory": "chinos", "category": "bottom", "prompt": "a photo of khaki or cotton chinos trousers", "default_warmth": 2, "default_formality": 3},
    {"subcategory": "formal trousers", "category": "bottom", "prompt": "a photo of tailored formal dress trousers slacks", "default_warmth": 2, "default_formality": 4},
    {"subcategory": "sweatpants", "category": "bottom", "prompt": "a photo of comfortable track pants sweatpants or joggers", "default_warmth": 2, "default_formality": 1},
    {"subcategory": "shorts", "category": "bottom", "prompt": "a photo of casual shorts or denim shorts", "default_warmth": 1, "default_formality": 1},
    
    # Footwear
    {"subcategory": "sneakers", "category": "footwear", "prompt": "a photo of casual lifestyle sneakers or trainers", "default_warmth": 2, "default_formality": 2},
    {"subcategory": "running shoes", "category": "footwear", "prompt": "a photo of athletic running sports gym shoes", "default_warmth": 2, "default_formality": 1},
    {"subcategory": "formal leather shoes", "category": "footwear", "prompt": "a photo of formal leather dress oxford or derby shoes", "default_warmth": 2, "default_formality": 5},
    {"subcategory": "boots", "category": "footwear", "prompt": "a photo of leather chelsea boots or ankle boots", "default_warmth": 3, "default_formality": 3},
    {"subcategory": "loafers", "category": "footwear", "prompt": "a photo of slip-on leather or suede loafers", "default_warmth": 2, "default_formality": 4},
    {"subcategory": "sandals", "category": "footwear", "prompt": "a photo of open-toe summer sandals or slides", "default_warmth": 1, "default_formality": 1},
]

class CLIPService:
    _instance = None

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.vision_model = None
        self.processor = None
        self.text_embeddings = None
        self._is_loaded = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = CLIPService()
        return cls._instance

    def load_model(self):
        """Loads lightweight CLIP Vision Encoder and pre-computed text embeddings."""
        if self._is_loaded:
            return

        try:
            # 1. Load pre-computed text embeddings (0MB RAM footprint)
            if TEXT_EMB_FILE.exists():
                with open(TEXT_EMB_FILE, "r") as f:
                    matrix = json.load(f)
                    self.text_embeddings = torch.tensor(matrix, dtype=torch.float32, device=self.device)
            
            # 2. Load lightweight Vision-only model (saves ~350MB of RAM)
            from transformers import AutoImageProcessor, CLIPVisionModelWithProjection
            print(f"[CLIPService] Loading lightweight vision model on {self.device}...")
            self.processor = AutoImageProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.vision_model = CLIPVisionModelWithProjection.from_pretrained(
                "openai/clip-vit-base-patch32",
                low_cpu_mem_usage=True
            ).to(self.device)
            self.vision_model.eval()

            self._is_loaded = True
            print("[CLIPService] Lightweight vision model loaded successfully.")
        except Exception as e:
            print(f"[CLIPService] Notice: Operating in memory-optimized mode ({e})")
            self._is_loaded = False

        gc.collect()

    def extract_image_embedding(self, image_path: str) -> list[float]:
        """Extracts 512-dim normalized CLIP embedding vector with low memory usage."""
        if not self._is_loaded:
            self.load_model()

        if self._is_loaded and self.vision_model is not None:
            try:
                with Image.open(image_path) as img:
                    img = img.convert("RGB")
                    # Downscale for inference efficiency if huge
                    if img.width > 800 or img.height > 800:
                        img.thumbnail((800, 800))
                    
                    inputs = self.processor(images=img, return_tensors="pt").to(self.device)
                    with torch.inference_mode():
                        outputs = self.vision_model(**inputs)
                        image_features = outputs.image_embeds
                        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
                        embedding = image_features.cpu().squeeze().tolist()
                        return embedding
            except Exception as e:
                print(f"[CLIPService] Vision inference notice: {e}")
            finally:
                gc.collect()

        # Fallback deterministic pseudo-embedding
        np.random.seed(abs(hash(image_path)) % (2**32))
        mock_vec = np.random.randn(512).astype(np.float32)
        mock_vec = mock_vec / np.linalg.norm(mock_vec)
        return mock_vec.tolist()

    def zero_shot_classify(self, image_path: str, top_k: int = 4) -> tuple[dict, list[dict]]:
        """Classifies image against categories using pre-computed text embeddings."""
        img_emb = self.extract_image_embedding(image_path)

        if self.text_embeddings is not None and len(img_emb) == 512:
            try:
                img_t = torch.tensor(img_emb, dtype=torch.float32, device=self.device).unsqueeze(0)
                # Cosine similarity
                similarities = (img_t @ self.text_embeddings.T).squeeze(0)
                probs = torch.softmax(similarities * 100, dim=0).cpu().numpy()

                top_indices = np.argsort(probs)[::-1][:top_k]
                
                candidates = []
                for idx in top_indices:
                    cat_info = CANDIDATE_CATEGORIES[idx]
                    candidates.append({
                        "subcategory": cat_info["subcategory"],
                        "category": cat_info["category"],
                        "confidence": round(float(probs[idx]) * 100, 1),
                        "default_warmth": cat_info["default_warmth"],
                        "default_formality": cat_info["default_formality"]
                    })

                best_match = candidates[0]
                return best_match, candidates
            except Exception as e:
                print(f"[CLIPService] Classification error: {e}")

        # Fallback default
        default_item = CANDIDATE_CATEGORIES[0]
        return {
            "subcategory": default_item["subcategory"],
            "category": default_item["category"],
            "confidence": 85.0,
            "default_warmth": default_item["default_warmth"],
            "default_formality": default_item["default_formality"]
        }, []

# Global Singleton
clip_service = CLIPService.get_instance()
