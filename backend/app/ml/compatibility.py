import numpy as np
from app.models.clothing_item import ClothingItem
from app.ml.color_extractor import calculate_color_harmony_score

def compute_cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.5
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.5
        
    dot = np.dot(a, b) / (norm_a * norm_b)
    # Scale from [-1, 1] to [0, 1]
    return float((dot + 1.0) / 2.0)

def score_outfit_baseline(
    top: ClothingItem,
    bottom: ClothingItem,
    footwear: ClothingItem,
    outerwear: ClothingItem = None,
    weather_temp: float = 22.0
) -> tuple[float, float, float, list[str]]:
    """
    Evaluates visual and aesthetic compatibility of an outfit combination.
    Returns (compatibility_score, color_harmony_score, total_score, match_reasons).
    """
    reasons = []
    
    # 1. Visual Embedding Pairwise Cosine Similarities
    sim_tb = compute_cosine_similarity(top.clip_embedding, bottom.clip_embedding)
    sim_ts = compute_cosine_similarity(top.clip_embedding, footwear.clip_embedding)
    sim_bs = compute_cosine_similarity(bottom.clip_embedding, footwear.clip_embedding)
    
    sim_components = [sim_tb * 0.40, sim_ts * 0.30, sim_bs * 0.30]
    visual_sim = sum(sim_components)
    
    if outerwear:
        sim_ot = compute_cosine_similarity(outerwear.clip_embedding, top.clip_embedding)
        sim_ob = compute_cosine_similarity(outerwear.clip_embedding, bottom.clip_embedding)
        sim_os = compute_cosine_similarity(outerwear.clip_embedding, footwear.clip_embedding)
        visual_sim = (visual_sim * 0.70) + (((sim_ot + sim_ob + sim_os) / 3.0) * 0.30)
        
    # Scale visual similarity to 0-100
    compat_score = round(min(max(visual_sim * 100.0, 10.0), 99.0), 1)
    
    # 2. Color Harmony
    hexes = [top.dominant_color_hex, bottom.dominant_color_hex, footwear.dominant_color_hex]
    if outerwear:
        hexes.append(outerwear.dominant_color_hex)
        
    harmony_val, harmony_reason = calculate_color_harmony_score(hexes)
    color_score = round(harmony_val * 100.0, 1)
    
    # Editorial Styling Insights
    reasons.append(f"{harmony_reason} featuring {top.dominant_color_name} and {bottom.dominant_color_name}")
    
    # 3. Silhouette & Formality Cohesion
    formality_diff = abs(top.formality_level - bottom.formality_level)
    if formality_diff == 0:
        reasons.append(f"Impeccable silhouette harmony and aligned aesthetic formality")
    elif formality_diff == 1:
        reasons.append(f"Balanced smart-casual styling with natural proportions")
    else:
        reasons.append(f"High-low statement contrast pairing")

    # 4. Total Composite Score
    total_score = round((compat_score * 0.65) + (color_score * 0.35), 1)
    
    return compat_score, color_score, total_score, reasons
