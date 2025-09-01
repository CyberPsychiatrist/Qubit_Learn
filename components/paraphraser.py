import os
import requests

HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
PARAPHRASER_URL = "https://api-inference.huggingface.co/models/Vamsi/T5_Paraphrase_Paws"
headers = {"Authorization": f"Bearer {HUGGING_FACE_API_KEY}"}

def paraphrase_text(text, num_return_sequences=3, max_length=128):
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
