import streamlit as st
from auth.authentication import register_user, authenticate_user

def show_login():
    if st.session_state.get("authenticated", False):
        return

    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 22px;">
            <div class="auth-brand-badge">✦ BRANDSHIELD</div>
            <h1 style="color: #FAF7FF; font-size: 28px; font-weight: 850; margin: 4px 0 6px;">Welcome Back</h1>
            <p style="color: #B4A6C8; font-size: 14px; margin: 0;">Sign in to your brand compliance command centre.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    login_tab, signup_tab = st.tabs(["🔐 Sign In", "✨ Create Account"])

    # SIGN IN TAB
    with login_tab:
        with st.form("login_form"):
            email = st.text_input(
                "Email address",
                value="demo@brandshield.ai",
                placeholder="name@company.com",
                key="demo_email"
            )
            password = st.text_input(
                "Password",
                value="BSdemo@2026",
                type="password",
                placeholder="Enter your password",
                key="demo_password"
            )

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            login_clicked = st.form_submit_button(
                "SIGN IN TO WORKSPACE →",
                use_container_width=True,
                type="primary"
            )

            if login_clicked:
                user = authenticate_user(email, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Incorrect email or password. Please try again.")

        st.markdown(
            """
            <div style="background: rgba(137, 85, 217, 0.12); border: 1px solid rgba(167, 139, 250, 0.2); border-radius: 8px; padding: 10px 14px; margin-top: 14px; text-align: center; font-size: 12px; color: #D0B7FF;">
                <strong>Demo Access:</strong> <code>demo@brandshield.ai</code> · <code>BSdemo@2026</code>
            </div>
            """,
            unsafe_allow_html=True
        )

    # CREATE ACCOUNT TAB
    with signup_tab:
        with st.form("signup_form"):
            name = st.text_input("Full name", placeholder="Your Name")
            email = st.text_input("Email address", placeholder="name@company.com", key="signup_email")
            password = st.text_input("Create password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm password", type="password", key="signup_confirm_password")

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            signup_clicked = st.form_submit_button(
                "CREATE MY ACCOUNT",
                use_container_width=True,
                type="primary"
            )

            if signup_clicked:
                if password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, message = register_user(name, email, password)
                    if success:
                        st.success(message + " You can now sign in using the 'Sign In' tab above.")
                    else:
                        st.error(message)
