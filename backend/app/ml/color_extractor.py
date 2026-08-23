import math
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

# Curated Palette of Named Fashion Colors with representative sRGB values
NAMED_COLORS = {
    "Black": (20, 20, 20),
    "White": (245, 245, 245),
    "Off-White / Cream": (240, 235, 220),
    "Charcoal": (50, 50, 55),
    "Heather Grey": (140, 142, 145),
    "Light Grey": (195, 198, 200),
    "Navy Blue": (15, 30, 70),
    "Denim / Indigo Blue": (40, 70, 120),
    "Sky Blue": (120, 175, 230),
    "Midnight Blue": (10, 15, 35),
    "Forest Green": (25, 65, 35),
    "Olive Green": (85, 95, 45),
    "Sage Green": (140, 160, 135),
    "Khaki / Beige": (190, 175, 140),
    "Camel / Tan": (175, 125, 75),
    "Dark Brown": (60, 40, 25),
    "Burgundy / Maroon": (90, 20, 35),
    "Crimson Red": (180, 30, 40),
    "Terracotta / Rust": (175, 75, 45),
    "Mustard Yellow": (210, 160, 30),
    "Pastel Pink": (230, 180, 190),
    "Lavender / Lilac": (180, 160, 210),
    "Teal / Emerald": (20, 110, 105),
}

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Converts RGB integers (0-255) to hex string."""
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

def color_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    """
    Computes weighted Euclidean distance in RGB space (approximating human eye sensitivity).
    Weights: Red (0.30), Green (0.59), Blue (0.11).
    """
    r_mean = (c1[0] + c2[0]) / 2
    r = c1[0] - c2[0]
    g = c1[1] - c2[1]
    b = c1[2] - c2[2]
    # Standard redmean formula for perceptually uniform color distance
    weight_r = 2 + (r_mean / 256.0)
    weight_g = 4.0
    weight_b = 2 + ((255 - r_mean) / 256.0)
    return math.sqrt(weight_r * (r ** 2) + weight_g * (g ** 2) + weight_b * (b ** 2))

def get_nearest_color_name(rgb: tuple[int, int, int]) -> str:
    """Finds closest fashion color name from predefined palette."""
    best_name = "Grey"
    min_dist = float("inf")
    
    for name, palette_rgb in NAMED_COLORS.items():
        dist = color_distance(rgb, palette_rgb)
        if dist < min_dist:
            min_dist = dist
            best_name = name
            
    return best_name

def extract_dominant_colors(image_path: str, n_colors: int = 3) -> tuple[str, str, list[dict]]:
    """
    Extracts dominant colors from an image using K-Means clustering on the central 70% region.
    Returns (dominant_color_name, dominant_color_hex, list_of_secondary_colors).
    """
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            
            # Crop center 70% to avoid background edges
            width, height = img.size
            left = int(width * 0.15)
            top = int(height * 0.15)
            right = int(width * 0.85)
            bottom = int(height * 0.85)
            cropped = img.crop((left, top, right, bottom))
            
            # Resize for fast clustering
            cropped.thumbnail((150, 150))
            np_img = np.array(cropped)
            pixels = np_img.reshape(-1, 3)
            
            # Filter out almost-pure white background pixels (common in studio / flat lay photos)
            # if > 85% of pixels are near white (> 240, 240, 240)
            non_white_mask = ~((pixels[:, 0] > 240) & (pixels[:, 1] > 240) & (pixels[:, 2] > 240))
            if np.sum(non_white_mask) > (len(pixels) * 0.1):  # If at least 10% non-white
                filtered_pixels = pixels[non_white_mask]
            else:
                filtered_pixels = pixels
                
            kmeans = KMeans(n_clusters=n_colors, n_init=5, random_state=42)
            kmeans.fit(filtered_pixels)
            
            # Get cluster counts and centroids
            labels, counts = np.unique(kmeans.labels_, return_counts=True)
            total_count = len(filtered_pixels)
            
            # Sort by frequency
            sorted_indices = np.argsort(-counts)
            
            palette = []
            for idx in sorted_indices:
                centroid = kmeans.cluster_centers_[idx]
                rgb = (int(centroid[0]), int(centroid[1]), int(centroid[2]))
                hex_code = rgb_to_hex(*rgb)
                name = get_nearest_color_name(rgb)
                pct = round((counts[idx] / total_count) * 100, 1)
                
                palette.append({
                    "name": name,
                    "hex": hex_code,
                    "percentage": pct
                })
                
            primary_name = palette[0]["name"]
            primary_hex = palette[0]["hex"]
            return primary_name, primary_hex, palette
            
    except Exception as e:
        print(f"Error extracting colors: {e}")
        return "Heather Grey", "#8c8e91", [{"name": "Heather Grey", "hex": "#8c8e91", "percentage": 100.0}]

def calculate_color_harmony_score(hex_list: list[str]) -> tuple[float, str]:
    """
    Scores color harmony (0.0 to 1.0) and generates an aesthetic explanation.
    Uses color temperature, neutrality rules, and high-fashion contrast pairing.
    """
    if not hex_list or len(hex_list) < 2:
        return 0.8, "Balanced standard tones"
        
    def hex_to_rgb(h: str):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        
    def is_neutral(name: str) -> bool:
        neutrals = ["Black", "White", "Off-White / Cream", "Charcoal", "Heather Grey", "Light Grey", "Navy Blue", "Khaki / Beige", "Dark Brown"]
        return any(neu.lower() in name.lower() for neu in neutrals)

    names = [get_nearest_color_name(hex_to_rgb(h)) for h in hex_list]
    
    # Rule 1: All neutrals (Monochrome / Minimalist Classic) -> High score
    if all(is_neutral(n) for n in names):
        return 0.95, "Timeless Neutral & Minimalist Coordination"
        
    # Rule 2: 1 Statement Color + Neutral Anchor (e.g. Olive + Beige + White, or Burgundy + Navy)
    neutral_count = sum(1 for n in names if is_neutral(n))
    if neutral_count >= 1:
        return 0.88, "Harmonious Statement + Neutral Anchor Pair"
        
    # Rule 3: Multiple non-neutral colors
    return 0.70, "Bold Color Combination"
