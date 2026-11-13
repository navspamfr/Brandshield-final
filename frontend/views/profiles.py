import streamlit as st
import json
from PIL import Image
import io
from backend.database.db import (
    get_organizations,
    get_organization_by_id,
    create_organization,
    update_organization,
    delete_organization,
    update_brand_phrases,
    update_brand_logo,
    log_activity
)
from components.header import render_view_header

def show_brand_profiles():
    user = st.session_state.get("user") or {}
    user_id = user.get("id", 1)

    render_view_header(
        "BRAND REPOSITORY",
        "Brand Profile Management",
        "Configure company profiles, upload official logos, set color palettes, voice guidelines, and phrase rules."
    )

    organizations = get_organizations()
    st.session_state.organizations = organizations

    if not organizations:
        st.warning("No brand profiles configured yet. Create your first profile below.")
        active_org = None
    else:
        active_id = st.session_state.get("active_org_id", organizations[0]["id"])
        active_org = get_organization_by_id(active_id) or organizations[0]
        st.session_state.active_org_id = active_org["id"]

    tab_manage, tab_create = st.tabs(["🏢 Manage & Edit Profiles", "➕ Create New Brand Profile"])

    # ========================================================
    # TAB 1: MANAGE EXISTING PROFILES
    # ========================================================
    with tab_manage:
        if not active_org:
            st.info("Create a brand profile to get started.")
        else:
            col_sel, col_del = st.columns([4, 1])
            with col_sel:
                org_map = {o["id"]: f"{o['name']} ({o.get('industry', 'General')})" for o in organizations}
                chosen_id = st.selectbox(
                    "Select Brand to Edit",
                    options=list(org_map.keys()),
                    format_func=lambda x: org_map[x],
                    index=list(org_map.keys()).index(active_org["id"]),
                    key="manage_brand_selector"
                )
                if chosen_id != active_org["id"]:
                    st.session_state.active_org_id = chosen_id
                    st.rerun()

            with col_del:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if len(organizations) > 1:
                    if st.button("🗑️ Delete", type="secondary", use_container_width=True, help="Delete this brand profile"):
                        delete_organization(active_org["id"], user_id)
                        st.session_state.active_org_id = organizations[0]["id"]
                        st.success(f"Brand profile deleted.")
                        st.rerun()

            # Active Brand Overview Card
            p_col = active_org.get('primary_color', '#8955D9')
            s_col = active_org.get('secondary_color', '#D0B7FF')
            a_col = active_org.get('accent_color', '#100C18')

            st.markdown(
                f"""
                <div style="background: rgba(22, 15, 38, 0.7); border: 1px solid rgba(167, 139, 250, 0.2); border-radius: 14px; padding: 22px; margin-bottom: 24px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <div class="bs-eyebrow">{active_org.get('industry', 'Enterprise Brand')}</div>
                            <h2 style="margin: 4px 0 6px; font-size: 24px; color: #FAF7FF;">{active_org.get('name')}</h2>
                            <p style="margin: 0; color: #B4A6C8; font-size: 13.5px;">{active_org.get('tagline', 'No tagline set')}</p>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div style="text-align: center;">
                                <div style="width: 28px; height: 28px; border-radius: 6px; background: {p_col}; border: 1px solid rgba(255,255,255,0.2); margin: 0 auto 4px;"></div>
                                <span style="font-size: 10px; color: #A78BFA; font-weight: 700;">PRIMARY</span>
                            </div>
                            <div style="text-align: center;">
                                <div style="width: 28px; height: 28px; border-radius: 6px; background: {s_col}; border: 1px solid rgba(255,255,255,0.2); margin: 0 auto 4px;"></div>
                                <span style="font-size: 10px; color: #A78BFA; font-weight: 700;">SECONDARY</span>
                            </div>
                            <div style="text-align: center;">
                                <div style="width: 28px; height: 28px; border-radius: 6px; background: {a_col}; border: 1px solid rgba(255,255,255,0.2); margin: 0 auto 4px;"></div>
                                <span style="font-size: 10px; color: #A78BFA; font-weight: 700;">ACCENT</span>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Sub-sections: Profile Details, Brand Colors, Voice & Phrases
            p_sub1, p_sub2 = st.tabs(["📝 Core Information & Palette", "🗣️ Voice & Preferred/Prohibited Phrases"])

            with p_sub1:
                with st.form("edit_brand_core_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        e_name = st.text_input("Brand Name *", value=active_org.get("name", ""))
                        e_ind = st.text_input("Industry", value=active_org.get("industry", ""))
                        e_web = st.text_input("Official Website", value=active_org.get("website", ""))
                    with col2:
                        e_tag = st.text_input("Brand Tagline", value=active_org.get("tagline", ""))
                        e_aud = st.text_input("Target Audience", value=active_org.get("target_audience", ""))

                    e_desc = st.text_area("Brand Mission / Description", value=active_org.get("description", ""), height=80)

                    st.markdown('<div class="bs-eyebrow" style="margin-top: 14px;">BRAND COLOR PALETTE</div>', unsafe_allow_html=True)
                    cp1, cp2, cp3 = st.columns(3)
                    with cp1:
                        e_pri = st.color_picker("Primary Color", value=p_col)
                    with cp2:
                        e_sec = st.color_picker("Secondary Color", value=s_col)
                    with cp3:
                        e_acc = st.color_picker("Accent / Surface", value=a_col)

                    if st.form_submit_button("Save Profile & Colors", type="primary", use_container_width=True):
                        if not e_name.strip():
                            st.error("Brand name cannot be blank.")
                        else:
                            update_organization(
                                org_id=active_org["id"],
                                name=e_name.strip(),
                                industry=e_ind.strip(),
                                tagline=e_tag.strip(),
                                description=e_desc.strip(),
                                website=e_web.strip(),
                                tone_of_voice=active_org.get("tone_of_voice", ""),
                                target_audience=e_aud.strip(),
                                primary_color=e_pri,
                                secondary_color=e_sec,
                                accent_color=e_acc
                            )
                            log_activity(user_id, "PROFILE_UPDATED", f"Updated profile & colors for '{e_name}'", active_org["id"])
                            st.success("Brand profile updated successfully.")
                            st.rerun()

                # Logo upload section
                st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
                st.markdown('<div class="bs-section-label">OFFICIAL LOGO ASSET</div>', unsafe_allow_html=True)
                logo_file = st.file_uploader("Upload Brand Logo (PNG / SVG with transparency)", type=["png", "jpg", "jpeg", "svg"], key="brand_logo_uploader")
                if logo_file:
                    logo_img = Image.open(logo_file)
                    st.image(logo_img, caption=f"Logo Preview: {logo_file.name}", width=200)
                    if st.button("Save As Official Logo", type="secondary"):
                        # Save path
                        update_brand_logo(active_org["id"], logo_file.name)
                        log_activity(user_id, "LOGO_UPDATED", f"Uploaded new logo for '{active_org.get('name')}'", active_org["id"])
                        st.success("Official logo updated in brand repository!")

            with p_sub2:
                st.markdown('<div class="bs-section-label">VOICE, TONE & PHRASE GUIDELINES</div>', unsafe_allow_html=True)

                with st.form("edit_phrases_form"):
                    e_tone = st.text_input(
                        "Tone of Voice Keywords",
                        value=active_org.get("tone_of_voice", "Professional, Authoritative, Visionary, Precise"),
                        help="Comma-separated adjectives describing the brand persona."
                    )

                    pref_raw = active_org.get("preferred_phrases") or "[]"
                    proh_raw = active_org.get("prohibited_phrases") or "[]"
                    try:
                        pref_list = json.loads(pref_raw)
                        proh_list = json.loads(proh_raw)
                    except Exception:
                        pref_list = []
                        proh_list = []

                    pref_text = "\n".join(pref_list) if pref_list else "Protect your identity.\nEvery asset. Every detail.\nEnterprise-grade assurance."
                    proh_text = "\n".join(proh_list) if proh_list else "100% guaranteed\nhack-proof\nwipes out all competitors\nsuper cool\ninsane deal"

                    col_pref, col_proh = st.columns(2)
                    with col_pref:
                        st.markdown("**Preferred Phrases (1 per line):**")
                        st.caption("Approved slogans, key messaging pillars, and standard statements.")
                        new_pref = st.text_area("Preferred", value=pref_text, height=130, label_visibility="collapsed")

                    with col_proh:
                        st.markdown("**Prohibited Phrases (1 per line):**")
                        st.caption("Forbidden superlatives, slang, and unverified claims.")
                        new_proh = st.text_area("Prohibited", value=proh_text, height=130, label_visibility="collapsed")

                    if st.form_submit_button("Update Voice & Phrase Rules", type="primary", use_container_width=True):
                        p_list = [p.strip() for p in new_pref.splitlines() if p.strip()]
                        pr_list = [p.strip() for p in new_proh.splitlines() if p.strip()]
                        
                        update_organization(
                            org_id=active_org["id"],
                            name=active_org.get("name"),
                            industry=active_org.get("industry"),
                            tagline=active_org.get("tagline"),
                            description=active_org.get("description"),
                            website=active_org.get("website"),
                            tone_of_voice=e_tone.strip(),
                            target_audience=active_org.get("target_audience"),
                            primary_color=p_col,
                            secondary_color=s_col,
                            accent_color=a_col
                        )
                        update_brand_phrases(active_org["id"], p_list, pr_list)
                        log_activity(user_id, "PHRASES_UPDATED", f"Updated tone & phrase rules for '{active_org.get('name')}'", active_org["id"])
                        st.success("Tone and phrase dictionary saved!")
                        st.rerun()

    # ========================================================
    # TAB 2: CREATE NEW BRAND PROFILE
    # ========================================================
    with tab_create:
        st.markdown('<div class="bs-section-label">CREATE NEW BRAND PROFILE</div>', unsafe_allow_html=True)
        with st.form("create_new_brand_form"):
            c_name = st.text_input("Brand Name *", placeholder="e.g. Acme Cloud Corp")
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                c_ind = st.text_input("Industry", placeholder="e.g. CyberSecurity, FinTech, HealthTech")
                c_web = st.text_input("Website URL", placeholder="https://example.com")
            with col_i2:
                c_tag = st.text_input("Tagline", placeholder="e.g. Next generation intelligence")
                c_aud = st.text_input("Target Audience", placeholder="e.g. Enterprise architects, B2B CTOs")

            c_tone = st.text_input("Tone of Voice", value="Authoritative, Professional, Crisp, Trustworthy")
            c_desc = st.text_area("Brand Mission / Description", placeholder="Summary of brand identity and core values.")

            st.markdown('<div class="bs-eyebrow">BRAND COLOR PALETTE</div>', unsafe_allow_html=True)
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                c_pri = st.color_picker("Primary Color", value="#8955D9")
            with col_c2:
                c_sec = st.color_picker("Secondary Color", value="#D0B7FF")
            with col_c3:
                c_acc = st.color_picker("Accent / Surface", value="#100C18")

            if st.form_submit_button("Create Brand Profile", type="primary", use_container_width=True):
                if not c_name.strip():
                    st.error("Brand name is required.")
                else:
                    new_id = create_organization(
                        user_id=user_id,
                        name=c_name.strip(),
                        industry=c_ind.strip(),
                        tagline=c_tag.strip(),
                        description=c_desc.strip(),
                        website=c_web.strip(),
                        tone_of_voice=c_tone.strip(),
                        target_audience=c_aud.strip(),
                        primary_color=c_pri,
                        secondary_color=c_sec,
                        accent_color=c_acc
                    )
                    st.session_state.active_org_id = new_id
                    st.success(f"Brand profile '{c_name}' created successfully!")
                    st.rerun()
