import re
import difflib

COMMON_PROHIBITED_CLAIMS = [
    (r"\b100%\s*(guaranteed|hack-proof|safe|secure|free|risk-free)\b", "Absolute guarantee claim cannot be legally verified.", "High", "enterprise-grade assurance"),
    (r"\b(only\s+solution\s+in\s+the\s+world|best\s+in\s+the\s+world|number\s+one\s+always)\b", "Unsubstantiated superlative claim.", "High", "industry-leading solution"),
    (r"\b(wipes\s+out\s+all\s+competitors|destroys?\s+all\s+competitors)\b", "Aggressive comparative advertising violation.", "High", "outperforms legacy solutions"),
    (r"\b(cheat\s+code|hack\s+the\s+system)\b", "Misleading security framing.", "Medium", "advanced capability"),
    (r"\b(miracle|instant\s+cure|overnight\s+success)\b", "Hyperbolic promotional claim.", "High", "proven methodology")
]

INFORMAL_SLANG_WORDS = [
    (r"\b(super\s+cool|insane\s+deal|crazy\s+cheap|dirt\s+cheap)\b", "Overly casual/sensational tone unsuitable for enterprise brand.", "Medium"),
    (r"\b(gonna|wanna|gotta|kinda|dunno|imho|tbh|y'all)\b", "Colloquial contraction violates professional brand voice.", "Low"),
    (r"\b(dude|bro|guys|peeps)\b", "Excessively informal audience address.", "Medium")
]

