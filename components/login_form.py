# components/login_form.py
import streamlit as st
from src.auth import login_user, register_user

def render_login_form():
    st.subheader("🔑 Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        user = login_user(email, password)
        if user and "id" in user:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials or email not verified.")

def render_register_form():
    st.subheader("📝 Register")
    email = st.text_input("Email", key="register_email")
    password = st.text_input("Password", type="password", key="register_password")

    if st.button("Register"):
        response = register_user(email, password)
        if response and "id" in response:
            st.success("📧 Verification email sent! Please check your inbox.")
        else:
            st.error("Registration failed. Try again.")
