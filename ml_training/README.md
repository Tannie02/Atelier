# 🎓 Machine Learning Training Hub — Outfit Picker

Welcome to your ML training workspace! This directory contains everything you need to understand, train, evaluate, and tune your own **Deep Neural Outfit Compatibility Model**.

---

## 🧠 1. The Machine Learning Concept

### A. The Challenge: Why Simple Cosine Similarity Is Not Enough
When pairing a shirt, trousers, and shoes:
- Two items don't just need to be "similar" in embedding space (e.g. an all-red shirt, red pants, and red shoes might have high cosine similarity, but might look overwhelming).
- Good fashion requires **cohesion, contrast, and complementary harmony** (e.g. Navy Blue blazer + Khaki chinos + Dark Brown loafers).
- Standard zero-shot CLIP vectors capture semantic appearance, but a **learned compatibility model** can discover non-linear synergies between items and adapt to user likes/dislikes.

### B. The Neural Network Architecture (`OutfitCompatibilityNet`)
Given three 512-dimensional CLIP vectors $\mathbf{e}_{\text{top}}, \mathbf{e}_{\text{bottom}}, \mathbf{e}_{\text{shoes}} \in \mathbb{R}^{512}$:

1. **Correlation Interactions (Hadamard Products)**:
   $$\mathbf{p}_{tb} = \mathbf{e}_t \odot \mathbf{e}_b, \quad \mathbf{p}_{ts} = \mathbf{e}_t \odot \mathbf{e}_s, \quad \mathbf{p}_{bs} = \mathbf{e}_b \odot \mathbf{e}_s$$
2. **Contrast Interactions (Absolute Differences)**:
   $$\mathbf{d}_{tb} = |\mathbf{e}_t - \mathbf{e}_b|, \quad \mathbf{d}_{ts} = |\mathbf{e}_t - \mathbf{e}_s|, \quad \mathbf{d}_{bs} = |\mathbf{e}_b - \mathbf{e}_s|$$
3. **Feature Concatenation**:
   $$\mathbf{x} = [\mathbf{e}_t \,\|\, \mathbf{e}_b \,\|\, \mathbf{e}_s \,\|\, \mathbf{p}_{tb} \,\|\, \mathbf{p}_{ts} \,\|\, \mathbf{p}_{bs} \,\|\, \mathbf{d}_{tb} \,\|\, \mathbf{d}_{ts} \,\|\, \mathbf{d}_{bs}] \in \mathbb{R}^{4608}$$
4. **Non-Linear MLP with Regularization**:
   $$\mathbf{h}_1 = \text{Dropout}_{0.3}(\text{ReLU}(\text{BatchNorm}(\mathbf{W}_1 \mathbf{x} + \mathbf{b}_1)))$$
   $$\mathbf{h}_2 = \text{Dropout}_{0.2}(\text{ReLU}(\text{BatchNorm}(\mathbf{W}_2 \mathbf{h}_1 + \mathbf{b}_2)))$$
   $$\hat{y} = \sigma(\mathbf{W}_4 \text{ReLU}(\mathbf{W}_3 \mathbf{h}_2 + \mathbf{b}_3) + b_4) \in [0, 1]$$

### C. The Loss Function: Binary Cross-Entropy (BCE)
$$\mathcal{L} = -\frac{1}{N} \sum_{i=1}^{N} \left[ y_i \log(\hat{y}_i) + (1 - y_i) \log(1 - \hat{y}_i) \right]$$
- $y_i = 1.0$: Harmonious / Compatible Outfit (User Like or Style-Matched Pair).
- $y_i = 0.0$: Clashing / Incompatible Outfit (User Dislike or Stylistically Conflicting Triplet).

---

## 🚀 2. How to Train Your Model (Step-by-Step)

### Step 1: Open Your Terminal
Navigate to the project root or the `ml_training` directory:
```powershell
cd C:\Users\taran\.gemini\antigravity\scratch\outfit_picker\ml_training
```

### Step 2: Run Training
Execute the training script:
```powershell
python train.py --epochs 30 --lr 0.001 --batch_size 32
```

You will see the interactive training progress:
```
🎓 OUTFIT COMPATIBILITY MODEL TRAINING
Device:            cpu (or cuda)
Epochs:            30
Learning Rate:     0.001
Batch Size:        32
----------------------------------------------------------------------
Epoch [01/30] | Train Loss: 0.5821 (Acc: 68.4%) | Val Loss: 0.5104 (Acc: 74.2%, AUC: 81.5%) 🌟 [Best Model Saved!]
Epoch [05/30] | Train Loss: 0.3214 (Acc: 86.1%) | Val Loss: 0.3412 (Acc: 84.8%, AUC: 91.2%) 🌟 [Best Model Saved!]
Epoch [15/30] | Train Loss: 0.1845 (Acc: 93.5%) | Val Loss: 0.2210 (Acc: 90.6%, AUC: 96.1%) 🌟 [Best Model Saved!]
🎉 TRAINING COMPLETE! Best Val Accuracy: 90.6%
Model saved to: checkpoints/best_scorer.pt
```

### Step 3: Evaluate & Test Predictions
Run the evaluation test script:
```powershell
python evaluate.py
```

### Step 4: Live Web App Integration
Once `best_scorer.pt` is generated in `ml_training/checkpoints/`, the FastAPI backend **hot-reloads your trained neural model automatically**. When you click **"Generate Outfits"** on the web app, you will see:
> **Scoring Engine**: `Neural Scorer (Trained)` instead of the baseline cosine scorer!

---

## 🧪 3. Hyperparameter Experiments to Try

Try experimenting with these parameters to see how they impact training dynamics and validation accuracy:

1. **Learning Rate & Optimizer**:
   - High learning rate (`--lr 0.01`): Watch if loss oscillates.
   - Low learning rate (`--lr 0.0001`): Watch if it converges slower.
2. **Hidden Dimensions**:
   - `--hidden_dim 128` vs `--hidden_dim 512`
3. **Sample Size**:
   - `--samples 1500` for higher dataset volume.

---

## 🔄 4. The Active Personalization Feedback Loop

1. When you use the web app and click **Thumbs Up 👍** or **Thumbs Down 👎** on outfits, your votes are stored in `backend/wardrobe.db`.
2. When you run `python train.py`, `dataset.py` automatically pulls your personal feedback and over-samples it into the training batches.
3. Over time, your neural model learns **your specific style preferences**!
