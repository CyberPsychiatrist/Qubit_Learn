import streamlit as st
from src.database import get_user_flashcards

def render_flashcards():
    st.subheader("Your Flashcards")

    if 'user_id' in st.session_state:
        flashcards = get_user_flashcards(st.session_state.user_id)
        
        if flashcards:
            for card in flashcards:
                with st.expander(card["question"]):
                    st.write(card["answer"])
        else:
            st.info("No flashcards yet. Generate some from your study material!")
    else:
        st.warning("Please log in to view your flashcards")
