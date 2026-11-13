import streamlit as st
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Initialize database schema and default seed data
from backend.database.db import init_db
init_db()

from auth.login import show_login
from auth.authentication import register_user, authenticate_user
from components.sidebar import show_sidebar
from views.dashboard import show_dashboard
from views.analysis import show_analysis
from views.profiles import show_brand_profiles
from views.guidelines import show_guidelines
from views.history import show_history
from views.reports import show_reports
from views.settings import show_settings

# -----------------------------------
# PAGE CONFIGURATION
# -----------------------------------
st.set_page_config(
    page_title="BrandShield | AI Brand Protection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------
# LOAD CSS
# -----------------------------------
css_path = Path(__file__).parent / "styles" / "style.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as file:
        custom_css = file.read()
    st.html(f"<style>{custom_css}</style>")

# -----------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "home"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

# -----------------------------------
# ANIMATED BACKGROUND EFFECTS
# -----------------------------------
st.markdown(
    """
    <div class="background-effects">
        <div class="glow glow-one"></div>
        <div class="glow glow-two"></div>
        <div class="grid-overlay"></div>
        <div class="orb orb-one"></div>
        <div class="orb orb-two"></div>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------
# AUTHENTICATED USER ROUTING
# -----------------------------------
if st.session_state.authenticated:
    # Ensure sidebar is expanded
    st.html("""
    <script>
        setTimeout(() => {
            const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
            if (sidebar && sidebar.getAttribute('aria-expanded') === 'false') {
                const btn = window.parent.document.querySelector('[data-testid="stSidebarCollapsedControl"] button, [data-testid="collapsedControl"] button, button[data-testid="stSidebarCollapsedControl"]');
                if (btn) btn.click();
            }
        }, 150);
    </script>
    """)
    show_sidebar()

    current_page = st.session_state.current_page

    if current_page == "dashboard":
        show_dashboard()
    elif current_page == "analysis":
        show_analysis()
    elif current_page == "profiles":
        show_brand_profiles()
    elif current_page == "guidelines":
        show_guidelines()
    elif current_page == "activity":
        show_history()
    elif current_page == "reports":
        show_reports()
    elif current_page == "settings":
        show_settings()
    else:
        show_dashboard()

    st.stop()

# -----------------------------------
# UNAUTHENTICATED / LANDING PAGE
# -----------------------------------
if st.session_state.auth_page == "home":
    st.html("""
    <div class="hero-container">
        <div class="brand-symbol">✦</div>
        <div class="brand-title">
            BRAND<span>SHIELD</span>
        </div>
        <div class="brand-line"></div>
        <div class="brand-tagline">
            PROTECT YOUR IDENTITY.
        </div>
        <div class="brand-description">
            Intelligent brand compliance.<br>
            Every asset. Every detail.
        </div>
        <div class="hero-caption">
            AI-POWERED BRAND INTELLIGENCE & COMPLIANCE GUARDIAN
        </div>
    </div>
    """)

    _, center_btn_col, _ = st.columns([1, 1.35, 1])
    with center_btn_col:
        b1, b2 = st.columns(2, gap="medium")
        with b1:
            if st.button("SIGN IN", use_container_width=True, type="primary"):
                st.session_state.auth_page = "signin"
                st.rerun()
        with b2:
            if st.button("CREATE ACCOUNT", use_container_width=True):
                st.session_state.auth_page = "signup"
                st.rerun()

# -----------------------------------
# SIGN IN PAGE
# -----------------------------------
elif st.session_state.auth_page == "signin":
    _, auth_center, _ = st.columns([1, 1.25, 1])
    with auth_center:
        show_login()
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        if st.button("← Back to Welcome", use_container_width=True):
            st.session_state.auth_page = "home"
            st.rerun()

# -----------------------------------
# SIGN UP PAGE
# -----------------------------------
elif st.session_state.auth_page == "signup":
    _, signup_center, _ = st.columns([1, 1.25, 1])
    with signup_center:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 22px;">
                <div class="auth-brand-badge">✦ BRANDSHIELD</div>
                <h1 style="color: #FAF7FF; font-size: 28px; font-weight: 850; margin: 4px 0 6px;">Create Account</h1>
                <p style="color: #B4A6C8; font-size: 14px; margin: 0;">Start protecting your brand identity with intelligent AI compliance.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form("landing_signup_form"):
            name = st.text_input("Full name", placeholder="Your Name")
            email = st.text_input("Email address", placeholder="name@company.com")
            password = st.text_input("Create password", type="password")
            confirm = st.text_input("Confirm password", type="password")

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "CREATE ACCOUNT",
                use_container_width=True,
                type="primary"
            )

            if submitted:
                if password != confirm:
                    st.error("Passwords do not match.")
                else:
                    success, message = register_user(name, email, password)
                    if success:
                        st.success(message + " You can now sign in.")
                        st.session_state.auth_page = "signin"
                        st.rerun()
                    else:
                        st.error(message)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        if st.button("← Back to Welcome", use_container_width=True):
            st.session_state.auth_page = "home"
            st.rerun()
