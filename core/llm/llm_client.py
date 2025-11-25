import os
import requests

MISTRAL_API_KEY = os.getenv("LLM_API_KEY")
MISTRAL_BASE = os.getenv("LLM_API_BASE", "https://api.mistral.ai/v1")
MISTRAL_MODEL = os.getenv("LLM_MODEL", "mistral-small-latest")

headers = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json"
}


def generate_answer(query: str, context_chunks):
    """
    Call Mistral AI to generate an answer from context.
    """

    # Combine context into a single block for RAG
    context_text = "\n\n".join(
        [chunk.get("text", "") for chunk in context_chunks]
    )

    prompt = f"""
You are an AI assistant answering questions based on the given context.

CONTEXT:
{context_text}

QUESTION:
{query}

Answer clearly using only the context. 
If the context does not contain the answer, say "I don't know based on the provided data."
"""

    payload = {
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(
            f"{MISTRAL_BASE}/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )

        if response.status_code != 200:
            print("Mistral API Error:", response.text)
            return "No answer"

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("Mistral LLM Exception:", e)
        return "No answer"
