import streamlit as st
from backend.database.db import (
    get_organizations,
    get_organization_by_id,
    get_brand_rules,
    add_brand_rule,
    delete_brand_rule,
    toggle_rule_status,
    apply_industry_preset,
    save_guideline_document,
    get_guideline_documents,
    log_activity
)
from processing.document_extraction.pdf_extractor import extract_text_from_pdf
from processing.ai_engine.vector_store import index_brand_rule
from components.header import render_view_header

RULE_CATEGORIES = [
    "Brand voice",
    "Content restrictions",
    "Visual identity",
    "Logo usage",
    "Typography",
    "Colour consistency"
]

def show_guidelines():
    user = st.session_state.get("user") or {}
    user_id = user.get("id", 1)

    render_view_header(
        "RULEBOOK ENGINE",
        "Brand Guidelines & Rulebook Workspace",
        "Manage compliance rule taxonomy, toggle active rules, install industry presets, and upload guideline PDFs."
    )

    organizations = get_organizations()
    if not organizations:
        st.warning("Please configure at least one brand profile first.")
        return

    active_org_id = st.session_state.get("active_org_id", organizations[0]["id"])
    active_org = get_organization_by_id(active_org_id) or organizations[0]

    # Tabs: Rule Management, Industry Presets, PDF Rulebook Ingestion
    tab_rules, tab_presets, tab_upload = st.tabs([
        "📋 Active Brand Rules",
        "⚡ Preset Industry Rulebooks",
        "📄 Upload Guideline PDF"
    ])

    # ========================================================
    # TAB 1: ACTIVE BRAND RULES & SEARCH
    # ========================================================
    with tab_rules:
        st.markdown(f'<div class="bs-section-label">ACTIVE RULES FOR {active_org["name"].upper()}</div>', unsafe_allow_html=True)

        # Filters: Search, Category, Severity
        f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
        with f_col1:
            search_rule = st.text_input("🔍 Search Rules", placeholder="Filter by rule title or keyword...", key="search_rules_input")
        with f_col2:
            cat_filter = st.selectbox("Category Filter", ["All Categories"] + RULE_CATEGORIES, key="cat_filter_select")
        with f_col3:
            sev_filter = st.selectbox("Severity Filter", ["All", "High", "Medium", "Low"], key="sev_filter_select")

        # Add Custom Rule expander
        with st.expander("➕ Create New Brand Rule", expanded=False):
            with st.form("create_rule_form"):
                r_cat = st.selectbox("Rule Category", RULE_CATEGORIES)
                r_title = st.text_input("Rule Title *", placeholder="e.g. Always Use Official BrandShield Slogan")
                r_desc = st.text_area("Rule Description *", placeholder="e.g. When referencing product capabilities, include standard trademark disclaimer.", height=80)
                r_sev = st.selectbox("Violation Severity", ["High", "Medium", "Low"], index=1)

                if st.form_submit_button("Add Rule to Brandbook", type="primary", use_container_width=True):
                    if not r_title.strip() or not r_desc.strip():
                        st.error("Rule title and description are required.")
                    else:
                        rule_id = add_brand_rule(
                            org_id=active_org["id"],
                            category=r_cat,
                            rule_title=r_title.strip(),
                            rule_description=r_desc.strip(),
                            severity=r_sev.lower()
                        )
                        index_brand_rule(rule_id, f"{r_cat} - {r_title}: {r_desc}")
                        log_activity(user_id, "RULE_ADDED", f"Added rule '{r_title}'", active_org["id"])
                        st.success(f"Rule '{r_title}' added and indexed in vector store!")
                        st.rerun()

        # Fetch and filter rules
        all_rules = get_brand_rules(active_org["id"])
        filtered_rules = []
        for r in all_rules:
            if cat_filter != "All Categories" and r.get("category") != cat_filter:
                continue
            if sev_filter != "All" and r.get("severity", "").lower() != sev_filter.lower():
                continue
            if search_rule:
                q = search_rule.lower()
                if q not in r.get("rule_title", "").lower() and q not in r.get("rule_description", "").lower():
                    continue
            filtered_rules.append(r)

        st.caption(f"Displaying {len(filtered_rules)} of {len(all_rules)} configured rules:")

        if not filtered_rules:
            st.info("No brand rules match your active filters.")
        else:
            for r in filtered_rules:
                sev = r.get("severity", "medium").lower()
                badge_cls = f"bs-badge-{sev}"
                is_enabled = bool(r.get("is_enabled", 1))

                st.markdown(
                    f"""
                    <div style="background: rgba(22, 15, 38, {0.75 if is_enabled else 0.35}); border: 1px solid rgba(167, 139, 250, {0.22 if is_enabled else 0.08}); border-radius: 12px; padding: 16px 20px; margin-bottom: 10px; opacity: {1.0 if is_enabled else 0.55};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span class="bs-eyebrow" style="margin: 0;">{r.get('category')}</span>
                            <div>
                                <span class="{badge_cls}">{r.get('severity')} Severity</span>
                                <span style="font-size: 11px; margin-left: 8px; color: {'#10B981' if is_enabled else '#7F7195'}; font-weight: 700;">
                                    {'● ACTIVE' if is_enabled else '○ MUTED'}
                                </span>
                            </div>
                        </div>
                        <h4 style="margin: 0 0 6px 0; color: #FAF7FF; font-size: 15px;">{r.get('rule_title')}</h4>
                        <p style="margin: 0; color: #B4A6C8; font-size: 13px; line-height: 1.5;">{r.get('rule_description')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                rc1, rc2, rc3 = st.columns([6, 1, 1])
                with rc2:
                    toggle_label = "Mute" if is_enabled else "Enable"
                    if st.button(toggle_label, key=f"toggle_rule_{r['id']}", use_container_width=True):
                        toggle_rule_status(r["id"], not is_enabled)
                        st.rerun()
                with rc3:
                    if st.button("Delete", key=f"del_rule_{r['id']}", use_container_width=True):
                        delete_brand_rule(r["id"])
                        log_activity(user_id, "RULE_DELETED", f"Deleted rule '{r.get('rule_title')}'", active_org["id"])
                        st.rerun()

    # ========================================================
    # TAB 2: INDUSTRY-SPECIFIC PRESET RULEBOOKS
    # ========================================================
    with tab_presets:
        st.markdown('<div class="bs-section-label">ONE-CLICK INDUSTRY RULE PRESETS</div>', unsafe_allow_html=True)
        st.caption("Instantly inject vetted industry compliance standards into your active brand profile.")

        preset_cols = st.columns(2)
        industries = [
            ("SaaS & Enterprise Tech", "SOC2 compliance, product naming, anti-hyperbole, enterprise tone of voice.", "💻"),
            ("FinTech & Banking", "Regulatory risk warnings, zero guarantee returns, transparent fee disclosures.", "💳"),
            ("Healthcare & Life Sciences", "FDA/CE disclaimers, no miracle language, empathetic clinical rigor.", "🏥"),
            ("E-Commerce & DTC Retail", "Clear refund/shipping policies, honest pricing, authentic social copy.", "🛍️")
        ]

        for idx, (ind_title, ind_desc, ind_icon) in enumerate(industries):
            with preset_cols[idx % 2]:
                st.markdown(
                    f"""
                    <div class="bs-action-card" style="margin-bottom: 14px;">
                        <div style="font-size: 24px; margin-bottom: 8px;">{ind_icon}</div>
                        <div class="bs-action-tag">INDUSTRY COMPLIANCE PACK</div>
                        <h3>{ind_title}</h3>
                        <p>{ind_desc}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button(f"Install {ind_title} Rules", key=f"install_preset_{idx}", use_container_width=True):
                    added = apply_industry_preset(active_org["id"], ind_title)
                    log_activity(user_id, "PRESET_INSTALLED", f"Installed {added} preset rules for {ind_title}", active_org["id"])
                    st.success(f"Installed {added} vetted compliance rules into {active_org['name']}!")
                    st.rerun()

    # ========================================================
    # TAB 3: UPLOAD GUIDELINE PDF
    # ========================================================
    with tab_upload:
        st.markdown('<div class="bs-section-label">INGEST BRAND RULEBOOK (PDF)</div>', unsafe_allow_html=True)
        st.caption("Upload official PDF brand guidelines. PyMuPDF will extract text, detect colors, and discover candidate rules.")

        up_pdf = st.file_uploader("Upload Brandbook PDF", type=["pdf", "txt"], key="guidelines_pdf_up")

        if up_pdf and active_org:
            st.info(f"File selected: **{up_pdf.name}** ({round(len(up_pdf.getvalue())/1024, 1)} KB)")

            if st.button("Extract & Auto-Discover Rules with PyMuPDF", type="primary"):
                with st.spinner("Extracting text and identifying rule patterns..."):
                    if up_pdf.name.lower().endswith(".pdf"):
                        extraction = extract_text_from_pdf(up_pdf.getvalue())
                    else:
                        text_content = up_pdf.getvalue().decode("utf-8", errors="ignore")
                        from processing.document_extraction.pdf_extractor import auto_extract_rules_from_text
                        extraction = {
                            "success": True,
                            "page_count": 1,
                            "full_text": text_content,
                            "suggested_rules": auto_extract_rules_from_text(text_content)
                        }

                    if extraction.get("success"):
                        save_guideline_document(
                            org_id=active_org["id"],
                            filename=up_pdf.name,
                            file_type=up_pdf.type or "application/pdf",
                            file_size=len(up_pdf.getvalue()),
                            extracted_text=extraction.get("full_text", "")
                        )
                        log_activity(user_id, "GUIDELINE_UPLOADED", f"Uploaded rulebook '{up_pdf.name}'", active_org["id"])
                        st.success(f"Extracted {len(extraction.get('full_text', ''))} characters across {extraction.get('page_count', 1)} page(s).")

                        suggested = extraction.get("suggested_rules", [])
                        if suggested:
                            st.markdown(f"### Discovered Rules ({len(suggested)})")
                            for s_idx, s_rule in enumerate(suggested):
                                with st.expander(f"Discovered: {s_rule['rule_title']} ({s_rule['category']})", expanded=True):
                                    st.write(s_rule["rule_description"])
                                    if st.button(f"Import Rule #{s_idx+1}", key=f"import_disc_{s_idx}"):
                                        r_id = add_brand_rule(
                                            org_id=active_org["id"],
                                            category=s_rule["category"],
                                            rule_title=s_rule["rule_title"],
                                            rule_description=s_rule["rule_description"],
                                            severity=s_rule["severity"]
                                        )
                                        index_brand_rule(r_id, f"{s_rule['category']} - {s_rule['rule_title']}: {s_rule['rule_description']}")
                                        st.success("Rule imported into brandbook!")
                                        st.rerun()
                        else:
                            st.info("Rulebook text saved to repository. No explicit pattern matches found.")

        # Previous rulebooks list
        docs = get_guideline_documents(active_org["id"])
        if docs:
            st.markdown("### Previously Ingested Rulebooks")
            for d in docs:
                st.markdown(
                    f"""
                    <div class="bs-rule-card">
                        <h4 style="margin: 0 0 4px 0;">📄 {d['filename']}</h4>
                        <p style="font-size: 12px; color: #9C8EB2;">Uploaded: {d['uploaded_at'][:16]} · Size: {round(d['file_size']/1024, 1)} KB</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
