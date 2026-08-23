from app.config import OCCASION_RULES, get_warmth_range_for_temp
from app.models.clothing_item import ClothingItem

def is_item_suitable_for_occasion(item: ClothingItem, occasion: str) -> tuple[bool, str]:
    """
    Checks if a clothing item fits the specified occasion.
    Returns (is_valid, reason).
    """
    rule = OCCASION_RULES.get(occasion.lower(), OCCASION_RULES["college"])
    
    # Check category
    if item.category not in rule["allowed_categories"]:
        return False, f"Category '{item.category}' not allowed for {occasion}"
        
    # Check disallowed subcategories
    if item.subcategory.lower() in [d.lower() for d in rule.get("disallowed_subcategories", [])]:
        return False, f"'{item.subcategory}' is not appropriate for {occasion}"
        
    # Check explicit user occasion tags if assigned
    item_occasions = [t.lower() for t in item.occasion_tags]
    if item_occasions and occasion.lower() in item_occasions:
        return True, "User tagged for occasion"

    # Check formality bounds
    if item.formality_level < rule["formality_min"]:
        return False, f"Formality ({item.formality_level}) too low for {occasion} (needs >={rule['formality_min']})"
    if item.formality_level > rule["formality_max"]:
        return False, f"Formality ({item.formality_level}) too high for {occasion} (needs <={rule['formality_max']})"
        
    return True, "Appropriate formality and style"

def is_item_suitable_for_weather(item: ClothingItem, temp_celsius: float) -> tuple[bool, float]:
    """
    Evaluates item warmth compatibility against current temperature.
    Returns (is_passable, penalty_factor).
    """
    min_w, max_w = get_warmth_range_for_temp(temp_celsius)
    item_w = item.warmth_level
    
    if min_w <= item_w <= max_w:
        return True, 1.0  # Perfect warmth match
        
    # Distance from ideal range
    dist = min(abs(item_w - min_w), abs(item_w - max_w))
    if dist == 1:
        return True, 0.85  # Acceptable with slight penalty
    elif dist == 2:
        return True, 0.60  # Marginal
    else:
        return False, 0.20 # Too hot or too cold
