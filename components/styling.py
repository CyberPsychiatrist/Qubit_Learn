import streamlit as st
import base64

def set_background(image_path: str):
    """Set a local image as background for the page."""
    try:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{encoded}");
                background-attachment: fixed;
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.warning(f"Background image not found: {image_path}")

def set_widget_style():
    """Improve readability of widgets on top of background."""
    st.markdown(
        """
        <style>
        .stTextInput, .stButton>button, .stSelectbox, .stTextArea {
            background-color: rgba(255, 255, 255, 0.85) !important;
            color: black !important;
            border-radius: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
