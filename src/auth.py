# src/auth.py
from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Missing Supabase credentials in settings.py")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def register_user(email: str, password: str):
    """Register new user with email verification."""
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
