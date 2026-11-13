import math
import numpy as np
from PIL import Image
import io

def hex_to_rgb(hex_code):
    """Converts a hex string like '#8955D9' to an (R, G, B) tuple."""
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 3:
        hex_code = "".join([c * 2 for c in hex_code])
    if len(hex_code) != 6:
        return (128, 128, 128)
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    """Converts an (R, G, B) tuple to a '#RRGGBB' hex string."""
    return f"#{int(rgb[0]):02X}{int(rgb[1]):02X}{int(rgb[2]):02X}"

def color_distance(rgb1, rgb2):
    """Calculates weighted Euclidean RGB distance approximating human perception."""
    # Redmean formula
    r_bar = 0.5 * (rgb1[0] + rgb2[0])
    delta_r = rgb1[0] - rgb2[0]
    delta_g = rgb1[1] - rgb2[1]
    delta_b = rgb1[2] - rgb2[2]
    dist_sq = (2 + r_bar / 256.0) * (delta_r ** 2) + 4.0 * (delta_g ** 2) + (2 + (255 - r_bar) / 256.0) * (delta_b ** 2)
    return math.sqrt(dist_sq)

def extract_dominant_colors(image_input, max_colors=5):
    """
    Extracts the top dominant colors from an image using Pillow & NumPy.
    Input can be a PIL Image, file path, or bytes.
    """
    if isinstance(image_input, (str, bytes)):
        if isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input))
        else:
            img = Image.open(image_input)
    else:
        img = image_input

    # Convert to RGB mode and resize for fast sampling
    img = img.convert("RGB")
    small_img = img.resize((150, 150))
    pixels = np.array(small_img).reshape(-1, 3)

    # Simple quantization: round RGB values to nearest step of 32
    quantized = (pixels // 32) * 32 + 16
    unique_colors, counts = np.unique(quantized, axis=0, return_counts=True)

    sorted_indices = np.argsort(counts)[::-1]
    dominant = []
    total_pixels = len(pixels)

    for i in sorted_indices[:max_colors]:
        color = unique_colors[i]
        percentage = float(round((float(counts[i]) / float(total_pixels)) * 100, 1))
        rgb_tuple = (int(color[0]), int(color[1]), int(color[2]))
        dominant.append({
            "hex": rgb_to_hex(rgb_tuple),
            "rgb": rgb_tuple,
            "percentage": percentage
        })

    return dominant, img.size

def verify_visual_compliance(image_input, approved_palette, visual_rules=None):
    """
    Verifies an image against approved brand colors and visual guidelines.
    Returns compliance score, detected violations, and palette comparison.
    """
    try:
        dominant_colors, dimensions = extract_dominant_colors(image_input)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to process image: {str(e)}",
            "visual_score": 0,
            "violations": []
        }

    violations = []
    approved_rgbs = [hex_to_rgb(c) for c in approved_palette if c]
    
    # 1. Palette check: Check each dominant color against the approved palette
    # Neutral colors (pure black, pure white, very dark/light grays) are generally allowed
    off_palette_count = 0
    color_matches = []

    for item in dominant_colors:
        rgb = item["rgb"]
        hex_val = item["hex"]
        pct = item["percentage"]

        # Check if neutral (low saturation)
        max_c, min_c = max(rgb), min(rgb)
        is_neutral = (max_c - min_c) < 25 or max_c < 30 or min_c > 230

        if is_neutral:
            color_matches.append({
                "hex": hex_val,
                "percentage": pct,
                "status": "Neutral (Allowed)",
                "closest_brand_color": None
            })
            continue

        # Find closest approved brand color
        closest_dist = float("inf")
        closest_hex = approved_palette[0] if approved_palette else "#8955D9"

        for approved_hex in approved_palette:
            app_rgb = hex_to_rgb(approved_hex)
            dist = color_distance(rgb, app_rgb)
            if dist < closest_dist:
                closest_dist = dist
                closest_hex = approved_hex

        # Threshold: if distance > 140, it is considered significantly off-brand
        if closest_dist > 140 and pct >= 10.0:
            off_palette_count += 1
            violations.append({
                "category": "Visual & Colors",
                "severity": "High" if pct > 25.0 else "Medium",
                "issue": f"Dominant color {hex_val} ({pct}% of image) does not align with approved brand palette.",
                "suggestion": f"Replace with nearest approved brand shade {closest_hex} or adjust tint/saturation."
            })
            color_matches.append({
                "hex": hex_val,
                "percentage": pct,
                "status": "Off-Brand Deviation",
                "closest_brand_color": closest_hex
            })
        else:
            color_matches.append({
                "hex": hex_val,
                "percentage": pct,
                "status": "Brand Aligned",
                "closest_brand_color": closest_hex
            })

    # 2. Resolution and sizing verification
    width, height = dimensions
    if width < 300 or height < 300:
        violations.append({
            "category": "Visual & Quality",
            "severity": "Medium",
            "issue": f"Image resolution ({width}x{height}px) is below the recommended 300x300px minimum for crisp rendering.",
            "suggestion": "Export asset at a higher resolution to prevent pixelation across displays."
        })

    # Calculate visual compliance score
    base_score = 100
    for v in violations:
        if v["severity"] == "High":
            base_score -= 25
        elif v["severity"] == "Medium":
            base_score -= 15
        else:
            base_score -= 5

    visual_score = max(20, min(100, base_score))

    return {
        "success": True,
        "visual_score": visual_score,
        "dimensions": f"{width}x{height}px",
        "dominant_colors": dominant_colors,
        "color_matches": color_matches,
        "violations": violations
    }
