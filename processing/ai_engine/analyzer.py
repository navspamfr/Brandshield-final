import json
import os
from pathlib import Path
from backend.database.db import get_setting, get_organization_by_id
from processing.ai_engine.vector_store import retrieve_relevant_rules
from processing.compliance.rules_engine import analyze_marketing_copy, generate_diff_html
from processing.image_analysis.visual_verifier import verify_visual_compliance

def run_compliance_audit(org_id, content_text=None, image_file=None, target_channel="General Marketing", user_prompt=None):
    """
    Unified AI Compliance Audit:
      1. AI-Powered Rule Retrieval: Fetches top relevant rules from vector database.
      2. Marketing Copy Analysis: Tests copy for brand naming, forbidden claims, tone of voice, etc.
      3. Visual Verification: Tests uploaded image for palette deviation, dimensions, quality.
      4. AI LLM (OpenAI) Integration: If API key is available, uses LLM for deep nuance & suggested rewrite.
      5. Generates overall score, violation breakdown, and diff.
    """
    org = get_organization_by_id(org_id)
    if not org:
        raise ValueError(f"Organization ID #{org_id} not found.")

    # 1. AI-Powered Rule Retrieval from Vector Database (Requirement 15)
    query_str = (content_text or "") + " " + (target_channel or "")
    api_key = get_setting("openai_api_key") or os.getenv("OPENAI_API_KEY")

    retrieved_rules = retrieve_relevant_rules(org_id, query_str, top_k=5, api_key=api_key)

    # 2. Text / Copy Analysis
    text_result = None
    if content_text and content_text.strip():
        text_result = analyze_marketing_copy(content_text, org, retrieved_rules)

    # 3. Visual / Image Analysis
    image_result = None
    if image_file is not None:
        approved_palette = [
            org.get("primary_color", "#8955D9"),
            org.get("secondary_color", "#D0B7FF"),
            org.get("accent_color", "#100C18")
        ]
        image_result = verify_visual_compliance(image_file, approved_palette)

    # 4. Optional OpenAI Deep Analysis if key is available
    use_openai = bool(api_key) and bool(content_text and content_text.strip())
    if use_openai:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            rules_context = "\n".join([
                f"- [{r.get('category')}] {r.get('rule_title')}: {r.get('rule_description')} (Severity: {r.get('severity')})"
                for r in retrieved_rules
            ])

            system_prompt = f"""You are BrandShield's AI Brand Compliance Guardian.
Analyze the following marketing copy strictly against the brand guidelines for '{org.get('name')}'.

Brand Voice & Tone: {org.get('tone_of_voice')}
Target Channel: {target_channel}
Industry: {org.get('industry')}

Relevant Brand Rules:
{rules_context}

Analyze the copy and respond ONLY in valid JSON matching this structure:
{{
  "compliance_score": <integer 0-100>,
  "tone_score": <integer 0-100>,
  "vocab_score": <integer 0-100>,
  "legal_score": <integer 0-100>,
  "status": "<Passed | Warning | Failed>",
  "summary": "<2-sentence executive summary of compliance status>",
  "corrected_content": "<complete rewritten copy fully aligned with brand guidelines>",
  "violations": [
    {{
      "category": "<Category>",
      "severity": "<High | Medium | Low>",
      "issue": "<Clear description of violation>",
      "suggestion": "<Actionable recommendation>",
      "snippet": "<The offending text snippet>"
    }}
  ]
}}"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Marketing Copy to Analyze:\n\n{content_text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )

            llm_result = json.loads(response.choices[0].message.content)
            # Merge / replace text_result with high-fidelity LLM response
            text_result = llm_result

        except Exception as e:
            # Fall back gracefully to heuristic text_result
            if text_result:
                text_result["llm_fallback_notice"] = f"OpenAI analysis unavailable ({str(e)}), used local compliance engine."

    # 5. Synthesize Combined Report
    all_violations = []
    overall_score = 100
    sub_scores = {"tone": 100, "vocab": 100, "legal": 100, "visual": 100}

    if text_result:
        all_violations.extend(text_result.get("violations", []))
        sub_scores["tone"] = text_result.get("tone_score", 100)
        sub_scores["vocab"] = text_result.get("vocab_score", 100)
        sub_scores["legal"] = text_result.get("legal_score", 100)

    if image_result and image_result.get("success"):
        all_violations.extend(image_result.get("violations", []))
        sub_scores["visual"] = image_result.get("visual_score", 100)

    # Compute weighted total score
    if text_result and image_result and image_result.get("success"):
        overall_score = int(0.6 * text_result.get("compliance_score", 100) + 0.4 * image_result.get("visual_score", 100))
    elif text_result:
        overall_score = text_result.get("compliance_score", 100)
    elif image_result and image_result.get("success"):
        overall_score = image_result.get("visual_score", 100)

    # Determine status
    if overall_score >= 90:
        status = "Passed"
    elif overall_score >= 70:
        status = "Warning"
    else:
        status = "Failed"

    corrected_content = text_result.get("corrected_content", content_text or "") if text_result else ""
    diff_html = generate_diff_html(content_text or "", corrected_content) if (content_text and corrected_content) else ""

    summary = (
        text_result.get("summary")
        if text_result and text_result.get("summary")
        else f"Compliance audit finished with a score of {overall_score}%. {len(all_violations)} issue(s) identified."
    )

    full_report = {
        "overall_score": overall_score,
        "status": status,
        "sub_scores": sub_scores,
        "summary": summary,
        "retrieved_rules": retrieved_rules,
        "violations": all_violations,
        "text_analysis": text_result,
        "visual_analysis": image_result,
        "original_content": content_text or "",
        "corrected_content": corrected_content,
        "diff_html": diff_html,
        "channel": target_channel,
        "brand_name": org.get("name")
    }

    return full_report
