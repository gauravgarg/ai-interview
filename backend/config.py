"""
Centralized configuration for ai-interview backend.
"""
import os
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
