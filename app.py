# app.py
import streamlit as st
from components.login_form import render_login_form, render_register_form
from components.dashboard import render_dashboard
from components.paraphrase_qg import render_paraphrase_qg   # ✅ already added earlier
from components.paraphraser import render_paraphraser       # ✅ new import


# -------------------- APP ENTRY --------------------
def main():
    st.set_page_config(page_title="Qubit Learn", layout="wide")

    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = {}

    # Navigation menu
    menu = ["Login", "Register", "Dashboard", "Paraphrase", "Paraphrase & QG"]

    if st.session_state.authenticated:
        # Show only Dashboard + Paraphrase pages when logged in
        choice = st.sidebar.selectbox("Navigation", menu[2:])
    else:
        # Only Login + Register when not logged in
        choice = st.sidebar.selectbox("Navigation", menu[:2])

    # Routing
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

    elif choice == "Paraphrase":
        if st.session_state.authenticated and st.session_state.user:
            render_paraphraser()
        else:
            st.warning("Please log in to use the paraphraser.")
            render_login_form()

    elif choice == "Paraphrase & QG":
        if st.session_state.authenticated and st.session_state.user:
            render_paraphrase_qg()
        else:
            st.warning("Please log in to access Paraphrase & QG.")
            render_login_form()


if __name__ == "__main__":
    main()
