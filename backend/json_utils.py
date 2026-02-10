"""
JSON utility functions for ai-interview backend.
"""
import json
 
def safe_json(text: str):
    try:
        return json.loads(text)
    except:
        start = text.find("{")
        end = text.rfind("}")
        return json.loads(text[start:end + 1])

