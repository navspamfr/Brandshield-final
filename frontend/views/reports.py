import streamlit as st
import json
import pandas as pd
from datetime import datetime
from backend.database.db import (
    get_organizations,
    get_analyses,
    get_recurring_violations,
    get_organization_by_id
)
from processing.compliance.report_generator import generate_html_audit_report
from components.header import render_view_header

def show_reports():
    render_view_header(
        "EXECUTIVE INTELLIGENCE",
        "Compliance Reports & Certificates",
        "Generate official compliance certificates, review recurring brand risk patterns, and export audit portfolios."
    )

    organizations = get_organizations()
    if not organizations:
        st.warning("No brand profiles configured yet.")
        return

    active_org_id = st.session_state.get("active_org_id", organizations[0]["id"])
    active_org = get_organization_by_id(active_org_id) or organizations[0]

    rep_tab1, rep_tab2, rep_tab3 = st.tabs([
        "📜 Official Audit Certificates",
        "⚠️ Recurring Risk Analysis",
        "📈 Compliance Improvement Trends"
    ])

    # ========================================================
    # TAB 1: OFFICIAL AUDIT CERTIFICATES
    # ========================================================
    with rep_tab1:
        st.markdown('<div class="bs-section-label">GENERATE & DOWNLOAD OFFICIAL COMPLIANCE CERTIFICATES</div>', unsafe_allow_html=True)
        st.caption("Official BrandShield compliance certificates ready for print-to-PDF, stakeholder review, or legal sign-off.")

        analyses = get_analyses(active_org_id, limit=30)
        if not analyses:
            st.info("No audit records found for this brand yet. Run an audit in Content Analysis first.")
        else:
            audit_choices = {a["id"]: f"[{a['compliance_score']}%] {a['title']} ({a.get('created_at','')[:10]})" for a in analyses}
            selected_audit_id = st.selectbox(
                "Select Audit to Generate Certificate",
                options=list(audit_choices.keys()),
                format_func=lambda x: audit_choices[x],
                key="rep_audit_selector"
            )

            chosen_audit = next(a for a in analyses if a["id"] == selected_audit_id)
            score = chosen_audit["compliance_score"]
            status = chosen_audit["status"]
            status_color = "#10B981" if score >= 90 else ("#F59E0B" if score >= 70 else "#EF4444")

            # Certificate summary card
            st.markdown(
                f"""
                <div style="background: rgba(22, 15, 38, 0.85); border: 1px solid rgba(167, 139, 250, 0.25); border-radius: 14px; padding: 24px; margin: 16px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(167, 139, 250, 0.15); padding-bottom: 14px; margin-bottom: 14px;">
                        <div>
                            <div class="bs-eyebrow">OFFICIAL BRANDSHIELD AUDIT RECORD</div>
                            <h2 style="margin: 4px 0; color: #FAF7FF; font-size: 22px;">{chosen_audit['title']}</h2>
                            <div style="font-size: 12.5px; color: #A78BFA;">Brand: <strong>{active_org['name']}</strong> · Channel: <strong>{chosen_audit.get('target_channel', 'General')}</strong></div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 40px; font-weight: 850; color: {status_color};">{score}%</div>
                            <span class="bs-badge-{status.lower()}">{status}</span>
                        </div>
                    </div>
                    <p style="color: #CFC2E3; font-size: 13.5px; line-height: 1.6; margin: 0;">{chosen_audit.get('summary', 'Audit evaluation completed.')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Generate HTML certificate
            report_data = {}
            if chosen_audit.get("full_report_json"):
                try:
                    report_data = json.loads(chosen_audit["full_report_json"])
                except Exception:
                    pass
            if not report_data:
                report_data = {
                    "overall_score": score,
                    "status": status,
                    "summary": chosen_audit.get("summary", ""),
                    "channel": chosen_audit.get("target_channel", "General Marketing"),
                    "original_content": chosen_audit.get("input_content", ""),
                    "corrected_content": chosen_audit.get("corrected_content", ""),
                    "violations": []
                }

            html_cert = generate_html_audit_report(report_data, active_org)

            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    label="📄 Download HTML Certificate (Print to PDF)",
                    data=html_cert,
                    file_name=f"BrandShield_Certificate_{chosen_audit['id']}.html",
                    mime="text/html",
                    type="primary",
                    use_container_width=True
                )
            with c2:
                st.download_button(
                    label="📥 Download Audit Data (JSON)",
                    data=json.dumps(report_data, indent=2),
                    file_name=f"BrandShield_Audit_{chosen_audit['id']}.json",
                    mime="application/json",
                    use_container_width=True
                )

    # ========================================================
    # TAB 2: RECURRING RISK ANALYSIS
    # ========================================================
    with rep_tab2:
        st.markdown('<div class="bs-section-label">TOP RECURRING BRAND VIOLATIONS & RISKS</div>', unsafe_allow_html=True)
        recur = get_recurring_violations(active_org_id)
        top_issues = recur.get("top_issues", [])

        if not top_issues:
            st.info("No recurring violations identified across your past audits.")
        else:
            st.caption("The most frequent compliance issues detected across all monitored campaigns:")
            for idx, (issue, count) in enumerate(top_issues):
                st.markdown(
                    f"""
                    <div style="background: rgba(22, 15, 38, 0.6); border: 1px solid rgba(167, 139, 250, 0.15); border-radius: 10px; padding: 14px 18px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="color: #F87171; font-weight: 700; margin-right: 8px;">#{idx + 1}</span>
                            <span style="color: #FAF7FF; font-size: 13.5px; font-weight: 550;">{issue}</span>
                        </div>
                        <span style="background: rgba(239, 68, 68, 0.15); color: #FCA5A5; padding: 3px 10px; border-radius: 20px; font-size: 11.5px; font-weight: 700;">
                            Flagged {count} time{'s' if count > 1 else ''}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # ========================================================
    # TAB 3: COMPLIANCE IMPROVEMENT TRENDS
    # ========================================================
    with rep_tab3:
        st.markdown('<div class="bs-section-label">HISTORICAL COMPLIANCE TRAJECTORY</div>', unsafe_allow_html=True)
        all_audits = get_analyses(active_org_id, limit=20)

        if not all_audits:
            st.info("Insufficient historical data to calculate compliance trajectories.")
        else:
            trend_df = pd.DataFrame([{
                "Date": a.get("created_at", "")[:10],
                "Audit": a.get("title", "")[:15],
                "Score": a.get("compliance_score", 100)
            } for a in reversed(all_audits)])

            st.line_chart(trend_df.set_index("Audit")["Score"], height=240, color="#8955D9")
            
            avg_recent = trend_df["Score"].tail(5).mean()
            avg_early = trend_df["Score"].head(5).mean()
            delta = round(avg_recent - avg_early, 1)

            st.markdown(
                f"""
                <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 10px; padding: 14px; margin-top: 14px; display: flex; align-items: center; justify-content: space-between;">
                    <div style="font-size: 13.5px; color: #FAF7FF;">
                        Rolling 5-Audit Compliance Trend: <strong>{'+' if delta >= 0 else ''}{delta}%</strong>
                    </div>
                    <span style="color: {'#34D399' if delta >= 0 else '#F87171'}; font-weight: 700; font-size: 12px;">
                        {'IMPROVING BRAND HEALTH' if delta >= 0 else 'NEEDS INTERVENTION'}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )
