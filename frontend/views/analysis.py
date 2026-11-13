import streamlit as st
import json
import pandas as pd
from datetime import datetime
from PIL import Image
import io

from backend.database.db import (
    get_organizations,
    get_organization_by_id,
    save_analysis,
    log_activity,
    get_setting
)
from processing.document_extraction.multi_format_parser import parse_uploaded_file
from processing.compliance.deep_analyzer import perform_deep_compliance_audit
from processing.ai_engine.vector_store import retrieve_relevant_rules
from processing.compliance.report_generator import generate_html_audit_report
from components.header import render_view_header

def show_analysis():
    user = st.session_state.get("user") or {}
    user_id = user.get("id", 1)

    render_view_header(
        "CONTENT INTELLIGENCE",
        "AI Brand Compliance Audit & Workbench",
        "Multi-modal compliance auditing for Copy, PDFs, Images, and Campaign Spreadsheets with interactive fixes."
    )

    organizations = get_organizations()
    if not organizations:
        st.warning("Please configure at least one brand profile in Guidelines before running an audit.")
        if st.button("Go to Guidelines"):
            st.session_state.current_page = "guidelines"
            st.rerun()
        return

    active_org_id = st.session_state.get("active_org_id", organizations[0]["id"])
    active_org = get_organization_by_id(active_org_id) or organizations[0]

    # Target brand and channel selection
    col_brand, col_channel = st.columns([2, 1])

    with col_brand:
        org_map = {o["id"]: o["name"] for o in organizations}
        selected_org_id = st.selectbox(
            "Target Brand Profile",
            options=list(org_map.keys()),
            format_func=lambda x: org_map[x],
            index=list(org_map.keys()).index(active_org["id"]),
            key="analysis_target_org"
        )
        if selected_org_id != active_org["id"]:
            st.session_state.active_org_id = selected_org_id
            st.rerun()

    with col_channel:
        target_channel = st.selectbox(
            "Distribution Channel",
            ["Social Media", "Press Release", "Billboard / Poster", "Website / Landing Page", "Email Campaign", "Print Ad", "Product Packaging"]
        )

    st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)

    # Mode Selector: Single Audit vs Batch Multi-File Audit
    mode_tab1, mode_tab2 = st.tabs(["⚡ Single Asset Audit & Interactive Fixer", "📁 Batch Multi-File Audit"])

    # ========================================================
    # MODE 1: SINGLE ASSET AUDIT & INTERACTIVE FIXER
    # ========================================================
    with mode_tab1:
        st.markdown('<div class="bs-section-label">INPUT ASSET (COPY, PDF, OR VISUAL)</div>', unsafe_allow_html=True)

        audit_title = st.text_input("Audit Title", value=f"{active_org['name']} {target_channel} Review", key="audit_title_input")

        # Live copy buffer in session state for interactive editing
        if "interactive_copy" not in st.session_state:
            st.session_state.interactive_copy = ""

        input_type = st.radio("Choose Input Method", ["Direct Text / Copy", "Upload File (PDF, Image, TXT, CSV)"], horizontal=True)

        input_text = ""
        uploaded_img_bytes = None
        preview_img = None

        if input_type == "Direct Text / Copy":
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Load High-Risk Sample Copy", use_container_width=True):
                    st.session_state.interactive_copy = (
                        f"{active_org['name'].lower()} announces 100% guaranteed super cool solution that destroys all competitors!!! "
                        f"Try our crazy cheap AI deal today."
                    )
                    st.rerun()
            with c2:
                if st.button("Load Compliant Sample Copy", use_container_width=True):
                    st.session_state.interactive_copy = (
                        f"{active_org['name']} delivers enterprise-grade brand intelligence. "
                        f"Protect your identity. Every asset. Every detail."
                    )
                    st.rerun()

            input_text = st.text_area(
                "Marketing Copy / Slogans / Ad Text",
                value=st.session_state.interactive_copy,
                height=130,
                placeholder=f"Enter {active_org['name']} copy here...",
                key="direct_copy_input"
            )
            st.session_state.interactive_copy = input_text

            # Optional companion image
            with st.expander("🖼️ Attach Visual Asset (Image) for Visual & Palette Check"):
                opt_img = st.file_uploader("Upload Banner or Poster", type=["png", "jpg", "jpeg", "webp"], key="opt_img_uploader")
                if opt_img:
                    uploaded_img_bytes = opt_img.getvalue()
                    preview_img = Image.open(io.BytesIO(uploaded_img_bytes))
                    st.image(preview_img, caption=f"{opt_img.name} ({preview_img.size[0]}x{preview_img.size[1]}px)", width=260)

        else:
            # File Upload Mode (PDF, Images, TXT, CSV)
            multi_file = st.file_uploader(
                "Upload Document, Poster, or Campaign Spreadsheet",
                type=["pdf", "png", "jpg", "jpeg", "webp", "txt", "md", "csv", "json"],
                key="single_file_upload"
            )
            if multi_file:
                parsed = parse_uploaded_file(multi_file.name, multi_file.getvalue())
                st.success(f"File parsed: **{multi_file.name}** ({parsed['file_type']} - {parsed['file_size_kb']} KB)")

                if parsed.get("text_content"):
                    st.caption("Extracted Text Content:")
                    input_text = st.text_area("Extracted Copy", value=parsed["text_content"][:2000], height=120)
                    st.session_state.interactive_copy = input_text

                if parsed.get("images"):
                    st.caption(f"Extracted {len(parsed['images'])} Image Asset(s):")
                    first_img = parsed["images"][0]
                    uploaded_img_bytes = first_img["bytes"]
                    preview_img = first_img["pil_image"]
                    st.image(preview_img, caption=first_img["name"], width=260)

        # Audit Trigger
        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
        if st.button("⚡ Run Deep AI Compliance Audit", type="primary", use_container_width=True):
            if not input_text.strip() and uploaded_img_bytes is None:
                st.error("Please provide text copy or upload a file.")
            else:
                with st.spinner("Retrieving vector rules, auditing linguistic depth, WCAG contrast, and tone..."):
                    api_key = get_setting("openai_api_key")
                    retrieved = retrieve_relevant_rules(active_org["id"], input_text or "", top_k=5, api_key=api_key)

                    report = perform_deep_compliance_audit(
                        content_text=input_text.strip() if input_text else None,
                        brand_info=active_org,
                        relevant_rules=retrieved,
                        image_file=uploaded_img_bytes,
                        target_channel=target_channel,
                        api_key=api_key
                    )

                    # Save in database
                    save_analysis(
                        org_id=active_org["id"],
                        user_id=user_id,
                        title=audit_title.strip() or "Content Audit",
                        asset_type="multimodal" if (input_text and uploaded_img_bytes) else ("image" if uploaded_img_bytes else "text"),
                        target_channel=target_channel,
                        input_content=input_text.strip() if input_text else "[Visual Asset]",
                        image_path=None,
                        compliance_score=report["overall_score"],
                        status=report["status"],
                        corrected_content=report.get("corrected_content", ""),
                        summary=report.get("summary", ""),
                        full_report_json=json.dumps(report)
                    )

                    st.session_state["deep_audit_report"] = report
                    st.session_state["active_corrected_copy"] = report.get("corrected_content", input_text)

        # ----------------------------------------------------
        # AUDIT RESULTS & INTERACTIVE WORKBENCH
        # ----------------------------------------------------
        if "deep_audit_report" in st.session_state:
            rep = st.session_state["deep_audit_report"]
            score = rep["overall_score"]
            status = rep["status"]
            status_cls = f"bs-badge-{status.lower()}"

            st.markdown("---")
            st.markdown('<div class="bs-section-label">AUDIT SCORECARD & INTERACTIVE WORKBENCH</div>', unsafe_allow_html=True)

            # Hero Card
            st.markdown(
                f"""
                <div class="bs-metric-card" style="padding: 24px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div class="bs-eyebrow">AUDIT HEALTH SUMMARY</div>
                        <h2 style="margin: 6px 0; color: #f5f0ff; font-size: 26px;">{active_org['name']} Compliance Score</h2>
                        <p style="margin: 0; color: #a99ec0; font-size: 14px;">{rep.get('summary')}</p>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 46px; font-weight: 850; color: {'#34d399' if score>=90 else ('#fbbf24' if score>=70 else '#f87171')};">
                            {score}%
                        </div>
                        <span class="{status_cls}">{status}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Interactive Multi-Dimension Charts & Metrics
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            subs = rep.get("sub_scores", {})
            m_col1.metric("Tone of Voice", f"{subs.get('tone', 100)}%")
            m_col2.metric("Vocabulary & Claims", f"{subs.get('vocab', 100)}%")
            m_col3.metric("Legal & Disclaimers", f"{subs.get('legal', 100)}%")
            m_col4.metric("Visual & Contrast", f"{subs.get('visual', 100)}%")
            read_score = rep.get("readability", {}).get("score", 85) if rep.get("readability") else 100
            m_col5.metric("Readability Ease", f"{read_score}/100")

            # Chart breakdown
            chart_col, read_col = st.columns([3, 2])
            with chart_col:
                score_df = pd.DataFrame({
                    "Dimension": ["Tone of Voice", "Vocabulary", "Legal & Claims", "Visual & Contrast", "Readability"],
                    "Score (%)": [subs.get('tone', 100), subs.get('vocab', 100), subs.get('legal', 100), subs.get('visual', 100), read_score]
                })
                st.bar_chart(score_df.set_index("Dimension"), height=190, color="#8955D9")

            with read_col:
                read_info = rep.get("readability")
                if read_info:
                    st.markdown(
                        f"""
                        <div class="bs-rule-card" style="height: 190px; box-sizing: border-box;">
                            <div class="bs-eyebrow">LINGUISTIC ANALYSIS</div>
                            <h4 style="margin: 4px 0;">{read_info['label']}</h4>
                            <p style="font-size: 12px;">Grade Level: <strong>Grade {read_info['grade_level']}</strong></p>
                            <p style="font-size: 12px;">Avg Sentence Length: <strong>{read_info['avg_words_per_sentence']} words</strong></p>
                            <p style="font-size: 12px;">Word Count: <strong>{read_info['word_count']} words</strong></p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.info("Visual asset audited. Contrast and composition analyzed.")

            # ------------------------------------------------
            # INTERACTIVE WORKBENCH: APPLY SUGGESTIONS IN 1 CLICK
            # ------------------------------------------------
            violations = rep.get("violations", [])
            st.markdown(f'<div class="bs-section-label">INTERACTIVE VIOLATION FIXER ({len(violations)} ISSUES)</div>', unsafe_allow_html=True)

            if not violations:
                st.success("🎉 Zero brand violations detected! Your asset is ready for deployment.")
            else:
                for idx, v in enumerate(violations):
                    sev = v.get("severity", "Medium")
                    badge_cls = f"bs-badge-{sev.lower()}"
                    v_col1, v_col2 = st.columns([4, 1])

                    with v_col1:
                        st.markdown(
                            f"""
                            <div class="bs-rule-card" style="margin-bottom: 8px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                    <strong style="color: #ede5fa; font-size: 13px;">{v.get('category')}</strong>
                                    <span class="{badge_cls}">{sev}</span>
                                </div>
                                <div style="color: #fca5a5; font-size: 13px;"><strong>Issue:</strong> {v.get('issue')}</div>
                                <div style="color: #86efac; font-size: 13px; margin-top: 3px;"><strong>💡 Suggestion:</strong> {v.get('suggestion')}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with v_col2:
                        snippet = v.get("snippet")
                        if snippet and snippet in st.session_state.interactive_copy:
                            if st.button("⚡ Apply Fix", key=f"fix_btn_{idx}", use_container_width=True):
                                # Replace snippet with suggestion
                                rep_corr = rep.get("corrected_content", "")
                                if rep_corr:
                                    st.session_state.interactive_copy = rep_corr
                                    st.rerun()

            # Interactive Live Editor
            st.markdown('<div class="bs-section-label">LIVE COPY WORKBENCH & DIFF PREVIEW</div>', unsafe_allow_html=True)
            v_tab_diff, v_tab_edit = st.tabs(["✨ Visual Diff View", "✍️ Live Editable Copy"])

            with v_tab_diff:
                st.markdown(rep.get("diff_html", ""), unsafe_allow_html=True)

            with v_tab_edit:
                active_text = st.text_area(
                    "Live Editable Copy (Updates instantly):",
                    value=st.session_state.get("active_corrected_copy", rep.get("corrected_content", "")),
                    height=130,
                    key="workbench_editable_text"
                )
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("🔄 Re-Audit This Revised Copy", use_container_width=True):
                        st.session_state.interactive_copy = active_text
                        st.rerun()
                with b2:
                    st.code(active_text, language="markdown")

            # ------------------------------------------------
            # VISUAL & WCAG ACCESSIBILITY COMPOSITION
            # ------------------------------------------------
            comp = rep.get("composition_analysis")
            if comp and not comp.get("error"):
                st.markdown('<div class="bs-section-label">VISUAL COMPOSITION & WCAG ACCESSIBILITY</div>', unsafe_allow_html=True)
                v_col1, v_col2, v_col3 = st.columns(3)
                v_col1.metric("Dimensions", comp.get("dimensions", "—"))
                v_col2.metric("Aspect Ratio", f"{comp.get('aspect_ratio', 1.0)}:1")
                v_col3.metric("Channel Fit", comp.get("recommended_channel_fit", "Custom"))

                wcag = comp.get("wcag_contrast")
                if wcag:
                    status_text = "PASSED WCAG AA (Compliant)" if wcag["wcag_aa_compliant"] else "FAILED (Low Contrast)"
                    color_tag = "#34d399" if wcag["wcag_aa_compliant"] else "#f87171"
                    st.markdown(
                        f"""
                        <div style="background: #140f21; border: 1px solid #2d2146; border-radius: 8px; padding: 12px; margin-top: 8px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span class="bs-eyebrow">WCAG 2.1 TEXT CONTRAST</span>
                                <div style="font-size: 14px; color: #ede6fa; margin-top: 2px;">
                                    Dominant Contrast Ratio: <strong>{wcag['contrast_ratio']}</strong>
                                    (Between {wcag.get('dominant_primary_hex')} and {wcag.get('dominant_secondary_hex')})
                                </div>
                            </div>
                            <span style="color: {color_tag}; font-weight: 700; font-size: 12px;">{status_text}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # Exporting: PDF/HTML Certificate + JSON
            st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="bs-section-label">EXPORT & SHARE AUDIT</div>', unsafe_allow_html=True)

            html_certificate = generate_html_audit_report(rep, active_org)
            e_col1, e_col2 = st.columns(2)

            with e_col1:
                st.download_button(
                    label="📄 Download HTML Audit Certificate & Report (Printable to PDF)",
                    data=html_certificate,
                    file_name=f"brandshield_certificate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html",
                    use_container_width=True
                )
            with e_col2:
                st.download_button(
                    label="📥 Download Audit Data (JSON)",
                    data=json.dumps(rep, indent=2),
                    file_name=f"brandshield_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )

    # ========================================================
    # MODE 2: BATCH MULTI-FILE AUDIT
    # ========================================================
    with mode_tab2:
        st.markdown('<div class="bs-section-label">BATCH MULTI-FILE COMPLIANCE AUDITING</div>', unsafe_allow_html=True)
        st.caption("Upload multiple marketing files (Posters, Brochures, Ad copy, Campaign CSVs) to run a batch brand health evaluation.")

        batch_files = st.file_uploader(
            "Upload Multiple Campaign Assets",
            type=["pdf", "png", "jpg", "jpeg", "webp", "txt", "md", "csv"],
            accept_multiple_files=True,
            key="batch_uploader"
        )

        if batch_files:
            st.info(f"Selected {len(batch_files)} asset(s) for batch audit.")

            if st.button("⚡ Run Batch Compliance Evaluation", type="primary", use_container_width=True):
                batch_results = []
                progress_bar = st.progress(0)

                for idx, f in enumerate(batch_files):
                    parsed = parse_uploaded_file(f.name, f.getvalue())
                    text_to_audit = parsed.get("text_content", "")
                    img_bytes_to_audit = parsed["images"][0]["bytes"] if parsed.get("images") else None

                    api_key = get_setting("openai_api_key")
                    retrieved = retrieve_relevant_rules(active_org["id"], text_to_audit or f.name, top_k=3, api_key=api_key)

                    f_rep = perform_deep_compliance_audit(
                        content_text=text_to_audit if text_to_audit else None,
                        brand_info=active_org,
                        relevant_rules=retrieved,
                        image_file=img_bytes_to_audit,
                        target_channel=target_channel,
                        api_key=api_key
                    )

                    batch_results.append({
                        "File Name": f.name,
                        "Type": parsed["file_type"],
                        "Compliance Score": f"{f_rep['overall_score']}%",
                        "Score_Num": f_rep['overall_score'],
                        "Status": f_rep["status"],
                        "Violations": len(f_rep["violations"]),
                        "Summary": f_rep.get("summary", ""),
                        "Report": f_rep
                    })

                    progress_bar.progress((idx + 1) / len(batch_files))

                st.session_state["batch_results"] = batch_results

        if "batch_results" in st.session_state:
            b_res = st.session_state["batch_results"]
            st.markdown("### Batch Audit Results Summary")

            b_df = pd.DataFrame([{
                "File": r["File Name"],
                "Type": r["Type"],
                "Score": r["Compliance Score"],
                "Status": r["Status"],
                "Issues Found": r["Violations"]
            } for r in b_res])

            st.dataframe(b_df, use_container_width=True)

            # Drill down into any batch item
            st.markdown("#### Inspect Individual Asset from Batch")
            selected_file = st.selectbox("Select Asset to Inspect", [r["File Name"] for r in b_res])
            chosen = next(r for r in b_res if r["File Name"] == selected_file)

            st.markdown(f"**Score:** {chosen['Compliance Score']} · **Status:** {chosen['Status']}")
            st.write(chosen["Summary"])
            if chosen["Report"].get("violations"):
                for v in chosen["Report"]["violations"]:
                    st.markdown(f"- **[{v.get('severity')}] {v.get('category')}:** {v.get('issue')} *(💡 {v.get('suggestion')})*")
