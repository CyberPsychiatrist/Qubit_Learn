# app.py
import streamlit as st
from components.login_form import render_login_form, render_register_form
from components.dashboard import render_dashboard

# -------------------- APP ENTRY --------------------
def main():
    st.set_page_config(page_title="Qubit Learn", layout="wide")

    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = {}

    # Navigation
    menu = ["Login", "Register", "Dashboard"]
    if st.session_state.authenticated:
        choice = "Dashboard"
    else:
        choice = st.sidebar.selectbox("Navigation", menu[:-1])  # no Dashboard if not logged in

    # Pages
    if choice == "Login":
        render_login_form()

    elif choice == "Register":
        render_register_form()

    elif choice == "Dashboard":
        if st.session_state.authenticated and st.session_state.user:
            render_dashboard(st.session_state.user)
        else:
            st.warning("Please log in to access your dashboard.")
            render_login_form()


if __name__ == "__main__":
    main()
