import json
from datetime import datetime

def generate_html_audit_report(report_data, brand_info):
    """
    Generates a standalone, beautifully styled executive brand compliance
    report and certificate in HTML format, ready to view or print to PDF.
    """
    brand_name = brand_info.get("name", "BrandShield")
    score = report_data.get("overall_score", 100)
    status = report_data.get("status", "Passed")
    channel = report_data.get("channel", "General Marketing")
    created_at = datetime.now().strftime("%d %B %Y, %H:%M UTC")

    status_color = "#34d399" if score >= 90 else ("#fbbf24" if score >= 70 else "#f87171")
    violations = report_data.get("violations", [])
    sub_scores = report_data.get("sub_scores", {})
    readability = report_data.get("readability") or {}

    violations_html = ""
    if not violations:
        violations_html = "<div style='color: #34d399; font-weight: 600; padding: 12px; background: rgba(52, 211, 153, 0.1); border-radius: 8px;'>Zero violations detected. Asset is fully compliant.</div>"
    else:
        for idx, v in enumerate(violations):
            sev = v.get("severity", "Medium")
            sev_bg = "rgba(239, 68, 68, 0.2)" if sev == "High" else ("rgba(245, 158, 11, 0.2)" if sev == "Medium" else "rgba(59, 130, 246, 0.2)")
            sev_color = "#f87171" if sev == "High" else ("#fbbf24" if sev == "Medium" else "#93c5fd")
            violations_html += f"""
            <div style="background: #191428; border: 1px solid #2b2140; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <strong style="color: #ede5f8;">{v.get('category')}</strong>
                    <span style="background: {sev_bg}; color: {sev_color}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700;">{sev} SEVERITY</span>
                </div>
                <div style="color: #fca5a5; font-size: 13px; margin-bottom: 4px;"><strong>Issue:</strong> {v.get('issue')}</div>
                <div style="color: #86efac; font-size: 13px;"><strong>Recommendation:</strong> {v.get('suggestion')}</div>
            </div>
            """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>BrandShield Audit Certificate — {brand_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #0f0b18;
            color: #f5efff;
            margin: 0;
            padding: 40px;
        }}
        .report-box {{
            max-width: 850px;
            margin: 0 auto;
            background: #161024;
            border: 1px solid #352650;
            border-radius: 16px;
            padding: 36px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }}
        .badge {{
            display: inline-block;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
            background: {status_color}22;
            color: {status_color};
            border: 1px solid {status_color}55;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin: 24px 0;
        }}
        .metric-card {{
            background: #1c152d;
            border: 1px solid #2e2348;
            border-radius: 10px;
            padding: 14px;
            text-align: center;
        }}
        .metric-val {{
            font-size: 24px;
            font-weight: 800;
            color: #a78bfa;
            margin-top: 4px;
        }}
        .metric-lbl {{
            font-size: 11px;
            color: #9f91b7;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .section-title {{
            font-size: 12px;
            letter-spacing: 1.5px;
            font-weight: 700;
            color: #a78bfa;
            margin: 28px 0 12px;
            text-transform: uppercase;
        }}
        .content-box {{
            background: #110c1c;
            border: 1px solid #241938;
            border-radius: 8px;
            padding: 14px;
            font-size: 13px;
            line-height: 1.6;
            color: #d8cde9;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <div class="report-box">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2d2244; padding-bottom: 20px;">
            <div>
                <div style="font-size: 11px; font-weight: 700; letter-spacing: 2px; color: #a78bfa;">BRANDSHIELD COMPLIANCE CERTIFICATE</div>
                <h1 style="margin: 4px 0 2px; font-size: 26px;">{brand_name}</h1>
                <div style="color: #9c8fb4; font-size: 13px;">Channel: {channel} · Date: {created_at}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 44px; font-weight: 900; color: {status_color};">{score}%</div>
                <span class="badge">{status.upper()}</span>
            </div>
        </div>

        <div class="section-title">Executive Summary</div>
        <div style="color: #cfc2e3; font-size: 14px; line-height: 1.6;">{report_data.get('summary', 'Audit evaluation completed.')}</div>

        <div class="section-title">Compliance Dimension Scores</div>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-lbl">Tone of Voice</div>
                <div class="metric-val">{sub_scores.get('tone', 100)}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-lbl">Vocabulary & Claims</div>
                <div class="metric-val">{sub_scores.get('vocab', 100)}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-lbl">Legal & Disclaimers</div>
                <div class="metric-val">{sub_scores.get('legal', 100)}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-lbl">Visual & Contrast</div>
                <div class="metric-val">{sub_scores.get('visual', 100)}%</div>
            </div>
        </div>

        <div class="section-title">Audited Content & Corrections</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
            <div>
                <div style="font-size: 12px; font-weight: 600; color: #a395bc; margin-bottom: 6px;">Original Content:</div>
                <div class="content-box">{report_data.get('original_content', '')}</div>
            </div>
            <div>
                <div style="font-size: 12px; font-weight: 600; color: #86efac; margin-bottom: 6px;">AI-Corrected Content:</div>
                <div class="content-box">{report_data.get('corrected_content', '')}</div>
            </div>
        </div>

        <div class="section-title">Violation Audit Log ({len(violations)})</div>
        {violations_html}

        <div style="margin-top: 36px; padding-top: 18px; border-top: 1px solid #291e3e; display: flex; justify-content: space-between; font-size: 11px; color: #7f7396;">
            <div>Verified by BrandShield AI Engine</div>
            <div>Document Hash: BS-{hash(str(report_data)) % 1000000:06d}</div>
        </div>
    </div>
</body>
</html>"""
    return html
