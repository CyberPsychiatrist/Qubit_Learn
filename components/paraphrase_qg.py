# components/paraphrase_qg.py

import streamlit as st
import pandas as pd


def render_paraphrase_qg():
    """
    Paraphrase & Question Generation page.
    - Lets users upload a document (.txt/.pdf/.docx)
    - Extracts text
    - Paraphrases + generates questions via ai_processor (through helpers)
    - Allows user to edit/select rows, download CSV
    - (Optional) Save to DB if services.db_client is available
    """

    st.title("📘 Paraphrase & Question Generation")

    # Lazy imports so the app doesn't break at module import time
    try:
        from components.helpers import (
            handle_file_upload,
            paraphrase_text_from_api,
            generate_questions_from_api,
        )
    except Exception as e:
        st.error(
            "Paraphrase/QG helpers are not available or failed to import.\n\n"
            f"Details: {e}\n\n"
            "Make sure components/helpers.py exports "
            "`handle_file_upload`, `paraphrase_text_from_api`, and `generate_questions_from_api`."
        )
        return

    # Optional DB client (only used if present)
    db_available = True
    try:
        from services.db_client import insert_cards, current_user_id_from_session
    except Exception:
        db_available = False

    uploaded_file = st.file_uploader("Upload a document", type=["txt", "pdf", "docx"])
    if not uploaded_file:
        st.info("Please upload a file to begin.")
        return

    # Extract text from file
    text = handle_file_upload(uploaded_file)
    if not text:
        st.error("Could not extract text from this file. Try a different file or format.")
        return

    with st.expander("Preview", expanded=False):
        st.text_area("Extracted text (first 1000 chars)", text[:1000], height=180)

    with st.expander("Options", expanded=False):
        num_paraphrases = st.slider("Paraphrases to generate", 1, 5, 3)
        max_questions = st.slider("Questions to generate", 1, 10, 5)

    # Generate
    if st.button("Paraphrase & Generate Questions", type="primary"):
        with st.spinner("Talking to Hugging Face…"):
            try:
                paraphrases = paraphrase_text_from_api(text, num_return_sequences=num_paraphrases)
            except Exception as e:
                st.error(f"Paraphrase error: {e}")
                paraphrases = []

            try:
                questions = generate_questions_from_api(text, max_questions=max_questions)
            except Exception as e:
                st.error(f"Question generation error: {e}")
                questions = []

        if not paraphrases and not questions:
            st.warning("No output generated.")
            return

        # Build editable table (pair questions with paraphrases for convenience)
        rows = []
        if questions:
            for i, q in enumerate(questions):
                ans = paraphrases[i % len(paraphrases)] if paraphrases else ""
                rows.append({"save": True, "question": q, "answer": ans})
        else:
            # If no questions were generated, still display paraphrases for export
            for p in paraphrases:
                rows.append({"save": False, "question": "", "answer": p})

        df = pd.DataFrame(rows, columns=["save", "question", "answer"])
        st.caption("Tip: you can edit any cells below before saving.")
        edited = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="pqg_editor")

        st.download_button(
            "Download CSV",
            data=edited.to_csv(index=False),
            file_name="paraphrase_questions.csv",
            mime="text/csv",
        )

        st.markdown("---")
        st.subheader("Save to Flashcards")

        if not db_available:
            st.info(
                "Database client not found. To enable saving, add `services/db_client.py` "
                "with `insert_cards` and `current_user_id_from_session`."
            )
            return

        if st.button("Save selected rows to `cards`"):
            selected = edited[edited["save"] == True]  # noqa: E712
            payload = []
            user_id = current_user_id_from_session()

            for _, r in selected.iterrows():
                item = {
                    "question": str(r.get("question", "")).strip(),
                    "answer": str(r.get("answer", "")).strip(),
                }
                if user_id:
                    item["created_by"] = user_id
                if item["question"] and item["answer"]:
                    payload.append(item)

            if not payload:
                st.warning("No valid rows selected (need both question and answer).")
                return

            with st.spinner("Saving to database…"):
                ok, data = insert_cards(payload)

            if ok:
                st.success(f"Saved {len(payload)} flashcards ✅")
                if data:
                    st.json(data)
            else:
                st.error("Failed to save flashcards.")
                st.code(str(data))
