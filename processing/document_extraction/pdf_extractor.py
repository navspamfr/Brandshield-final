import pymupdf
import re
from pathlib import Path

def extract_text_from_pdf(pdf_bytes_or_path):
    """
    Extracts text and structured sections from a PDF file using PyMuPDF.
    Accepts either file path (str/Path) or bytes.
    """
    doc = None
    try:
        if isinstance(pdf_bytes_or_path, (str, Path)):
            doc = pymupdf.open(pdf_bytes_or_path)
        else:
            doc = pymupdf.open(stream=pdf_bytes_or_path, filetype="pdf")

        full_text = []
        page_details = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            full_text.append(text)
            page_details.append({
                "page": page_num + 1,
                "text_length": len(text),
                "text_preview": text[:200].strip()
            })

        combined_text = "\n\n".join(full_text)
        extracted_rules = auto_extract_rules_from_text(combined_text)

        return {
            "success": True,
            "page_count": len(doc),
            "full_text": combined_text,
            "page_details": page_details,
            "suggested_rules": extracted_rules
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "full_text": "",
            "page_count": 0,
            "suggested_rules": []
        }
    finally:
        if doc:
            doc.close()

def auto_extract_rules_from_text(text):
    """
    Parses guidelines text to find candidate rules, colors, and tone guidelines.
    """
    suggested_rules = []

    # 1. Look for Hex color codes (e.g. #8955D9, #FFFFFF)
    hex_colors = list(set(re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}\b', text)))
    if hex_colors:
        suggested_rules.append({
            "category": "Visual & Colors",
            "rule_title": "Approved Brand Color Palette",
            "rule_description": f"The document references the following brand colors: {', '.join(hex_colors)}. Content must adhere to this palette.",
            "severity": "medium"
        })

    # 2. Look for bullet points or numbered rules containing keywords
    keywords = ["must", "never", "always", "prohibited", "do not", "forbidden", "tone", "voice", "logo", "disclaimer", "trademark"]
    lines = text.split("\n")
    rule_id = 1

    for line in lines:
        cleaned = line.strip(" •-*#1234567890.\t")
        if len(cleaned) > 25 and any(kw in cleaned.lower() for kw in keywords):
            # Categorize rule
            category = "General Guidelines"
            severity = "medium"
            lowered = cleaned.lower()

            if "color" in lowered or "palette" in lowered or "visual" in lowered:
                category = "Visual & Colors"
            elif "logo" in lowered or "icon" in lowered:
                category = "Visual & Colors"
                severity = "high"
            elif "tone" in lowered or "voice" in lowered or "style" in lowered:
                category = "Tone & Voice"
            elif "prohibited" in lowered or "never" in lowered or "forbidden" in lowered:
                category = "Prohibited Claims"
                severity = "high"
            elif "disclaimer" in lowered or "trademark" in lowered or "legal" in lowered or "copyright" in lowered:
                category = "Legal & Disclaimers"
                severity = "high"

            suggested_rules.append({
                "category": category,
                "rule_title": f"Guideline Rule: {cleaned[:40]}...",
                "rule_description": cleaned,
                "severity": severity
            })

            if len(suggested_rules) >= 10:
                break

    return suggested_rules