def analyze_marketing_copy(text, brand_info, relevant_rules=None):
    """
    Performs comprehensive rule-based compliance checking on marketing copy.
    """
    if not text or not text.strip():
        return {
            "compliance_score": 100,
            "tone_score": 100,
            "vocab_score": 100,
            "legal_score": 100,
            "status": "Passed",
            "violations": [],
            "suggestions": [],
            "corrected_content": text,
            "summary": "No content provided for analysis."
        }

    violations = []
    seen_violations = set()
    brand_full_name = brand_info.get("name", "BrandShield")
    # Also extract root brand name (e.g. 'BrandShield' from 'BrandShield AI')
    brand_core_name = brand_full_name.split()[0] if brand_full_name else "BrandShield"
    corrected_text = text

    # 1. Check Brand Name Casing & Spelling for both full and core name
    for b_name in list(set([brand_full_name, brand_core_name])):
        if len(b_name) < 3:
            continue
        pattern = r'\b' + re.escape(b_name) + r'\b'
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            found_casing = m.group(0)
            if found_casing != b_name:
                key = f"casing_{found_casing}_{b_name}"
                if key not in seen_violations:
                    seen_violations.add(key)
                    violations.append({
                        "category": "Brand Naming",
                        "severity": "High",
                        "issue": f"Incorrect brand casing '{found_casing}'. Canonical spelling is '{b_name}'.",
                        "suggestion": f"Always write as '{b_name}'.",
                        "snippet": found_casing
                    })
                corrected_text = re.sub(r'\b' + re.escape(found_casing) + r'\b', b_name, corrected_text)

    # 2. Check Common Prohibited Marketing Claims
    for pattern, explanation, severity, replacement in COMMON_PROHIBITED_CLAIMS:
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
        for m in matches:
            matched_str = m.group(0)
            key = f"claim_{matched_str.lower()}"
            if key not in seen_violations:
                seen_violations.add(key)
                violations.append({
                    "category": "Prohibited Claims",
                    "severity": severity,
                    "issue": f"Prohibited claim: '{matched_str}'. {explanation}",
                    "suggestion": f"Reframe to: '{replacement}'.",
                    "snippet": matched_str
                })
        corrected_text = re.sub(pattern, replacement, corrected_text, flags=re.IGNORECASE)

    # 3. Check Informal Slang & Tone
    tone_of_voice = brand_info.get("tone_of_voice", "").lower()
    is_formal_brand = any(t in tone_of_voice for t in ["professional", "authoritative", "precise", "corporate", "executive"])

    if is_formal_brand:
        for pattern, explanation, severity in INFORMAL_SLANG_WORDS:
            matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
            for m in matches:
                matched_str = m.group(0)
                key = f"slang_{matched_str.lower()}"
                if key not in seen_violations:
                    seen_violations.add(key)
                    violations.append({
                        "category": "Tone & Voice",
                        "severity": severity,
                        "issue": f"Informal slang detected: '{matched_str}'. {explanation}",
                        "suggestion": "Replace with precise, executive-ready terminology.",
                        "snippet": matched_str
                    })
        corrected_text = re.sub(r'\bsuper\s+cool\b', 'next-generation', corrected_text, flags=re.IGNORECASE)
        corrected_text = re.sub(r'\binsane\s+deal\b', 'exclusive offering', corrected_text, flags=re.IGNORECASE)
        corrected_text = re.sub(r'\bgonna\b', 'going to', corrected_text, flags=re.IGNORECASE)
        corrected_text = re.sub(r'\bwanna\b', 'want to', corrected_text, flags=re.IGNORECASE)

    # 4. Check Excessive Punctuation / Capitalization
    if re.search(r'[!?]{2,}', text):
        snippet = re.search(r'[!?]{2,}', text).group(0)
        violations.append({
            "category": "Tone & Voice",
            "severity": "Medium",
            "issue": f"Excessive sensational punctuation '{snippet}' detected.",
            "suggestion": "Limit punctuation to single marks to maintain an authoritative brand tone.",
            "snippet": snippet
        })
        corrected_text = re.sub(r'[!]{2,}', '!', corrected_text)
        corrected_text = re.sub(r'[?]{2,}', '?', corrected_text)

    # Check for shouting (all caps words >= 4 letters)
    all_caps_words = [w for w in text.split() if w.isupper() and len(w) > 4 and w not in ["BRANDSHIELD", "GDPR", "HIPAA", "SOC2", "SaaS", "AI"]]
    if len(all_caps_words) >= 2:
        violations.append({
            "category": "Tone & Voice",
            "severity": "Low",
            "issue": f"Aggressive uppercase shouting detected: {', '.join(all_caps_words[:3])}.",
            "suggestion": "Use standard Sentence or Title Case.",
            "snippet": " ".join(all_caps_words[:2])
        })
        for w in all_caps_words:
            corrected_text = corrected_text.replace(w, w.capitalize())

    # 5. Evaluate against Specific Retrieved Brand Rules
    if relevant_rules:
        for r in relevant_rules:
            cat = r.get("category", "")
            title = r.get("rule_title", "")
            desc = r.get("rule_description", "")
            
            # Look for prohibited terms enclosed in quotes or explicitly marked "never write"
            if any(term in desc.lower() for term in ["never", "prohibited", "forbidden", "do not"]):
                quoted_terms = re.findall(r"['\"]([^'\"]+)['\"]", desc)
                for q in quoted_terms:
                    # If this is a prohibited spelling/casing rule, check exact presence
                    if q in text and q != brand_full_name and q != brand_core_name:
                        key = f"rule_{r.get('id')}_{q}"
                        if key not in seen_violations:
                            seen_violations.add(key)
                            violations.append({
                                "category": cat,
                                "severity": r.get("severity", "medium").capitalize(),
                                "issue": f"Violates rule '{title}': found prohibited term '{q}'.",
                                "suggestion": f"Guideline: {desc}",
                                "snippet": q
                            })

    # 6. Scoring Calculations
    high_count = sum(1 for v in violations if v["severity"] == "High")
    med_count = sum(1 for v in violations if v["severity"] == "Medium")
    low_count = sum(1 for v in violations if v["severity"] == "Low")

    penalty = (high_count * 18) + (med_count * 8) + (low_count * 3)
    overall_score = max(20, min(100, 100 - penalty))

    tone_score = max(30, 100 - (sum(1 for v in violations if v["category"] == "Tone & Voice") * 15))
    vocab_score = max(30, 100 - (sum(1 for v in violations if v["category"] in ["Brand Naming", "Prohibited Claims"]) * 18))
    legal_score = max(40, 100 - (sum(1 for v in violations if v["category"] == "Legal & Disclaimers") * 20))

    if overall_score >= 90:
        status = "Passed"
    elif overall_score >= 70:
        status = "Warning"
    else:
        status = "Failed"

    summary_text = (
        "Content passes all brand compliance checks with high adherence."
        if not violations else
        f"Found {len(violations)} brand guideline violation{'s' if len(violations) > 1 else ''} ({high_count} high, {med_count} medium, {low_count} low severity)."
    )

    return {
        "compliance_score": overall_score,
        "tone_score": tone_score,
        "vocab_score": vocab_score,
        "legal_score": legal_score,
        "status": status,
        "violations": violations,
        "corrected_content": corrected_text,
        "summary": summary_text
    }

def generate_diff_html(original, corrected):
    """
    Produces inline HTML diff showing additions in purple/green
    and removals in struck-through red.
    """
    if original.strip() == corrected.strip():
        return f"<div class='diff-container'><span class='diff-unchanged'>{original}</span></div>"

    words1 = original.split()
    words2 = corrected.split()
    matcher = difflib.SequenceMatcher(None, words1, words2)
    output = []

    for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
        if opcode == 'equal':
            output.append(" ".join(words1[a0:a1]))
        elif opcode == 'insert':
            output.append(f"<span class='diff-ins'>{' '.join(words2[b0:b1])}</span>")
        elif opcode == 'delete':
            output.append(f"<span class='diff-del'>{' '.join(words1[a0:a1])}</span>")
        elif opcode == 'replace':
            output.append(f"<span class='diff-del'>{' '.join(words1[a0:a1])}</span> <span class='diff-ins'>{' '.join(words2[b0:b1])}</span>")

    return " ".join(output)
