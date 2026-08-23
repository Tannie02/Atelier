"""
Outfit Compatibility Neural Network Architecture
=================================================
This PyTorch module implements a Deep Compatibility Scorer for fashion items.

Mathematical Formulation:
-------------------------
Given three item embeddings extracted from CLIP:
  - e_top      in R^512
  - e_bottom   in R^512
  - e_footwear in R^512

To learn non-linear cross-item interactions, we compute:
  1. Element-wise Product (Hadamard Product):
     e_i ⊙ e_j  -> captures feature correlation & semantic alignment
  2. Absolute Difference:
     |e_i - e_j| -> captures feature distance & style contrast
  3. Raw Features:
     [e_top, e_bottom, e_footwear]

The combined feature vector x in R^(9 * 512) = R^4608 is passed through
a Multi-Layer Perceptron (MLP) with Batch Normalization, Dropout, and ReLU:
  h_1 = ReLU(BN(W_1 x + b_1))
  h_2 = ReLU(BN(W_2 h_1 + b_2))
  y_hat = Sigmoid(W_3 h_2 + b_3)  in [0, 1]

y_hat represents the probability that the outfit is visually & aesthetically compatible.
"""

import torch
import torch.nn as nn

class OutfitCompatibilityNet(nn.Module):
    def __init__(self, emb_dim: int = 512, hidden_dim: int = 256, dropout_rate: float = 0.3):
        super().__init__()
        
        # 3 raw vectors + 3 Hadamard products + 3 absolute differences = 9 * emb_dim
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
        """
        Args:
            top: Tensor of shape (Batch_Size, 512)
            bottom: Tensor of shape (Batch_Size, 512)
            footwear: Tensor of shape (Batch_Size, 512)
        Returns:
            Tensor of shape (Batch_Size, 1) with compatibility score in [0.0, 1.0]
        """
        # Ensure 2D (Batch_Size, 512)
        if top.dim() == 1:
            top = top.unsqueeze(0)
            bottom = bottom.unsqueeze(0)
            footwear = footwear.unsqueeze(0)

        # 1. Hadamard Products (Correlation)
        prod_tb = top * bottom
        prod_ts = top * footwear
        prod_bs = bottom * footwear
        
        # 2. Absolute Differences (Contrast)
        diff_tb = torch.abs(top - bottom)
        diff_ts = torch.abs(top - footwear)
        diff_bs = torch.abs(bottom - footwear)
        
        # 3. Concatenate feature representation
        features = torch.cat(
            [top, bottom, footwear, prod_tb, prod_ts, prod_bs, diff_tb, diff_ts, diff_bs], 
            dim=-1
        )
        
        # 4. Forward through MLP
        x = self.drop1(self.relu1(self.bn1(self.fc1(features))))
        x = self.drop2(self.relu2(self.bn2(self.fc2(x))))
        x = self.relu3(self.fc3(x))
        out = self.sigmoid(self.out(x))
        
        return out
