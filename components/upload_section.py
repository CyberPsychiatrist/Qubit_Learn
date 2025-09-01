# components/upload_section.py
import streamlit as st
import docx
import PyPDF2
from src.ai_processor import paraphrase_text

def read_file(file):
    """Read uploaded file content based on file type."""
    content = ""
    if file.type == "text/plain":
        content = file.read().decode("utf-8")
    elif file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            content += page.extract_text() or ""
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(file)
        for para in doc.paragraphs:
            content += para.text + "\n"
    else:
        st.error("❌ Unsupported file format. Please upload TXT, PDF, or DOCX.")
    return content

def render_upload_section():
    """Render upload section with paraphrasing option."""
    st.subheader("📄 Upload a File")

    uploaded_file = st.file_uploader("Upload TXT, PDF, or DOCX", type=["txt", "pdf", "docx"])

    if uploaded_file:
        file_text = read_file(uploaded_file)

        if file_text.strip():
            st.text_area("Extracted Text", file_text, height=200)

            if st.button("Paraphrase Uploaded Text"):
                with st.spinner("Paraphrasing..."):
                    results = paraphrase_text(file_text[:2000])  # Limit length
                    for r in results:
                        st.write(f"- {r}")
        else:
            st.warning("No text could be extracted from the file.")
