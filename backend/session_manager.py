"""
Session management utilities for ai-interview backend.
"""
 
import uuid

# In-memory session store (for MVP only)
SESSIONS = {}

def create_session(resume_text: str, job_description: str, first_question: str) -> str:
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "resume": resume_text,
        "jd": job_description,
        "answers": [],
        "current_question": first_question,
    }
    return session_id

def get_session(session_id: str):
    return SESSIONS.get(session_id)

def update_session(session_id: str, key: str, value):
    if session_id in SESSIONS:
        SESSIONS[session_id][key] = value
