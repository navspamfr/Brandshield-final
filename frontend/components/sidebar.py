import streamlit as st
from backend.database.db import get_organizations

def show_sidebar():
    with st.sidebar:
        # Brand Logo Header
        st.markdown(
            """
            <div class="sidebar-brand">
                <span>✦</span> BRANDSHIELD
            </div>
            """,
            unsafe_allow_html=True
        )

        user = st.session_state.get("user") or {}
        user_name = user.get("name", "User")
        user_role = user.get("role", "admin").upper()

        # User profile chip
        st.markdown(
            f"""
            <div style="background: rgba(26, 18, 44, 0.6); border: 1px solid rgba(167, 139, 250, 0.15); border-radius: 10px; padding: 10px 14px; margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-size: 13px; font-weight: 700; color: #FAF7FF;">{user_name}</div>
                    <div style="font-size: 10.5px; color: #A78BFA; letter-spacing: 0.5px;">{user_role}</div>
                </div>
                <div class="bs-status-dot" title="AI Guardian Online"></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Quick Organization Switcher in Sidebar
        orgs = get_organizations()
        if orgs:
            active_id = st.session_state.get("active_org_id", orgs[0]["id"])
            org_options = {o["id"]: o["name"] for o in orgs}
            
            # Ensure active_id is in options
            if active_id not in org_options:
                active_id = orgs[0]["id"]
                st.session_state.active_org_id = active_id

            current_idx = list(org_options.keys()).index(active_id)
            selected_id = st.selectbox(
                "Active Brand Profile",
                options=list(org_options.keys()),
                format_func=lambda x: org_options[x],
                index=current_idx,
                label_visibility="collapsed",
                key="sidebar_org_selector"
            )
            if selected_id != st.session_state.get("active_org_id"):
                st.session_state.active_org_id = selected_id
                st.session_state.active_organization = org_options[selected_id]
                st.rerun()

        st.caption("CORE WORKSPACE")

        current_page = st.session_state.get("current_page", "dashboard")

        def nav_btn(label, target_page, icon=""):
            is_active = (current_page == target_page)
            display_label = f"{icon}  {label}" if icon else label
            # Add subtle visual indicator if active
            btn_type = "primary" if is_active else "secondary"
            if st.button(display_label, use_container_width=True, key=f"nav_{target_page}", type=btn_type):
                st.session_state.current_page = target_page
                st.rerun()

        nav_btn("Dashboard", "dashboard", "⌂")
        nav_btn("Content Analysis", "analysis", "⚡")
        nav_btn("Brand Profiles", "profiles", "🏢")
        nav_btn("Guidelines & Rules", "guidelines", "▤")
        nav_btn("Activity History", "activity", "◷")
        nav_btn("Compliance Reports", "reports", "📑")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        st.caption("PREFERENCES")

        nav_btn("Settings", "settings", "⚙")

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("↪  Sign Out", use_container_width=True, key="nav_logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.auth_page = "home"
            st.session_state.current_page = "dashboard"
            st.rerun()
