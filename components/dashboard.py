# components/dashboard.py
import streamlit as st
from src.database import get_user_flashcards, get_user_data, save_flashcards, update_user_profile
from src.ai_processor import generate_questions, paraphrase_text
from components.upload_section import render_upload_section
from components.donate import render_donate_tab

# -------------------- FLASHCARDS --------------------
def generate_flashcards(passage: str):
    questions = generate_questions(passage)
    return [{"question": q, "answer": "Answer TBD"} for q in questions]

def display_flashcards(user_id):
    st.subheader("🧠 Your Flashcards")
    flashcards = get_user_flashcards(user_id)

    if isinstance(flashcards, dict) and "error" in flashcards:
        st.error(f"Error loading flashcards: {flashcards['error']}")
        return

    if flashcards:
        for card in flashcards:
            with st.expander(card["question"]):
                st.write(card["answer"])
    else:
        st.info("No flashcards available.")

    # Add flashcard manually
    st.subheader("➕ Add Flashcard")
    q = st.text_input("Question")
    a = st.text_input("Answer")
    if st.button("Save Flashcard"):
        if q and a:
            save_flashcards([{"question": q, "answer": a}], user_id)
            st.success("Flashcard added successfully!")
            st.rerun()
        else:
            st.warning("Please fill both fields.")

# -------------------- STUDY TIMER --------------------
def study_timer():
    st.subheader("⏱ Study Timer")
    if "study_time" not in st.session_state:
        st.session_state.study_time = 0

    if st.button("➕ Add 5 minutes"):
        st.session_state.study_time += 5

    if st.button("➖ Subtract 5 minutes"):
        st.session_state.study_time = max(0, st.session_state.study_time - 5)

    st.write(f"Time spent studying: {st.session_state.study_time} minutes")

# -------------------- USER PROFILE --------------------
def user_profile(user_id):
    st.subheader("👤 User Profile")
    user = get_user_data(user_id)

    if isinstance(user, dict) and "error" in user:
        st.error(f"Unable to load profile: {user['error']}")
        return

    st.write(f"Name: {user.get('name', 'N/A')}")
    st.write(f"Email: {user.get('email', 'N/A')}")
    st.write(f"Member since: {user.get('registration_date', 'N/A')}")

    new_name = st.text_input("Edit Name", user.get("name", ""))
    new_email = st.text_input("Edit Email", user.get("email", ""))
    if st.button("Save Profile"):
        profile_data = {"name": new_name, "email": new_email}
        result = update_user_profile(user_id, profile_data)
        if isinstance(result, dict) and "error" in result:
            st.error(f"Update failed: {result['error']}")
        else:
            st.success("Profile updated successfully!")

# -------------------- MAIN DASHBOARD --------------------
def render_dashboard(user: dict):
    st.title(f"📚 Welcome, {user.get('email', 'Learner')}")

    tab1, tab2, tab3, tab4, tab5, tab6 ,tab7 = st.tabs([
        "📄 Upload",
        "✍️ Paraphrasing",
        "❓ Question Generator",
        "🧠 Flashcards",
        "⏱ Study Timer",
        "👤 Profile",
        "💝 Donate"
    ])

    # Upload
    with tab1:
        render_upload_section()

    # Paraphrasing
    with tab2:
        st.subheader("Paraphrase Text")
        text = st.text_area("Enter text to paraphrase")
        if st.button("Paraphrase"):
            if text.strip():
                results = paraphrase_text(text)
                for r in results:
                    st.write(f"- {r}")
            else:
                st.warning("Please enter text to paraphrase.")

    # Question Generator
    with tab3:
        st.subheader("Generate Questions")
        passage = st.text_area("Enter a passage")
        if st.button("Generate Questions"):
            if passage.strip():
                questions = generate_questions(passage)
                for q in questions:
                    st.write(f"- {q}")
            else:
                st.warning("Please enter a passage.")

    # Flashcards
    with tab4:
        display_flashcards(user.get("id"))

    # Study Timer
    with tab5:
        study_timer()

    # Profile
    with tab6:
        user_profile(user.get("id"))

    # Donate
    with tab7:
        render_donate_tab(user.get("email"))

    # Sidebar
    st.sidebar.success("✅ You are logged in")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user = {}
        st.rerun()
