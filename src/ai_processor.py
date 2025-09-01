# src/ai_processor.py

from __future__ import annotations

import os
import requests
from typing import List, Dict, Any, Optional

# 👉 Make sure you have src/settings.py with HUGGING_FACE_API_KEY defined
# If not, we'll also check environment variables at runtime.
try:
    from config.settings import HUGGING_FACE_API_KEY as _HF_TOKEN_FROM_SETTINGS  # optional
except Exception:
    _HF_TOKEN_FROM_SETTINGS = None

# --- Model IDs (Inference API) ---
PARAPHRASE_PRIMARY = "https://api-inference.huggingface.co/models/tuner007/pegasus_paraphrase"       # text2text-generation
PARAPHRASE_FALLBACK = "google/flan-t5-base"             # text2text-generation
QG_MODEL = "https://api-inference.huggingface.co/models/iarfmoose/t5-base-question-generator"                        # text2text-generation

# --- HTTP ---
_DEFAULT_TIMEOUT = 45


def _get_hf_token() -> Optional[str]:
    """
    Resolve the token safely:
    1) ENV: HUGGING_FACE_API_KEY or HF_TOKEN
    2) src.settings.HUGGING_FACE_API_KEY if present
    3) streamlit secrets (if running in Streamlit), but only when available
    """
    token = os.getenv("HUGGING_FACE_API_KEY") or os.getenv("HF_TOKEN") or _HF_TOKEN_FROM_SETTINGS
    if token:
        return token

    # Try streamlit secrets without importing at module level
    try:
        import streamlit as st  # local import to avoid ImportError in tests
        token = st.secrets.get("HUGGING_FACE_API_KEY")  # type: ignore[attr-defined]
    except Exception:
        token = None

    return token


def _hf_text2text(model_id: str, prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Call the Hugging Face Inference API for text2text-generation models.
    Returns a dict: {"ok": bool, "data": Any, "status": int}
    """
    token = _get_hf_token()
    if not token:
        return {"ok": False, "data": "Hugging Face API key is missing.", "status": 0}

    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {token}"}

    payload: Dict[str, Any] = {"inputs": prompt}
    if params:
        payload["parameters"] = params

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=_DEFAULT_TIMEOUT)
        status = resp.status_code

        if status == 503:
            return {"ok": False, "data": "Model is loading on Hugging Face. Please try again in a few seconds.", "status": status}

        if status >= 400:
            return {"ok": False, "data": getattr(resp, "text", "") or resp.json(), "status": status}

        data = resp.json()
        return {"ok": True, "data": data, "status": status}

    except requests.Timeout:
        return {"ok": False, "data": "Request to Hugging Face timed out.", "status": 0}
    except Exception as e:
        return {"ok": False, "data": f"Unexpected error: {e}", "status": 0}


# -------------------------
# Public functions you call
# -------------------------

def paraphrase_text(text: str, num_return_sequences: int = 3, max_new_tokens: int = 96) -> List[str]:
    text = (text or "").strip()
    if not text:
        return ["⚠️ Please provide some text to paraphrase."]

    params = {
        "num_return_sequences": max(1, int(num_return_sequences)),
        "do_sample": True,
        "temperature": 0.9,
        "top_p": 0.95,
        "max_new_tokens": max_new_tokens,
    }
    r1 = _hf_text2text(PARAPHRASE_PRIMARY, text, params=params)
    if r1["ok"]:
        items = r1["data"]
        outs = [it.get("generated_text") for it in items if isinstance(it, dict) and "generated_text" in it]
        if outs:
            return outs

    # Fallback
    prompt = (
        "Paraphrase the following text in fluent, natural English. Provide diverse rephrasings.\n\n"
        f"Text: {text}\n\nParaphrases:"
    )
    r2 = _hf_text2text(
        PARAPHRASE_FALLBACK,
        prompt,
        params={"num_return_sequences": num_return_sequences, "max_new_tokens": max_new_tokens, "temperature": 0.9, "top_p": 0.95},
    )
    if r2["ok"]:
        items = r2["data"]
        outs = [it.get("generated_text") for it in items if isinstance(it, dict) and "generated_text" in it]
        if outs:
            return outs

    err = r1["data"] if not r1["ok"] else r2["data"]
    return [f"❌ Paraphrasing failed: {err}"]


def generate_questions(text: str, max_questions: int = 5, max_new_tokens: int = 96) -> List[str]:
    text = (text or "").strip()
    if not text:
        return ["⚠️ Please provide text to generate questions."]

    prompt = (
        f"Read the following passage and generate {max(1, int(max_questions))} clear study questions.\n\n"
        f"Passage:\n{text}\n\nQuestions:"
    )
    r = _hf_text2text(
        QG_MODEL,
        prompt,
        params={"max_new_tokens": max_new_tokens, "temperature": 0.7, "top_p": 0.95},
    )
    if r["ok"]:
        data = r["data"]
        if isinstance(data, list) and data and isinstance(data[0], dict) and "generated_text" in data[0]:
            blob = data[0]["generated_text"]
            lines = [ln.strip(" -)\t.") for ln in blob.splitlines() if ln.strip()]
            if len(lines) <= 1:
                return [blob.strip()]
            out = []
            for ln in lines:
                if len(out) >= max_questions:
                    break
                if ln and not ln.lower().startswith("questions"):
                    out.append(ln)
            return out or [blob.strip()]
        return [f"Unexpected response format: {data}"]

    return [f"❌ Question generation failed: {r['data']}"]
