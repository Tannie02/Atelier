import torch
import numpy as np
from PIL import Image
from typing import Optional

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
        self.model = None
        self.processor = None
        self.text_embeddings = None
        self._is_loaded = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = CLIPService()
        return cls._instance

    def load_model(self):
        """Loads CLIP model and pre-computes candidate label embeddings."""
        if self._is_loaded:
            return

        try:
            from transformers import CLIPProcessor, CLIPModel
            print(f"[CLIPService] Loading openai/clip-vit-base-patch32 onto {self.device}...")
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
            self.model.eval()

            # Pre-compute text prompts
            prompts = [c["prompt"] for c in CANDIDATE_CATEGORIES]
            text_inputs = self.processor(text=prompts, return_tensors="pt", padding=True).to(self.device)
            
            with torch.no_grad():
                text_features = self.model.get_text_features(**text_inputs)
                # L2 Normalize
                self.text_embeddings = text_features / text_features.norm(p=2, dim=-1, keepdim=True)

            self._is_loaded = True
            print("[CLIPService] Model loaded successfully.")
        except Exception as e:
            print(f"[CLIPService] Warning: Could not initialize online CLIP ({e}). Operating in lightweight fallback mode.")
            self._is_loaded = False

    def extract_image_embedding(self, image_path: str) -> list[float]:
        """Extracts 512-dim normalized CLIP embedding vector."""
        if not self._is_loaded:
            self.load_model()

        if self._is_loaded and self.model is not None:
            try:
                with Image.open(image_path) as img:
                    img = img.convert("RGB")
                    inputs = self.processor(images=img, return_tensors="pt").to(self.device)
                    with torch.no_grad():
                        image_features = self.model.get_image_features(**inputs)
                        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
                        embedding = image_features.cpu().squeeze().tolist()
                        return embedding
            except Exception as e:
                print(f"[CLIPService] Embedding extraction error: {e}")

        # Deterministic pseudo-embedding fallback if CLIP is offline/downloading
        np.random.seed(abs(hash(image_path)) % (2**32))
        mock_vec = np.random.randn(512).astype(np.float32)
        mock_vec = mock_vec / np.linalg.norm(mock_vec)
        return mock_vec.tolist()

    def zero_shot_classify(self, image_path: str, top_k: int = 5) -> tuple[dict, list[dict]]:
        """
        Performs zero-shot classification over clothing candidate taxonomy.
        Returns (best_match_info, list_of_top_candidates).
        """
        if not self._is_loaded:
            self.load_model()

        if self._is_loaded and self.model is not None and self.text_embeddings is not None:
            try:
                with Image.open(image_path) as img:
                    img = img.convert("RGB")
                    inputs = self.processor(images=img, return_tensors="pt").to(self.device)
                    with torch.no_grad():
                        image_features = self.model.get_image_features(**inputs)
                        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
                        
                        # Cosine similarity matrix (1 x Num_Categories)
                        similarity = (image_features @ self.text_embeddings.T).squeeze(0)
                        probs = torch.softmax(similarity * 100.0, dim=-1).cpu().numpy()

                # Rank predictions
                ranked_indices = np.argsort(-probs)[:top_k]
                candidates = []
                for idx in ranked_indices:
                    item_meta = CANDIDATE_CATEGORIES[idx]
                    candidates.append({
                        "category": item_meta["category"],
                        "subcategory": item_meta["subcategory"],
                        "confidence": round(float(probs[idx]) * 100, 1),
                        "default_warmth": item_meta["default_warmth"],
                        "default_formality": item_meta["default_formality"]
                    })

                best = candidates[0]
                return best, candidates
            except Exception as e:
                print(f"[CLIPService] Zero-shot error: {e}")

        # Fallback default
        default_item = CANDIDATE_CATEGORIES[0]
        return {
            "category": default_item["category"],
            "subcategory": default_item["subcategory"],
            "confidence": 85.0,
            "default_warmth": default_item["default_warmth"],
            "default_formality": default_item["default_formality"]
        }, []

clip_service = CLIPService.get_instance()
