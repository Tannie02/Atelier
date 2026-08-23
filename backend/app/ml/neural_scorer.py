import os
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from app.config import BEST_MODEL_PATH
from app.models.clothing_item import ClothingItem

class OutfitCompatibilityNet(nn.Module):
    """
    Deep Neural Outfit Compatibility Scorer.
    Takes 3 item embeddings (Top, Bottom, Footwear - 512-d each)
    Computes element-wise interactions, differences, and outputs compatibility probability [0, 1].
    """
    def __init__(self, emb_dim: int = 512, hidden_dim: int = 256, dropout_rate: float = 0.3):
        super().__init__()
        self.in_features = emb_dim * 9
        
        self.fc1 = nn.Linear(self.in_features, hidden_dim * 2)
        self.bn1 = nn.BatchNorm1d(hidden_dim * 2)
        self.relu1 = nn.ReLU()
        self.drop1 = nn.Dropout(dropout_rate)
        
        self.fc2 = nn.Linear(hidden_dim * 2, hidden_dim)
        self.bn2 = nn.BatchNorm1d(hidden_dim)
        self.relu2 = nn.ReLU()
        self.drop2 = nn.Dropout(dropout_rate * 0.7)
        
        self.fc3 = nn.Linear(hidden_dim, 64)
        self.relu3 = nn.ReLU()
        
        self.out = nn.Linear(64, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, top: torch.Tensor, bottom: torch.Tensor, footwear: torch.Tensor) -> torch.Tensor:
        if top.dim() == 1:
            top = top.unsqueeze(0)
            bottom = bottom.unsqueeze(0)
            footwear = footwear.unsqueeze(0)

        prod_tb = top * bottom
        prod_ts = top * footwear
        prod_bs = bottom * footwear
        
        diff_tb = torch.abs(top - bottom)
        diff_ts = torch.abs(top - footwear)
        diff_bs = torch.abs(bottom - footwear)
        
        features = torch.cat([top, bottom, footwear, prod_tb, prod_ts, prod_bs, diff_tb, diff_ts, diff_bs], dim=-1)
        
        x = self.drop1(self.relu1(self.bn1(self.fc1(features))))
        x = self.drop2(self.relu2(self.bn2(self.fc2(x))))
        x = self.relu3(self.fc3(x))
        out = self.sigmoid(self.out(x))
        return out

class NeuralScorerService:
    _instance = None

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self._model_mtime = 0
        self.reload_if_updated()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = NeuralScorerService()
        return cls._instance

    def reload_if_updated(self):
        """Checks if a new checkpoint has been trained and saved by the user."""
        if BEST_MODEL_PATH.exists():
            mtime = BEST_MODEL_PATH.stat().st_mtime
            if mtime > self._model_mtime or self.model is None:
                try:
                    print(f"[NeuralScorer] Loading newly trained checkpoint from {BEST_MODEL_PATH}...")
                    model = OutfitCompatibilityNet().to(self.device)
                    state_dict = torch.load(BEST_MODEL_PATH, map_location=self.device)
                    model.load_state_dict(state_dict)
                    model.eval()
                    self.model = model
                    self._model_mtime = mtime
                    print("[NeuralScorer] Trained neural scorer loaded successfully.")
                except Exception as e:
                    print(f"[NeuralScorer] Failed to load trained checkpoint: {e}")
                    self.model = None
        else:
            self.model = None

    def is_trained_model_available(self) -> bool:
        self.reload_if_updated()
        return self.model is not None

    def score_outfit(self, top: ClothingItem, bottom: ClothingItem, footwear: ClothingItem) -> float | None:
        """
        Scores outfit using the trained PyTorch neural model.
        Returns score in [0.0, 100.0] or None if not trained yet.
        """
        self.reload_if_updated()
        if self.model is None:
            return None

        try:
            t_emb = np.array(top.clip_embedding, dtype=np.float32)
            b_emb = np.array(bottom.clip_embedding, dtype=np.float32)
            f_emb = np.array(footwear.clip_embedding, dtype=np.float32)

            if len(t_emb) != 512 or len(b_emb) != 512 or len(f_emb) != 512:
                return None

            t_t = torch.tensor(t_emb).unsqueeze(0).to(self.device)
            b_t = torch.tensor(b_emb).unsqueeze(0).to(self.device)
            f_t = torch.tensor(f_emb).unsqueeze(0).to(self.device)

            with torch.no_grad():
                pred = self.model(t_t, b_t, f_t).item()

            return round(pred * 100.0, 1)
        except Exception as e:
            print(f"[NeuralScorer] Inference error: {e}")
            return None

neural_scorer = NeuralScorerService.get_instance()
