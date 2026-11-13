import streamlit as st
import json
from backend.database.db import (
    get_organizations,
    get_analyses,
    get_recent_activity,
    get_organization_by_id
)
from processing.compliance.report_generator import generate_html_audit_report
from components.header import render_view_header

def show_history():
    render_view_header(
        "AUDIT REPOSITORY",
        "Activity History & Audit Records",
        "Inspect historical brand audits, search campaign records, review revisions, and download official certificates."
    )

    tab_analyses, tab_activity = st.tabs(["📊 Searchable Audit Records", "🕒 System Audit Trail"])

    # ========================================================
    # TAB 1: SEARCHABLE AUDIT RECORDS
    # ========================================================
    with tab_analyses:
        organizations = get_organizations()
        org_filter_options = {0: "All Brand Profiles"}
        for o in organizations:
            org_filter_options[o["id"]] = o["name"]

        f_col1, f_col2, f_col3 = st.columns([2, 1, 1])

        with f_col1:
            search_query = st.text_input("🔍 Search Audits", placeholder="Filter by title, channel, or text...", key="hist_search_box")

        with f_col2:
            selected_org_filter = st.selectbox(
                "Filter Brand",
                options=list(org_filter_options.keys()),
                format_func=lambda x: org_filter_options[x],
                key="hist_brand_select"
            )

        with f_col3:
            status_filter = st.selectbox("Status Filter", ["All Statuses", "Passed", "Warning", "Failed"], key="hist_status_select")

        org_id_arg = selected_org_filter if selected_org_filter != 0 else None
        analyses = get_analyses(org_id=org_id_arg, limit=100)

        # Apply in-memory search and status filters
        filtered_analyses = []
        for a in analyses:
            if status_filter != "All Statuses" and a["status"] != status_filter:
                continue
            if search_query:
                q = search_query.lower()
                title_match = q in a.get("title", "").lower()
                content_match = q in (a.get("input_content") or "").lower()
                channel_match = q in (a.get("target_channel") or "").lower()
                if not (title_match or content_match or channel_match):
                    continue
            filtered_analyses.append(a)

        st.caption(f"Showing {len(filtered_analyses)} recorded audit(s):")

        if not filtered_analyses:
            st.markdown(
                """
                <div class="bs-activity-empty">
                    <div class="bs-empty-icon">◷</div>
                    <h3>No audit records found</h3>
                    <p>No audits match the current search filters. Run a new audit in Content Analysis.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            for item in filtered_analyses:
                score = item.get("compliance_score", 100)
                status = item.get("status", "Passed")
                status_cls = f"bs-badge-{status.lower()}"
                title = item.get("title", "Untitled Audit")
                org_name = item.get("org_name", "Brand")
                date_str = item.get("created_at", "")[:16]
                channel = item.get("target_channel", "General")
                asset_type = item.get("asset_type", "text").capitalize()

                with st.expander(f"[{score}%] {title} · {org_name} ({date_str})", expanded=False):
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <div>
                                <span style="font-size: 13px; color: #B4A6C8;">Channel: <strong>{channel}</strong> · Type: <strong>{asset_type}</strong></span>
                            </div>
                            <div>
                                <span class="{status_cls}">{status} ({score}%)</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if item.get("summary"):
                        st.info(item["summary"])

                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**Original Evaluated Content:**")
                        st.text_area("Original", value=item.get("input_content", ""), height=90, disabled=True, key=f"hist_orig_{item['id']}")

                    with c2:
                        st.markdown("**AI Corrected Content:**")
                        st.text_area("Corrected", value=item.get("corrected_content", ""), height=90, disabled=True, key=f"hist_corr_{item['id']}")

                    # Violation breakdown if available
                    report_json = item.get("full_report_json")
                    rep_dict = {}
                    if report_json:
                        try:
                            rep_dict = json.loads(report_json)
                            v_list = rep_dict.get("violations", [])
                            if v_list:
                                st.markdown(f"**Detected Violations ({len(v_list)}):**")
                                for v in v_list:
                                    s_cls = f"bs-badge-{v.get('severity', 'medium').lower()}"
                                    st.markdown(
                                        f"""
                                        <div style="padding: 8px 12px; margin-bottom: 6px; background: rgba(19, 13, 31, 0.7); border: 1px solid rgba(167, 139, 250, 0.15); border-radius: 6px; font-size: 13px;">
                                            <span class="{s_cls}">{v.get('severity')}</span>
                                            <strong style="color: #FAF7FF; margin-left: 8px;">{v.get('category')}:</strong> {v.get('issue')}
                                            <div style="color: #86efac; margin-top: 4px;">💡 {v.get('suggestion')}</div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                        except Exception:
                            pass

                    if not rep_dict:
                        rep_dict = {
                            "overall_score": score,
                            "status": status,
                            "summary": item.get("summary", ""),
                            "original_content": item.get("input_content", ""),
                            "corrected_content": item.get("corrected_content", ""),
                            "violations": [],
                            "sub_scores": {"tone": score, "vocab": score, "legal": score, "visual": 100}
                        }

                    dl_c1, dl_c2 = st.columns(2)
                    with dl_c1:
                        st.download_button(
                            label="📄 Download HTML Certificate (Print to PDF)",
                            data=generate_html_audit_report(rep_dict, {"name": org_name}),
                            file_name=f"certificate_{item['id']}.html",
                            mime="text/html",
                            key=f"hist_dl_html_{item['id']}",
                            use_container_width=True
                        )
                    with dl_c2:
                        st.download_button(
                            label="📥 Download JSON Data",
                            data=report_json or json.dumps(item, indent=2),
                            file_name=f"audit_{item['id']}.json",
                            mime="application/json",
                            key=f"hist_dl_json_{item['id']}",
                            use_container_width=True
                        )

    # ========================================================
    # TAB 2: SYSTEM AUDIT TRAIL
    # ========================================================
    with tab_activity:
        st.markdown('<div class="bs-section-label">FULL SYSTEM AUDIT TRAIL</div>', unsafe_allow_html=True)
        activities = get_recent_activity(limit=60)

        if not activities:
            st.info("No activity records logged.")
        else:
            for act in activities:
                action_type = act.get("action_type", "EVENT")
                desc = act.get("description", "")
                org = act.get("org_name") or "Global"
                created = act.get("created_at", "")[:19]

                st.markdown(
                    f"""
                    <div class="bs-activity-row">
                        <div>
                            <strong>{desc}</strong>
                            <p>{org} · {created}</p>
                        </div>
                        <span class="bs-activity-status" style="letter-spacing: 0.8px;">
                            {action_type}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
