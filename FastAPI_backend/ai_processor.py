# src/ai_processor.py

from __future__ import annotations

import os
from typing import List, Dict, Any, Optional
from huggingface_hub import InferenceClient

# ============================
# Model Registry
# ============================

PARAPHRASE_MODELS = {
    "pegasus": "tuner007/pegasus_paraphrase",
    "t5": "AventIQ-AI/t5-paraphrase-generation",
    "flan": "google/flan-t5-base",
}

QG_MODELS = {
    "t5-simple": "iarfmoose/t5-base-question-generator",
    "t5-advanced": "Avinash250325/T5BaseQuestionGeneration",
}

DEFAULT_PARAPHRASE = "pegasus"
DEFAULT_QG = "t5-simple"

# ============================
# Token Handling
# ============================

try:
    try:
        from config.settings import HUGGING_FACE_API_KEY as _HF_TOKEN_FROM_SETTINGS
    except ImportError:
        # Fallback to root level config if not found in current directory
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from config.settings import HUGGING_FACE_API_KEY as _HF_TOKEN_FROM_SETTINGS
except Exception:
    _HF_TOKEN_FROM_SETTINGS = None


def _get_hf_token() -> Optional[str]:
    return (
        os.getenv("HUGGING_FACE_API_KEY")
        or os.getenv("HF_TOKEN")
        or _HF_TOKEN_FROM_SETTINGS
    )

# ============================
# Hugging Face Client
# ============================

_HF_CLIENT: Optional[InferenceClient] = None


def _get_client() -> InferenceClient:
    global _HF_CLIENT
    if _HF_CLIENT is None:
        token = _get_hf_token()
        if not token:
            raise RuntimeError("❌ Hugging Face API key is missing. Set HUGGING_FACE_API_KEY.")
        _HF_CLIENT = InferenceClient(token=token)
    return _HF_CLIENT

# ============================
# Core helper
# ============================

def _hf_text2text(
    model_id: str,
    prompt: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Wrapper around Hugging Face InferenceClient.text_generation
    to simulate text2text generation (works for T5/Pegasus/Flan).
    """
    try:
        client = _get_client()
        params = params or {}

        num_return_sequences = params.get("num_return_sequences", 1)
        outputs = []

        for _ in range(num_return_sequences):
            out = client.text_generation(
                model=model_id,
                prompt=prompt,
                max_new_tokens=params.get("max_new_tokens", 128),
                temperature=params.get("temperature", 0.7),
                top_p=params.get("top_p", 0.95),
                do_sample=params.get("do_sample", True),
                return_full_text=False,
            )
            outputs.append({"generated_text": out})

        return {"ok": True, "data": outputs, "status": 200}

    except Exception as e:
        return {"ok": False, "data": str(e), "status": 0}

# ============================
# Public functions
# ============================

def paraphrase_text(
    text: str,
    num_return_sequences: int = 3,
    max_new_tokens: int = 96,
    model_choice: str = DEFAULT_PARAPHRASE,
) -> List[str]:
    """Generate paraphrases using Pegasus / T5 / Flan."""
    text = (text or "").strip()
    if not text:
        return ["⚠️ Please provide some text to paraphrase."]

    model_id = PARAPHRASE_MODELS.get(model_choice, PARAPHRASE_MODELS[DEFAULT_PARAPHRASE])

    params = {
        "num_return_sequences": max(1, int(num_return_sequences)),
        "do_sample": True,
        "temperature": 0.9,
        "top_p": 0.95,
        "max_new_tokens": max_new_tokens,
    }

    r = _hf_text2text(model_id, text, params)
    if r["ok"]:
        return [it.get("generated_text", "").strip() for it in r["data"] if isinstance(it, dict)]
    return [f"❌ Paraphrasing failed: {r['data']}"]


def generate_questions(
    text: str,
    max_questions: int = 5,
    max_new_tokens: int = 96,
    model_choice: str = DEFAULT_QG,
) -> List[str]:
    """Generate study questions from text using T5-based QG models."""
    text = (text or "").strip()
    if not text:
        return ["⚠️ Please provide text to generate questions."]

    model_id = QG_MODELS.get(model_choice, QG_MODELS[DEFAULT_QG])

    if model_choice == "t5-advanced":
        prompt = f"<extra_id_97>short answer <extra_id_98>easy <extra_id_99>[] {text}"
    else:
        prompt = (
            f"Read the following passage and generate {max(1, int(max_questions))} clear study questions.\n\n"
            f"Passage:\n{text}\n\nQuestions:"
        )

    params = {"max_new_tokens": max_new_tokens, "temperature": 0.7, "top_p": 0.95}
    r = _hf_text2text(model_id, prompt, params)

    if r["ok"]:
        blob = r["data"][0].get("generated_text", "").strip()
        lines = [ln.strip(" -)\t.") for ln in blob.splitlines() if ln.strip()]

        if len(lines) <= 1:
            return [blob]

        out = []
        for ln in lines:
            if len(out) >= max_questions:
                break
            if ln and not ln.lower().startswith("questions"):
                out.append(ln)
        return out or [blob]

    return [f"❌ Question generation failed: {r['data']}"]
