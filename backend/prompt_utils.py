"""
Prompt generation and parsing utilities for ai-interview backend.
"""
 
def generate_question_prompt(resume: str, jd: str, answers: list) -> str:
    return f"""
You are an interviewer.
*** End Patch
Resume:
{resume}

Job Description:
{jd}

Ask question #{len(answers) + 1}.
Only return the question.
""".strip()

def generate_evaluation_prompt(question: str, answer: str) -> str:
    return f"""
Question: {question}
Answer: {answer}

Return ONLY valid JSON:
{{
  "clarity": 1-5,
  "correctness": 1-5,
  "communication": 1-5,
  "improvement_tip": "text"
}}
""".strip()
