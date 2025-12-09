import os
import requests

HF_API_KEY = os.getenv("HF_API_KEY")
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://router.huggingface.co")
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Llama-3.2-1B-Instruct")


def generate_llm_answer(query: str, context: str) -> str:
    """
    Calls HuggingFace Inference Router API with context + query.
    """
    try:
        payload = {
            "model": LLM_MODEL,
            "input": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:",
            "parameters": {
                "max_new_tokens": 10,
                "temperature": 0.3,
            }
        }

        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json"
        }

        resp = requests.post(
            f"{LLM_API_BASE}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )

        if resp.status_code != 200:
            print("HF LLM Error:", resp.text)
            return ""

        data = resp.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("HF LLM Error:", e)
        return ""
