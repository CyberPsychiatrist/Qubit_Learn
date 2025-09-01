# src/auth.py
from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("⚠️ Warning: Missing Supabase credentials. Authentication features will be disabled.")


def register_user(email: str, password: str):
    """Register new user with email verification."""
    if not supabase:
        return {"error": "Supabase not configured. Please check credentials in settings.py or Streamlit secrets."}
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        if response.user:
            return {"id": response.user.id, "email": response.user.email}
        return None
    except Exception as e:
        return {"error": str(e)}


def login_user(email: str, password: str):
    """Log in user if email is verified."""
    if not supabase:
        return {"error": "Supabase not configured. Please check credentials in settings.py or Streamlit secrets."}
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response.user:
            return {"id": response.user.id, "email": response.user.email}
        return None
    except Exception as e:
        return {"error": str(e)}
