import streamlit as st

def render_metric_card(label, value, description=""):
    """Renders a single metric card matching BrandShield UI styles."""
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

def render_metric_grid(metrics):
    """
    Renders a row of metric cards.
    metrics is a list of tuples: (label, value, description)
    """
    cols = st.columns(len(metrics))
    for col, (label, val, desc) in zip(cols, metrics):
        with col:
            render_metric_card(label, val, desc)
