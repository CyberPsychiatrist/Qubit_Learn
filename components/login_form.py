# components/login_form.py
import streamlit as st
from src.auth import login_user, register_user, supabase

def render_login_form():
    st.subheader("🔑 Login")

    # Warn if Supabase is not configured
    if supabase is None:
        st.error("⚠️ Supabase is not configured. Login is currently disabled. Please contact the administrator.")
        return  # Stop rendering the login form

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        user = login_user(email, password)

        if not user:
            st.error("❌ Login failed. Please try again.")
        elif "error" in user:
            st.error(f"⚠️ {user['error']}")
        elif "id" in user:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("❌ Invalid credentials or email not verified.")


def render_register_form():
    st.subheader("📝 Register")

    # Warn if Supabase is not configured
    if supabase is None:
        st.error("⚠️ Supabase is not configured. Registration is currently disabled. Please contact the administrator.")
        return  # Stop rendering the register form

    email = st.text_input("Email", key="register_email")
    password = st.text_input("Password", type="password", key="register_password")

    if st.button("Register"):
        response = register_user(email, password)

        if not response:
            st.error("❌ Registration failed. Please try again.")
        elif "error" in response:
            st.error(f"⚠️ {response['error']}")
        elif "id" in response:
            st.success("📧 Verification email sent! Please check your inbox.")
        else:
            st.error("❌ Registration could not be completed.")
