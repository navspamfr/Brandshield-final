import streamlit as st
from datetime import datetime

def render_view_header(eyebrow, title, subtitle, show_date=True):
    """Renders a standard BrandShield view header matching style.css."""
    date_html = f'<div class="bs-header-date">{datetime.now().strftime("%d %B %Y")}</div>' if show_date else ""
    st.markdown(
        f"""
        <div class="bs-dashboard-header">
            <div>
                <div class="bs-eyebrow">{eyebrow}</div>
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
            {date_html}
        </div>
        """,
        unsafe_allow_html=True
    )
