# components/helpers.py
import os
import requests
import PyPDF2
import docx

# Hugging Face API Config
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
PARAPHRASER_URL = "https://api-inference.huggingface.co/models/Vamsi/T5_Paraphrase_Paws"
headers = {"Authorization": f"Bearer {HUGGING_FACE_API_KEY}"}


# =============== Paraphraser =================
def paraphrase_text(text, num_return_sequences=3, max_length=128):
    """Generate paraphrased sentences using Hugging Face API."""
    payload = {
        "inputs": f"paraphrase: {text}",
        "parameters": {
            "num_return_sequences": num_return_sequences,
            "max_length": max_length,
        },
    }
    response = requests.post(PARAPHRASER_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return [r["generated_text"] for r in response.json()]
    else:
        return [f"Error: {response.text}"]


# =============== File Handlers =================
def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()


def extract_text_from_docx(uploaded_file):
    doc = docx.Document(uploaded_file)
    text = "\n".join([p.text for p in doc.paragraphs if p.text])
    return text.strip()


def extract_text_from_txt(uploaded_file):
    return uploaded_file.read().decode("utf-8").strip()


def handle_file_upload(uploaded_file):
    """Handle text extraction from different file formats."""
    if uploaded_file.type == "text/plain":
        return extract_text_from_txt(uploaded_file)
    elif uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]:
        return extract_text_from_docx(uploaded_file)
    else:
        return ""
