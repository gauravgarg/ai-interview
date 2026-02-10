from fastapi import FastAPI, UploadFile, Form
import PyPDF2
from fastapi.middleware.cors import CORSMiddleware
import uuid

from llm import generate_question, evaluate_answer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (OK for MVP)
SESSIONS = {}


@app.post("/upload")
async def upload(resume: UploadFile, job_description: str = Form(...)):
    try:
        print(f"Received resume: {resume.filename}, job_description: {job_description}")
        resume_bytes = await resume.read()
        print(f"Resume bytes length: {len(resume_bytes)}")
        resume_text = None
        if resume.filename and resume.filename.lower().endswith(".pdf"):
            try:
                from io import BytesIO
                pdf_reader = PyPDF2.PdfReader(BytesIO(resume_bytes))
                resume_text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
            except Exception as pdf_e:
                print(f"PDF extraction error: {pdf_e}")
                raise Exception("Could not extract text from PDF. Please upload a valid PDF.")
        else:
            try:
                resume_text = resume_bytes.decode("utf-8")
            except Exception as txt_e:
                print(f"Text file decode error: {txt_e}")
                raise Exception("Could not decode resume as text. Please upload a valid .txt or .pdf file.")

        session_id = str(uuid.uuid4())

        question = generate_question(resume_text, job_description, [])

        SESSIONS[session_id] = {
            "resume": resume_text,
            "jd": job_description,
            "answers": [],
            "current_question": question,
        }

        return {
            "session_id": session_id,
            "question": question,
        }
    except Exception as e:
        print(f"Error in /upload: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Upload failed: {e}")


@app.post("/answer")
async def answer(session_id: str = Form(...), transcript: str = Form(...)):
    session = SESSIONS[session_id]

    question = session["current_question"]

    feedback = evaluate_answer(question, transcript)

    session["answers"].append(transcript)

    next_question = generate_question(
        session["resume"],
        session["jd"],
        session["answers"],
    )
    print(f"Next question generated: {next_question!r}")

    session["current_question"] = next_question

    return {
        "feedback": feedback,
        "next_question": next_question,
    }
