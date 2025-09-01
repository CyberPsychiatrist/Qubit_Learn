# config/settings.py
import os
from dotenv import load_dotenv

# Try loading .env file (works in local dev)
load_dotenv()

try:
    import streamlit as st
    # Try reading from Streamlit secrets if available
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY"))
    HUGGING_FACE_API_KEY = st.secrets.get("HUGGING_FACE_API_KEY", os.getenv("HUGGING_FACE_API_KEY"))
except Exception:
    # Fallback if not running inside Streamlit
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")

# Application metadata
APP_TITLE = "QuBit_Learn"
APP_VERSION = "1.0.0"
