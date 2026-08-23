"""
Dataset Loader & Synthesizer for Outfit Compatibility
=====================================================
Builds balanced binary classification datasets (Positive = 1: Compatible, Negative = 0: Incompatible).
Loads from:
  1. Real user feedback (Likes / Dislikes) from the SQLite database.
  2. Grounded synthetic fashion pairs generated from wardrobe items / style theory.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.append(str(backend_path))

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.clothing_item import ClothingItem
from app.models.feedback import OutfitFeedback
from app.models.outfit import OutfitRecommendation

class OutfitDataset(Dataset):
    def __init__(self, top_embeddings, bottom_embeddings, footwear_embeddings, labels):
        self.tops = torch.tensor(top_embeddings, dtype=torch.float32)
        self.bottoms = torch.tensor(bottom_embeddings, dtype=torch.float32)
        self.shoes = torch.tensor(footwear_embeddings, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32).unsqueeze(1)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.tops[idx], self.bottoms[idx], self.shoes[idx], self.labels[idx]

def create_synthetic_grounded_samples(items: list[ClothingItem], num_samples: int = 500) -> tuple:
    """
    Generates balanced positive & negative outfit embedding pairs from available wardrobe items
    or high-quality fashion prototypes.
    """
    np.random.seed(42)
    
    # Categorize items
    tops = [i for i in items if i.category == "top" and len(i.clip_embedding) == 512]
    bottoms = [i for i in items if i.category == "bottom" and len(i.clip_embedding) == 512]
    shoes = [i for i in items if i.category == "footwear" and len(i.clip_embedding) == 512]
    
    # If not enough items in wardrobe, generate high-quality pseudo-embeddings with controlled clusters
    if len(tops) < 2 or len(bottoms) < 2 or len(shoes) < 2:
        print("[Dataset] Generating synthetic fashion prototypes for bootstrap training...")
        
        # Define 4 fashion style clusters: (1) Casual, (2) Formal, (3) Sporty, (4) Streetwear
        cluster_centers = [np.random.randn(512) for _ in range(4)]
        cluster_centers = [c / np.linalg.norm(c) for c in cluster_centers]
        
        top_list, bot_list, sho_list, labels_list = [], [], [], []
        
        # Positive pairs (items from the SAME style cluster with minor variation)
        for _ in range(num_samples // 2):
            c_idx = np.random.randint(0, 4)
            center = cluster_centers[c_idx]
            
            # Add small noise (simulating items of same aesthetic)
            t_vec = center + np.random.randn(512) * 0.15
            b_vec = center + np.random.randn(512) * 0.15
            s_vec = center + np.random.randn(512) * 0.15
            
            top_list.append(t_vec / np.linalg.norm(t_vec))
            bot_list.append(b_vec / np.linalg.norm(b_vec))
            sho_list.append(s_vec / np.linalg.norm(s_vec))
            labels_list.append(1.0)
            
        # Negative pairs (items from DIFFERENT conflicting style clusters, e.g. formal blazer + gym sweatpants + sandals)
        for _ in range(num_samples // 2):
            c1, c2, c3 = np.random.choice(4, 3, replace=False)
            t_vec = cluster_centers[c1] + np.random.randn(512) * 0.2
            b_vec = cluster_centers[c2] + np.random.randn(512) * 0.2
            s_vec = cluster_centers[c3] + np.random.randn(512) * 0.2
            
            top_list.append(t_vec / np.linalg.norm(t_vec))
            bot_list.append(b_vec / np.linalg.norm(b_vec))
            sho_list.append(s_vec / np.linalg.norm(s_vec))
            labels_list.append(0.0)
            
        return np.array(top_list), np.array(bot_list), np.array(sho_list), np.array(labels_list)
        
    top_list, bot_list, sho_list, labels_list = [], [], [], []
    
    # Positive pairs: Formality matching items
    for _ in range(num_samples // 2):
        t = np.random.choice(tops)
        # Find bottoms with close formality
        compatible_bottoms = [b for b in bottoms if abs(b.formality_level - t.formality_level) <= 1] or bottoms
        b = np.random.choice(compatible_bottoms)
        compatible_shoes = [s for s in shoes if abs(s.formality_level - t.formality_level) <= 1] or shoes
        s = np.random.choice(compatible_shoes)
        
        top_list.append(t.clip_embedding)
        bot_list.append(b.clip_embedding)
        sho_list.append(s.clip_embedding)
        labels_list.append(1.0)
        
    # Negative pairs: Clashing formality & style
    for _ in range(num_samples // 2):
        t = np.random.choice(tops)
        # Find clashing bottoms (formality diff >= 2)
        clashing_bottoms = [b for b in bottoms if abs(b.formality_level - t.formality_level) >= 2] or bottoms
        b = np.random.choice(clashing_bottoms)
        s = np.random.choice(shoes)
        
        top_list.append(t.clip_embedding)
        bot_list.append(b.clip_embedding)
        sho_list.append(s.clip_embedding)
        labels_list.append(0.0)
        
    return np.array(top_list), np.array(bot_list), np.array(sho_list), np.array(labels_list)

def load_outfit_data(val_split: float = 0.2, batch_size: int = 32, num_synthetic: int = 600):
    """
    Main data loader function.
    Combines real database feedback + synthetic grounded pairs.
    """
    db: Session = SessionLocal()
    items = db.query(ClothingItem).all()
    feedbacks = db.query(OutfitFeedback).all()
    
    real_tops, real_bots, real_shoes, real_labels = [], [], [], []
    
    for fb in feedbacks:
        outfit = fb.outfit
        if not outfit:
            continue
        top = db.query(ClothingItem).filter(ClothingItem.id == outfit.top_id).first()
        bot = db.query(ClothingItem).filter(ClothingItem.id == outfit.bottom_id).first()
        shoe = db.query(ClothingItem).filter(ClothingItem.id == outfit.footwear_id).first()
        
        if top and bot and shoe and top.clip_embedding and bot.clip_embedding and shoe.clip_embedding:
            real_tops.append(top.clip_embedding)
            real_bots.append(bot.clip_embedding)
            real_shoes.append(shoe.clip_embedding)
            real_labels.append(1.0 if fb.rating == 1 else 0.0)
            
    db.close()
    
    # Generate synthetic pairs
    syn_tops, syn_bots, syn_shoes, syn_labels = create_synthetic_grounded_samples(items, num_samples=num_synthetic)
    
    if real_tops:
        # Over-sample real user feedback to give it higher priority
        user_weight_multiplier = 5
        tops_all = np.vstack([syn_tops] + [np.array(real_tops)] * user_weight_multiplier)
        bots_all = np.vstack([syn_bots] + [np.array(real_bots)] * user_weight_multiplier)
        shoes_all = np.vstack([syn_shoes] + [np.array(real_shoes)] * user_weight_multiplier)
        labels_all = np.concatenate([syn_labels] + [np.array(real_labels)] * user_weight_multiplier)
        print(f"[Dataset] Loaded {len(real_tops)} real user feedback interactions + {len(syn_labels)} synthetic pairs.")
    else:
        tops_all, bots_all, shoes_all, labels_all = syn_tops, syn_bots, syn_shoes, syn_labels
        print(f"[Dataset] Loaded {len(syn_labels)} bootstrap training pairs (0 user feedback interactions yet).")
        
    # Shuffle
    indices = np.arange(len(labels_all))
    np.random.shuffle(indices)
    
    split_idx = int(len(indices) * (1 - val_split))
    train_idx = indices[:split_idx]
    val_idx = indices[split_idx:]
    
    train_dataset = OutfitDataset(tops_all[train_idx], bots_all[train_idx], shoes_all[train_idx], labels_all[train_idx])
    val_dataset = OutfitDataset(tops_all[val_idx], bots_all[val_idx], shoes_all[val_idx], labels_all[val_idx])
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, val_loader

if __name__ == "__main__":
    t_loader, v_loader = load_outfit_data(num_synthetic=200)
    print(f"Data loading test passed! Train batches: {len(t_loader)}, Val batches: {len(v_loader)}")
