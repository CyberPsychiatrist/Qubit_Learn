# components/paraphraser.py

import streamlit as st
from src.ai_processor import paraphrase_text


def render_paraphraser():
    """
    Paraphraser page UI.
    Lets user input text and generate paraphrases using ai_processor
    with support for model switching.
    """
    st.title("📝 Paraphraser")

    # Input text
    text = st.text_area(
        "Enter text to paraphrase",
        height=150,
        placeholder="Type or paste text here...",
    )

    # Sidebar options
    st.sidebar.header("Paraphraser Options")
    num_variants = st.sidebar.slider("Number of paraphrases", 1, 5, 3)
    max_tokens = st.sidebar.slider("Max new tokens", 32, 256, 96, step=16)

    model_choice = st.sidebar.selectbox(
        "Choose paraphrasing model",
        options=["pegasus", "t5", "flan"],
        index=0,
        help=(
            "pegasus = high quality\n"
            "t5 = efficient, newer model\n"
            "flan = general-purpose fallback"
        ),
    )

    if st.button("Paraphrase", type="primary"):
        if not text.strip():
            st.warning("Please enter some text.")
            return

        with st.spinner(
            f"Generating {num_variants} paraphrase(s) using {model_choice} model..."
        ):
            results = paraphrase_text(
                text,
                num_return_sequences=num_variants,
                max_new_tokens=max_tokens,
                model_choice=model_choice,
            )

        st.subheader("Paraphrases")
        for idx, r in enumerate(results, start=1):
            st.markdown(f"**{idx}.** {r}")
