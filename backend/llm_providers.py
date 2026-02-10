"""
Provider-specific LLM logic for ai-interview backend.
"""
import requests
from openai import OpenAI
from config import LLM_PROVIDER, OLLAMA_URL, OLLAMA_MODEL, OPENAI_API_KEY
 
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def openai_generate(prompt: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a strict JSON-only AI interviewer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content or ""

def ollama_generate(prompt: str) -> str:
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.Timeout:
        raise Exception("Ollama API timed out. Try again or check Ollama server performance.")
    except Exception as e:
        raise Exception(f"Ollama API error: {e}")
