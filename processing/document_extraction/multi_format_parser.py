import os
import json
import io
import csv
import re
from pathlib import Path
from PIL import Image
import pymupdf

def parse_uploaded_file(file_name, file_bytes):
    """
    Parses multiple file types (PDF, Images, TXT, MD, CSV, JSON)
    into a standardized asset representation for deep compliance analysis.
    """
    ext = Path(file_name).suffix.lower()
    asset = {
        "file_name": file_name,
        "extension": ext,
        "file_size_kb": round(len(file_bytes) / 1024, 1),
        "text_content": "",
        "images": [],
        "metadata": {},
        "file_type": "unknown"
    }

    try:
        # 1. PDF Documents
        if ext == ".pdf":
            asset["file_type"] = "document_pdf"
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            page_texts = []
            extracted_images = []

            for p_idx in range(len(doc)):
                page = doc[p_idx]
                text = page.get_text("text")
                if text.strip():
                    page_texts.append(f"--- Page {p_idx + 1} ---\n{text}")

                # Extract embedded images from PDF pages (up to 3 images)
                image_list = page.get_images(full=True)
                for img_info in image_list[:2]:
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)
                    img_bytes = base_image["image"]
                    img_ext = base_image["ext"]
                    try:
                        pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                        extracted_images.append({
                            "name": f"Page_{p_idx+1}_img_{xref}.{img_ext}",
                            "pil_image": pil_img,
                            "bytes": img_bytes,
                            "dimensions": pil_img.size
                        })
                    except Exception:
                        pass

            asset["text_content"] = "\n\n".join(page_texts)
            asset["images"] = extracted_images
            asset["metadata"] = {
                "page_count": len(doc),
                "extracted_images_count": len(extracted_images)
            }
            doc.close()

        # 2. Image Files (PNG, JPG, JPEG, WEBP)
        elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
            asset["file_type"] = "image_asset"
            pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            asset["images"] = [{
                "name": file_name,
                "pil_image": pil_img,
                "bytes": file_bytes,
                "dimensions": pil_img.size
            }]
            asset["metadata"] = {
                "width": pil_img.width,
                "height": pil_img.height,
                "aspect_ratio": round(pil_img.width / max(1, pil_img.height), 2)
            }

        # 3. Plain Text and Markdown
        elif ext in [".txt", ".md", ".markdown"]:
            asset["file_type"] = "text_document"
            text_str = file_bytes.decode("utf-8", errors="ignore")
            asset["text_content"] = text_str
            asset["metadata"] = {
                "word_count": len(text_str.split()),
                "line_count": len(text_str.splitlines())
            }

        # 4. CSV Spreadsheets (e.g. ad variants, social media calendar)
        elif ext == ".csv":
            asset["file_type"] = "csv_campaign"
            text_str = file_bytes.decode("utf-8", errors="ignore")
            reader = csv.reader(io.StringIO(text_str))
            rows = list(reader)
            extracted_lines = []
            for r_idx, row in enumerate(rows):
                if row:
                    extracted_lines.append(f"Row {r_idx + 1}: " + " | ".join(row))
            asset["text_content"] = "\n".join(extracted_lines)
            asset["metadata"] = {
                "row_count": len(rows),
                "column_count": len(rows[0]) if rows else 0
            }

        # 5. JSON Campaign Files
        elif ext == ".json":
            asset["file_type"] = "json_data"
            text_str = file_bytes.decode("utf-8", errors="ignore")
            data = json.loads(text_str)
            # Flatten or format json into readable text for analysis
            asset["text_content"] = json.dumps(data, indent=2)
            asset["metadata"] = {"json_type": type(data).__name__}

    except Exception as e:
        asset["error"] = f"Parsing error: {str(e)}"

    return asset
