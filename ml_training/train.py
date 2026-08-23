"""
Outfit Compatibility Scorer — Training Script 🎓
================================================
Train your deep neural outfit compatibility model!

Usage:
------
python train.py --epochs 25 --lr 0.001 --batch_size 32

What happens during training:
1. Loads fashion embeddings and user feedback pairs from dataset.py.
2. Initializes OutfitCompatibilityNet (MLP with Hadamard & Difference interactions).
3. Trains with Binary Cross Entropy (BCE) Loss and AdamW optimizer.
4. Tracks Validation Loss, Accuracy (%), and ROC-AUC.
5. Saves best model weights to `checkpoints/best_scorer.pt`.
6. Once saved, the FastAPI backend immediately uses your newly trained model!
"""

import os
import sys
import argparse
import time
from pathlib import Path

# Add project paths
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent
BACKEND_DIR = PROJECT_DIR / "backend"
sys.path.append(str(BACKEND_DIR))
sys.path.append(str(CURRENT_DIR))

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from sklearn.metrics import roc_auc_score

from model import OutfitCompatibilityNet
from dataset import load_outfit_data

def train_model(
    epochs: int = 25,
    lr: float = 0.001,
    batch_size: int = 32,
    hidden_dim: int = 256,
    weight_decay: float = 1e-4,
    val_split: float = 0.2,
    num_samples: int = 800,
    seed: int = 42
):
    # Set random seeds for reproducibility
    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    print("=" * 70)
    print("[ML HUB] OUTFIT COMPATIBILITY MODEL TRAINING")
    print(f"Device:            {device}")
    print(f"Epochs:            {epochs}")
    print(f"Learning Rate:     {lr}")
    print(f"Batch Size:        {batch_size}")
    print(f"Hidden Dimension:  {hidden_dim}")
    print("=" * 70)

    # 1. Load Dataset
    print("\n[Step 1/4] Preparing dataset...")
    train_loader, val_loader = load_outfit_data(
        val_split=val_split, 
        batch_size=batch_size, 
        num_synthetic=num_samples
    )
    print(f"-> Train samples: {len(train_loader.dataset)}, Validation samples: {len(val_loader.dataset)}")

    # 2. Instantiate Model, Loss Function, and Optimizer
    print("\n[Step 2/4] Initializing OutfitCompatibilityNet...")
    model = OutfitCompatibilityNet(emb_dim=512, hidden_dim=hidden_dim).to(device)
    
    criterion = nn.BCELoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=4, verbose=True)

    # Checkpoint output directory
    checkpoint_dir = CURRENT_DIR / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    best_model_path = checkpoint_dir / "best_scorer.pt"

    # 3. Training Loop
    print("\n[Step 3/4] Starting training loop...")
    best_val_loss = float("inf")
    best_val_acc = 0.0

    start_time = time.time()

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        train_correct = 0
        total_train = 0

        for tops, bottoms, shoes, labels in train_loader:
            tops = tops.to(device)
            bottoms = bottoms.to(device)
            shoes = shoes.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            predictions = model(tops, bottoms, shoes)
            loss = criterion(predictions, labels)
            
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * len(labels)
            preds_binary = (predictions >= 0.5).float()
            train_correct += (preds_binary == labels).sum().item()
            total_train += len(labels)

        avg_train_loss = train_loss / total_train
        train_acc = (train_correct / total_train) * 100.0

        # Evaluation on Validation set
        model.eval()
        val_loss = 0.0
        val_correct = 0
        total_val = 0
        all_val_preds = []
        all_val_labels = []

        with torch.no_grad():
            for tops, bottoms, shoes, labels in val_loader:
                tops = tops.to(device)
                bottoms = bottoms.to(device)
                shoes = shoes.to(device)
                labels = labels.to(device)

                predictions = model(tops, bottoms, shoes)
                loss = criterion(predictions, labels)

                val_loss += loss.item() * len(labels)
                preds_binary = (predictions >= 0.5).float()
                val_correct += (preds_binary == labels).sum().item()
                total_val += len(labels)

                all_val_preds.extend(predictions.cpu().squeeze().tolist())
                all_val_labels.extend(labels.cpu().squeeze().tolist())

        avg_val_loss = val_loss / total_val
        val_acc = (val_correct / total_val) * 100.0
        
        try:
            val_auc = roc_auc_score(all_val_labels, all_val_preds) * 100.0
        except Exception:
            val_auc = 50.0

        scheduler.step(avg_val_loss)

        # Check for best model
        saved_tag = ""
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_val_acc = val_acc
            torch.save(model.state_dict(), best_model_path)
            saved_tag = "* [BEST MODEL SAVED!]"

        print(
            f"Epoch [{epoch:02d}/{epochs:02d}] | "
            f"Train Loss: {avg_train_loss:.4f} (Acc: {train_acc:.1f}%) | "
            f"Val Loss: {avg_val_loss:.4f} (Acc: {val_acc:.1f}%, AUC: {val_auc:.1f}%) "
            f"{saved_tag}"
        )

    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print("[SUCCESS] TRAINING COMPLETE!")
    print(f"Total Time:         {total_time:.2f} seconds")
    print(f"Best Val Loss:      {best_val_loss:.4f}")
    print(f"Best Val Accuracy:  {best_val_acc:.1f}%")
    print(f"Model saved to:     {best_model_path}")
    print("=" * 70)
    print("\n[NOTE] The FastAPI backend has now detected your new weights.")
    print("All subsequent outfit recommendations will use your trained Neural Scorer!\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Outfit Compatibility Scorer")
    parser.add_argument("--epochs", type=int, default=25, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=0.001, help="Initial learning rate")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--hidden_dim", type=int, default=256, help="Hidden layer neurons")
    parser.add_argument("--samples", type=int, default=800, help="Number of synthetic samples to synthesize")
    args = parser.parse_args()

    train_model(
        epochs=args.epochs,
        lr=args.lr,
        batch_size=args.batch_size,
        hidden_dim=args.hidden_dim,
        num_samples=args.samples
    )
