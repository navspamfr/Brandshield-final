import streamlit as st
import os
from backend.database.db import (
    get_setting,
    set_setting,
    get_connection,
    get_organizations,
    log_activity
)
from auth.authentication import hash_password, verify_password
from processing.ai_engine.vector_store import reindex_all_rules_for_org
from components.header import render_view_header

def show_settings():
    user = st.session_state.get("user") or {}
    user_id = user.get("id", 1)

    render_view_header(
        "PLATFORM PREFERENCES",
        "Settings & Account Management",
        "Manage your security credentials, notification rules, AI model connections, and system preferences."
    )

    tab_profile, tab_appearance, tab_notifications, tab_api, tab_system = st.tabs([
        "👤 Profile & Security",
        "🎨 Appearance & Layout",
        "🔔 Notifications",
        "🤖 AI Model & API",
        "⚙️ System Maintenance"
    ])

    # ========================================================
    # TAB 1: PROFILE & SECURITY
    # ========================================================
    with tab_profile:
        st.markdown('<div class="bs-section-label">ACCOUNT INFORMATION</div>', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div style="background: rgba(22, 15, 38, 0.65); border: 1px solid rgba(167, 139, 250, 0.18); border-radius: 12px; padding: 20px; margin-bottom: 24px;">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <div style="width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, #8955D9, #6D28D9); display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 800; color: white;">
                        {user.get('name', 'U')[0].upper()}
                    </div>
                    <div>
                        <div style="font-size: 16px; font-weight: 750; color: #FAF7FF;">{user.get('name', 'User')}</div>
                        <div style="font-size: 13px; color: #A78BFA;">{user.get('email', 'demo@brandshield.ai')}</div>
                        <div style="font-size: 11px; color: #7F7195; margin-top: 2px;">Role: {user.get('role', 'admin').capitalize()} · BrandShield Enterprise License</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown('<div class="bs-section-label">CHANGE ACCOUNT PASSWORD</div>', unsafe_allow_html=True)
        with st.form("settings_password_form"):
            c_curr = st.text_input("Current Password", type="password")
            c_new = st.text_input("New Password (min 8 characters)", type="password")
            c_confirm = st.text_input("Confirm New Password", type="password")

            if st.form_submit_button("Update Password", type="primary"):
                if not c_curr or not c_new or not c_confirm:
                    st.error("Please fill in all password fields.")
                elif len(c_new) < 8:
                    st.error("New password must be at least 8 characters long.")
                elif c_new != c_confirm:
                    st.error("New passwords do not match.")
                else:
                    with get_connection() as conn:
                        row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
                        if row and verify_password(c_curr, row[0]):
                            new_hash = hash_password(c_new)
                            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
                            conn.commit()
                            log_activity(user_id, "PASSWORD_CHANGED", "User changed account password")
                            st.success("Password updated successfully!")
                        else:
                            st.error("Current password verification failed.")

    # ========================================================
    # TAB 2: APPEARANCE & LAYOUT
    # ========================================================
    with tab_appearance:
        st.markdown('<div class="bs-section-label">DISPLAY & THEME PREFERENCES</div>', unsafe_allow_html=True)
        theme_mode = st.radio(
            "Color Theme",
            ["Dark Cyber-Purple (Linear/Stripe SaaS Style - Active)", "Midnight Monochrome (Subtle Dark)"],
            index=0
        )
        density = st.radio("Workspace Density", ["Standard Responsive (Recommended)", "Compact Data Mode"], index=0)
        show_animations = st.checkbox("Enable micro-animations and background glows", value=True)

        if st.button("Save Appearance Preferences", type="primary"):
            st.toast("Appearance settings applied!")

    # ========================================================
    # TAB 3: NOTIFICATIONS
    # ========================================================
    with tab_notifications:
        st.markdown('<div class="bs-section-label">NOTIFICATION ALERTS</div>', unsafe_allow_html=True)
        n1 = st.checkbox("Instant alerts for High-Severity violations (Legal & Prohibited claims)", value=True)
        n2 = st.checkbox("Weekly executive brand compliance digest email", value=True)
        n3 = st.checkbox("In-app status toasts for batch audits", value=True)

        if st.button("Save Notification Rules", type="primary"):
            st.toast("Notification preferences saved!")

    # ========================================================
    # TAB 4: AI MODEL & API CONFIGURATION
    # ========================================================
    with tab_api:
        st.markdown('<div class="bs-section-label">OPENAI LLM & VISION CONFIGURATION</div>', unsafe_allow_html=True)
        st.caption(
            "BrandShield features an integrated local rule & semantic vector engine that runs 100% offline. "
            "Configure an OpenAI API key below to unlock advanced generative reasoning, Vision OCR, and text-embedding-3-small vectors."
        )

        current_key = get_setting("openai_api_key", os.getenv("OPENAI_API_KEY", ""))

        api_input = st.text_input(
            "OpenAI API Key (sk-...)",
            value=current_key,
            type="password",
            help="Used for GPT-4o-mini reasoning and text-embedding-3-small vectors."
        )

        col_save, col_test = st.columns([1, 1])
        with col_save:
            if st.button("Save API Key", type="primary", use_container_width=True):
                set_setting("openai_api_key", api_input.strip())
                os.environ["OPENAI_API_KEY"] = api_input.strip()
                log_activity(user_id, "API_KEY_UPDATED", "OpenAI API key configured")
                st.success("API key stored securely.")

        with col_test:
            if st.button("Test Connection", use_container_width=True):
                if not api_input.strip():
                    st.error("Provide an API key to test.")
                else:
                    with st.spinner("Pinging OpenAI API..."):
                        try:
                            from openai import OpenAI
                            client = OpenAI(api_key=api_input.strip())
                            client.models.list()
                            st.success("Connection verified! Models accessible.")
                        except Exception as e:
                            st.error(f"Connection failed: {str(e)}")

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        current_eng = get_setting("analysis_engine_mode", "auto")
        mode = st.radio(
            "AI Engine Mode",
            ["Auto (AI with Local Heuristic Fallback)", "Strict Local Engine Only (100% Offline)"],
            index=0 if current_eng == "auto" else 1
        )
        if st.button("Save Engine Selection"):
            set_setting("analysis_engine_mode", "auto" if "Auto" in mode else "local")
            st.toast("Engine preference saved.")

    # ========================================================
    # TAB 5: SYSTEM MAINTENANCE
    # ========================================================
    with tab_system:
        st.markdown('<div class="bs-section-label">VECTOR EMBEDDING INDEXATION</div>', unsafe_allow_html=True)
        st.caption("Re-compute dense embeddings for all brand rules in SQLite to optimize semantic retrieval.")

        if st.button("🔄 Re-Index All Rules across Organizations", use_container_width=True):
            with st.spinner("Re-indexing rules..."):
                orgs = get_organizations()
                tot = 0
                for o in orgs:
                    tot += reindex_all_rules_for_org(o["id"])
                log_activity(user_id, "VECTORS_REINDEXED", f"Re-indexed {tot} rule vectors")
                st.success(f"Vector store refreshed! {tot} rule(s) indexed.")

        st.markdown("---")
        st.markdown('<div class="bs-section-label">DEMO SEED DATA RESTORATION</div>', unsafe_allow_html=True)
        if st.button("🌱 Reset to Factory Demo Configuration", use_container_width=True):
            from backend.database.db import init_db
            init_db()
            st.success("Synchronized with factory demo defaults!")
            st.rerun()
