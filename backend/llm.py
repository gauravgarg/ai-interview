
from prompt_utils import generate_question_prompt, generate_evaluation_prompt
from config import LLM_PROVIDER
from llm_providers import openai_generate, ollama_generate
from json_utils import safe_json

def generate_text(prompt: str) -> str:
    if LLM_PROVIDER == "ollama":
        return ollama_generate(prompt)
    return openai_generate(prompt)

def evaluate_answer(question: str, answer: str):
    prompt = generate_evaluation_prompt(question, answer)
    raw = generate_text(prompt)
    return safe_json(raw)

def generate_question(resume: str, jd: str, answers: list):
    prompt = generate_question_prompt(resume, jd, answers)
    return generate_text(prompt).strip()
