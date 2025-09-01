# components/helpers.py
import PyPDF2
import docx
from src.ai_processor import paraphrase_text, generate_questions


# =============== Paraphraser =================
def paraphrase_text_from_api(text: str, num_return_sequences: int = 3, max_length: int = 128):
    """Generate paraphrases using ai_processor."""
    return paraphrase_text(text, num_return_sequences=num_return_sequences, max_new_tokens=max_length)


def generate_questions_from_api(text: str, max_questions: int = 5, max_new_tokens: int = 96):
    """Generate questions using ai_processor."""
    return generate_questions(text, max_questions=max_questions, max_new_tokens=max_new_tokens)


# =============== File Handlers =================
def extract_text_from_pdf(uploaded_file) -> str:
    reader = PyPDF2.PdfReader(uploaded_file)
    return "".join([page.extract_text() or "" for page in reader.pages]).strip()


def extract_text_from_docx(uploaded_file) -> str:
    doc = docx.Document(uploaded_file)
    return "\n".join([p.text for p in doc.paragraphs if p.text]).strip()


def extract_text_from_txt(uploaded_file) -> str:
    return uploaded_file.read().decode("utf-8").strip()


def handle_file_upload(uploaded_file) -> str:
    """Handle text extraction from txt, pdf, and docx files."""
    if uploaded_file.type == "text/plain":
        return extract_text_from_txt(uploaded_file)
    elif uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]:
        return extract_text_from_docx(uploaded_file)
    return ""
