import re
import math
import numpy as np
from PIL import Image
import base64
import io

def calculate_readability(text):
    """
    Computes Flesch Reading Ease and approximate Grade Level.
    Flesch Reading Ease:
      90-100: Very Easy (5th grade)
      60-70: Plain English (8th-9th grade) - Ideal for B2B/B2C marketing
      30-50: Difficult (College level)
      0-30: Very Confusing (Academic/Legal)
    """
    words = re.findall(r'\b[a-zA-Z]+\b', text)
    sentences = re.split(r'[\.\?!]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    num_words = max(1, len(words))
    num_sentences = max(1, len(sentences))

    # Approximate syllable count by vowel clusters
    def count_syllables(word):
        w = word.lower()
        count = len(re.findall(r'[aeiouy]+', w))
        if w.endswith('e') and not w.endswith('le') and len(w) > 2:
            count = max(1, count - 1)
        return max(1, count)

    total_syllables = sum(count_syllables(w) for w in words)

    asl = num_words / num_sentences  # Average Sentence Length
    asw = total_syllables / num_words  # Average Syllables per Word

    # Flesch Reading Ease formula
    fre = 206.835 - (1.015 * asl) - (84.6 * asw)
    fre_score = max(0, min(100, round(fre, 1)))

    if fre_score >= 80:
        ease_label = "Very Easy to Read (Mass Consumer)"
    elif fre_score >= 60:
        ease_label = "Optimal Readability (Standard Marketing)"
    elif fre_score >= 40:
        ease_label = "Moderately Complex (Technical / B2B)"
    else:
        ease_label = "Dense & Overly Complex (May Alienate Audience)"

    # Flesch-Kincaid Grade Level
    fkgl = (0.39 * asl) + (11.8 * asw) - 15.59
    grade_level = max(1, round(fkgl, 1))

    return {
        "score": fre_score,
        "label": ease_label,
        "grade_level": grade_level,
        "word_count": num_words,
        "sentence_count": num_sentences,
        "avg_words_per_sentence": round(asl, 1)
    }

def calculate_wcag_contrast(rgb1, rgb2):
    """
    Calculates WCAG 2.1 relative luminance and contrast ratio between two RGB colors.
    Returns contrast ratio (e.g. 4.8) and compliance tags.
    """
    def relative_luminance(rgb):
        srgb = [c / 255.0 for c in rgb]
        linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    l1 = relative_luminance(rgb1)
    l2 = relative_luminance(rgb2)

    lum_light = max(l1, l2)
    lum_dark = min(l1, l2)

    ratio = (lum_light + 0.05) / (lum_dark + 0.05)
    ratio_val = round(ratio, 2)

    # WCAG 2.1 thresholds
    aa_normal = ratio_val >= 4.5
    aa_large = ratio_val >= 3.0
    aaa_normal = ratio_val >= 7.0

    return {
        "contrast_ratio": f"{ratio_val}:1",
        "ratio_numeric": ratio_val,
        "wcag_aa_compliant": aa_normal,
        "wcag_large_text_compliant": aa_large,
        "wcag_aaa_compliant": aaa_normal
    }

def analyze_visual_composition_and_contrast(image_input, approved_palette):
    """
    Performs deep visual contrast and composition analysis on an image.
    """
    from processing.image_analysis.visual_verifier import extract_dominant_colors, hex_to_rgb, color_distance

    try:
        dominant_colors, (width, height) = extract_dominant_colors(image_input, max_colors=6)
    except Exception as e:
        return {"error": str(e)}

    # Contrast between two highest frequency colors (typically foreground & background)
    contrast_analysis = None
    if len(dominant_colors) >= 2:
        c1 = dominant_colors[0]["rgb"]
        c2 = dominant_colors[1]["rgb"]
        contrast_analysis = calculate_wcag_contrast(c1, c2)
        contrast_analysis["dominant_primary_hex"] = dominant_colors[0]["hex"]
        contrast_analysis["dominant_secondary_hex"] = dominant_colors[1]["hex"]

    # Aspect ratio detection & channel recommendation
    aspect_ratio = round(width / max(1, height), 2)
    aspect_recommendation = "Custom"
    if 0.95 <= aspect_ratio <= 1.05:
        aspect_recommendation = "1:1 Square (Instagram Feed, Product Catalog, Profile Avatars)"
    elif 1.70 <= aspect_ratio <= 1.85:
        aspect_recommendation = "16:9 Landscape (YouTube Thumbnail, X/Twitter Header, LinkedIn Banner)"
    elif 0.50 <= aspect_ratio <= 0.60:
        aspect_recommendation = "9:16 Portrait (Instagram Stories, TikTok, Mobile Reels)"
    elif 1.25 <= aspect_ratio <= 1.40:
        aspect_recommendation = "4:3 Standard Display"
    elif 0.75 <= aspect_ratio <= 0.85:
        aspect_recommendation = "4:5 Portrait Feed (High-Engagement Instagram/Pinterest Post)"

    return {
        "dimensions": f"{width}x{height}px",
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio,
        "recommended_channel_fit": aspect_recommendation,
        "dominant_colors": dominant_colors,
        "wcag_contrast": contrast_analysis
    }

def perform_deep_compliance_audit(content_text, brand_info, relevant_rules=None, image_file=None, target_channel="General Marketing", api_key=None):
    """
    Orchestrates the enhanced multi-dimensional compliance audit:
      1. Text readability & linguistic complexity
      2. Regulatory, legal, trademark, & claim auditing
      3. Tone, formality, and emotional polarity
      4. Visual composition, WCAG contrast & palette deviation
      5. OpenAI Vision OCR & layout analysis (if API key provided)
      6. Sentence-by-sentence rewrites with interactive replacement tokens
    """
    from processing.compliance.rules_engine import analyze_marketing_copy, generate_diff_html
    from processing.image_analysis.visual_verifier import verify_visual_compliance

    # 1. Base copy audit
    base_result = analyze_marketing_copy(content_text or "", brand_info, relevant_rules)

    # 2. Readability metrics
    readability = calculate_readability(content_text or "") if content_text else None

    # Check readability against brand audience
    if readability and readability["grade_level"] > 14 and "mass" in brand_info.get("target_audience", "").lower():
        base_result["violations"].append({
            "category": "Readability & Accessibility",
            "severity": "Medium",
            "issue": f"Text grade level ({readability['grade_level']}) is excessively academic for target audience.",
            "suggestion": f"Simplify sentence structure to reach an 8th-10th grade reading level for maximum consumer engagement."
        })

    # 3. Visual & WCAG accessibility audit
    visual_result = None
    composition_result = None

    if image_file is not None:
        approved_palette = [
            brand_info.get("primary_color", "#8955D9"),
            brand_info.get("secondary_color", "#D0B7FF"),
            brand_info.get("accent_color", "#100C18")
        ]
        visual_result = verify_visual_compliance(image_file, approved_palette)
        composition_result = analyze_visual_composition_and_contrast(image_file, approved_palette)

        # WCAG accessibility violation check
        if composition_result and composition_result.get("wcag_contrast"):
            contrast_info = composition_result["wcag_contrast"]
            if not contrast_info["wcag_aa_compliant"]:
                base_result["violations"].append({
                    "category": "Visual & Accessibility (WCAG)",
                    "severity": "Medium",
                    "issue": f"Dominant foreground/background contrast ({contrast_info['contrast_ratio']}) fails WCAG 2.1 AA requirement (minimum 4.5:1).",
                    "suggestion": f"Increase lightness contrast between dominant surfaces ({contrast_info['dominant_primary_hex']} and {contrast_info['dominant_secondary_hex']}) for legibility."
                })

    # 4. Optional OpenAI Vision & Advanced LLM Reasoning
    if api_key and (content_text or image_file):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            rules_summary = "\n".join([
                f"- [{r.get('category')}] {r.get('rule_title')}: {r.get('rule_description')}"
                for r in (relevant_rules or [])
            ])

            user_prompt = f"""Brand Profile: {brand_info.get('name')}
Industry: {brand_info.get('industry')}
Brand Voice: {brand_info.get('tone_of_voice')}
Target Channel: {target_channel}

Active Brand Rules:
{rules_summary}

Content To Review:
{content_text or '[Visual Only Asset]'}
"""

            messages = [
                {
                    "role": "system",
                    "content": """You are BrandShield's Chief Brand Compliance Officer.
Analyze the provided content and return a strict JSON response matching:
{
  "compliance_score": <int 0-100>,
  "tone_score": <int 0-100>,
  "vocab_score": <int 0-100>,
  "legal_score": <int 0-100>,
  "status": "<Passed|Warning|Failed>",
  "summary": "<2-sentence executive summary>",
  "corrected_content": "<rewritten copy fully aligned with brand rules>",
  "sentence_explanations": [
    {"original_sentence": "<original>", "revised_sentence": "<revised>", "reason": "<why changed>"}
  ],
  "violations": [
    {"category": "<Category>", "severity": "<High|Medium|Low>", "issue": "<Description>", "suggestion": "<Fix>", "snippet": "<snippet>"}
  ]
}"""
                }
            ]

            # If image provided, add to OpenAI vision message
            if image_file:
                b64_img = base64.b64encode(image_file).decode("utf-8")
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt + "\nAlso inspect the uploaded visual asset for logo placement, OCR text inside image, and brand styling."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]
                })
            else:
                messages.append({"role": "user", "content": user_prompt})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.2
            )

            import json
            llm_data = json.loads(response.choices[0].message.content)
            base_result = llm_data

        except Exception as e:
            base_result["llm_note"] = f"Local heuristics applied ({str(e)})."

    # Recalculate combined score
    all_violations = base_result.get("violations", [])
    overall_score = base_result.get("compliance_score", 100)
    if visual_result and visual_result.get("success"):
        all_violations.extend(visual_result.get("violations", []))
        if content_text:
            overall_score = int(0.6 * base_result.get("compliance_score", 100) + 0.4 * visual_result.get("visual_score", 100))
        else:
            overall_score = visual_result.get("visual_score", 100)

    # Determine status
    if overall_score >= 90:
        status = "Passed"
    elif overall_score >= 70:
        status = "Warning"
    else:
        status = "Failed"

    corrected_text = base_result.get("corrected_content", content_text or "")
    diff_html = generate_diff_html(content_text or "", corrected_text) if (content_text and corrected_text) else ""

    return {
        "overall_score": overall_score,
        "status": status,
        "sub_scores": {
            "tone": base_result.get("tone_score", 95),
            "vocab": base_result.get("vocab_score", 90),
            "legal": base_result.get("legal_score", 90),
            "visual": visual_result.get("visual_score", 100) if visual_result else 100,
            "readability": readability.get("score", 85) if readability else 100
        },
        "summary": base_result.get("summary", f"Compliance audit finished with a score of {overall_score}%."),
        "violations": all_violations,
        "readability": readability,
        "visual_analysis": visual_result,
        "composition_analysis": composition_result,
        "original_content": content_text or "",
        "corrected_content": corrected_text,
        "diff_html": diff_html,
        "sentence_explanations": base_result.get("sentence_explanations", []),
        "retrieved_rules": relevant_rules or [],
        "channel": target_channel,
        "brand_name": brand_info.get("name")
    }
