import os
import json
import requests
from openai import OpenAI

# =========================
# ENV CONFIG
# =========================
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# CORE GENERATOR
# =========================
def generate_text(prompt: str) -> str:
    if LLM_PROVIDER == "ollama":
        return ollama_generate(prompt)
    return openai_generate(prompt)

# =========================
# OPENAI
# =========================
def openai_generate(prompt: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a strict JSON-only AI interviewer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

# =========================
# OLLAMA
# =========================
def ollama_generate(prompt: str) -> str:
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=180  # Increased timeout to 3 minutes
        )
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.Timeout:
        raise Exception("Ollama API timed out. Try again or check Ollama server performance.")
    except Exception as e:
        raise Exception(f"Ollama API error: {e}")

# =========================
# BUSINESS LOGIC
# =========================
def evaluate_answer(answer: str, question: str):
    prompt = f"""
Question: {question}
Answer: {answer}

Return ONLY valid JSON:
{{
  "clarity": 1-5,
  "correctness": 1-5,
  "communication": 1-5,
  "improvement_tip": "text"
}}
"""
    raw = generate_text(prompt)
    return safe_json(raw)

def generate_question(resume: str, jd: str, answers: list):
    prompt = f"""
You are an interviewer.

Resume:
{resume}

Job Description:
{jd}

Ask question #{len(answers) + 1}.
Only return the question.
"""
    return generate_text(prompt).strip()

# =========================
# JSON SAFETY (VERY IMPORTANT FOR OLLAMA)
# =========================
def safe_json(text: str):
    try:
        return json.loads(text)
    except:
        start = text.find("{")
        end = text.rfind("}")
        return json.loads(text[start:end + 1])
