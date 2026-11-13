import streamlit as st
from datetime import datetime
from backend.database.db import (
    get_organizations,
    get_dashboard_metrics,
    get_recent_activity,
    get_organization_by_id
)

def show_dashboard():
    # -----------------------------------------
    # USER & ORG DETAILS
    # -----------------------------------------
    user = st.session_state.get("user") or {}
    user_name = user.get("name", "User")

    organizations = get_organizations()
    st.session_state.organizations = organizations

    if not organizations:
        active_org = None
        active_org_id = None
        selected_org = "No organization selected"
    else:
        active_org_id = st.session_state.get("active_org_id")
        if not active_org_id or not any(o["id"] == active_org_id for o in organizations):
            active_org_id = organizations[0]["id"]
            st.session_state.active_org_id = active_org_id

        active_org = next((o for o in organizations if o["id"] == active_org_id), organizations[0])
        selected_org = active_org["name"]
        st.session_state.active_organization = selected_org

    org_count = len(organizations)

    # -----------------------------------------
    # HEADER
    # -----------------------------------------
    st.markdown(
        f"""
        <div class="bs-dashboard-header">
            <div>
                <div class="bs-eyebrow">BRAND PROTECTION WORKSPACE</div>
                <h1>Welcome back, {user_name}.</h1>
                <p>Your brand intelligence command centre.</p>
            </div>
            <div class="bs-header-date">
                {datetime.now().strftime("%d %B %Y")}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------------------
    # ACTIVE BRAND PROFILE
    # -----------------------------------------
    st.markdown('<div class="bs-section-label">ACTIVE BRAND PROFILE</div>', unsafe_allow_html=True)

    brand_col, status_col = st.columns([3, 1])

    with brand_col:
        if organizations:
            org_names = [o["name"] for o in organizations]
            curr_index = org_names.index(selected_org) if selected_org in org_names else 0

            chosen_name = st.selectbox(
                "Select active organization",
                org_names,
                index=curr_index,
                label_visibility="collapsed",
                key="dash_org_picker_main"
            )

            if chosen_name != selected_org:
                matched_org = next(o for o in organizations if o["name"] == chosen_name)
                st.session_state.active_org_id = matched_org["id"]
                st.session_state.active_organization = chosen_name
                st.rerun()

            # Color palette & tone tag
            if active_org:
                p_c = active_org.get('primary_color', '#8955D9')
                s_c = active_org.get('secondary_color', '#D0B7FF')
                a_c = active_org.get('accent_color', '#100C18')
                tone = active_org.get('tone_of_voice', 'Professional, Authoritative')
                st.markdown(
                    f"""
                    <div style="margin-top: 8px; display: flex; align-items: center; gap: 14px; font-size: 13px; color: #B4A6C8;">
                        <span>Voice: <strong style="color: #FAF7FF;">{tone}</strong></span>
                        <span>•</span>
                        <span style="display: flex; align-items: center; gap: 6px;">Palette: 
                            <span style="width: 16px; height: 16px; border-radius: 4px; background: {p_c}; display: inline-block;" title="{p_c}"></span>
                            <span style="width: 16px; height: 16px; border-radius: 4px; background: {s_c}; display: inline-block;" title="{s_c}"></span>
                            <span style="width: 16px; height: 16px; border-radius: 4px; background: {a_c}; display: inline-block;" title="{a_c}"></span>
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                """
                <div class="bs-brand-empty">
                    <div class="bs-empty-icon">✦</div>
                    <div>
                        <h3>No brand profile connected yet</h3>
                        <p>Create a company profile and upload its brand guidelines to start monitoring compliance.</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    with status_col:
        st.markdown(
            """
            <div class="bs-system-status">
                <span class="bs-status-dot"></span>
                SYSTEM STATUS
                <strong>Ready</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height: 22px'></div>", unsafe_allow_html=True)

    # -----------------------------------------
    # COMPLIANCE OVERVIEW METRICS
    # -----------------------------------------
    st.markdown('<div class="bs-section-label">COMPLIANCE OVERVIEW</div>', unsafe_allow_html=True)

    metrics_data = get_dashboard_metrics(active_org_id)
    assets_val = str(metrics_data["assets_analysed"])
    score_val = f"{metrics_data['compliance_score']}%"
    violations_val = str(metrics_data["violations_found"])
    profiles_val = str(org_count)

    metrics = [
        ("ASSETS ANALYSED", assets_val, "Total content reviews"),
        ("COMPLIANCE SCORE", score_val, "Average brand health"),
        ("VIOLATIONS FOUND", violations_val, "Issues requiring attention"),
        ("BRAND PROFILES", profiles_val, "Configured organizations"),
    ]

    metric_cols = st.columns(4)
    for col, (label, value, description) in zip(metric_cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="bs-metric-card">
                    <div class="bs-metric-label">{label}</div>
                    <div class="bs-metric-value">{value}</div>
                    <div class="bs-metric-description">{description}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)

    # -----------------------------------------
    # START WORKING (THE TWO SIGNATURE ACTION CARDS)
    # -----------------------------------------
    st.markdown('<div class="bs-section-label">START WORKING</div>', unsafe_allow_html=True)

    action1, action2 = st.columns(2, gap="large")

    with action1:
        st.markdown(
            """
            <div class="bs-action-card">
                <div class="bs-action-icon">⌁</div>
                <div class="bs-action-tag">CONTENT INTELLIGENCE</div>
                <h3>Analyse Content</h3>
                <p>Review marketing copy, advertisements, posters and creative assets for brand guideline violations.</p>
                <div class="bs-action-footer">TEXT & VISUAL ANALYSIS →</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Start analysis",
            key="dashboard_start_analysis",
            use_container_width=True,
            type="primary"
        ):
            st.session_state.current_page = "analysis"
            st.rerun()

    with action2:
        st.markdown(
            """
            <div class="bs-action-card">
                <div class="bs-action-icon">✦</div>
                <div class="bs-action-tag">BRAND INTELLIGENCE</div>
                <h3>Manage Guidelines</h3>
                <p>Configure company profiles, upload brand rulebooks, reference logos, approved colours and brand requirements.</p>
                <div class="bs-action-footer">MANAGE BRAND PROFILES →</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Open guidelines",
            key="dashboard_open_guidelines",
            use_container_width=True
        ):
            st.session_state.current_page = "guidelines"
            st.rerun()

    st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)

    # -----------------------------------------
    # RECENT ACTIVITY
    # -----------------------------------------
    st.markdown('<div class="bs-section-label">RECENT ACTIVITY</div>', unsafe_allow_html=True)

    activity = get_recent_activity(active_org_id, limit=5)

    if activity:
        for item in activity:
            desc = item.get("description", "Content analysis")
            org_name = item.get("org_name", selected_org)
            date_str = item.get("created_at", "")[:16]
            status_text = item.get("action_type", "Completed")

            st.markdown(
                f"""
                <div class="bs-activity-row">
                    <div>
                        <strong>{desc}</strong>
                        <p>{org_name} · {date_str}</p>
                    </div>
                    <span class="bs-activity-status">
                        {status_text}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            """
            <div class="bs-activity-empty">
                <div class="bs-empty-icon">◷</div>
                <h3>Your activity will appear here</h3>
                <p>Once you analyse your first asset, its results and compliance history will be displayed here.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
