from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
import PyPDF2
from io import BytesIO


from llm import generate_question, evaluate_answer
from session_manager import create_session, get_session, update_session

app = FastAPI()

# Allow all CORS for MVP/demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
async def upload(resume: UploadFile, job_description: str = Form(...)):
    """
    Upload a resume and job description, extract text, generate first question, and create a session.
    """
    try:
        print(f"Received resume: {resume.filename}, job_description: {job_description}")
        resume_bytes = await resume.read()
        print(f"Resume bytes length: {len(resume_bytes)}")
        resume_text = None

        if resume.filename and resume.filename.lower().endswith(".pdf"):
            try:
                pdf_reader = PyPDF2.PdfReader(BytesIO(resume_bytes))
                resume_text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
            except Exception as pdf_e:
                print(f"PDF extraction error: {pdf_e}")
                raise HTTPException(status_code=400, detail="Could not extract text from PDF. Please upload a valid PDF.")
        else:
            try:
                resume_text = resume_bytes.decode("utf-8")
            except Exception as txt_e:
                print(f"Text file decode error: {txt_e}")
                raise HTTPException(status_code=400, detail="Could not decode resume as text. Please upload a valid .txt or .pdf file.")

        question = generate_question(resume_text, job_description, [])
        session_id = create_session(resume_text, job_description, question)

        return {
            "session_id": session_id,
            "question": question,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /upload: {e}")
        raise HTTPException(status_code=400, detail=f"Upload failed: {e}")



@app.post("/answer")
async def answer(session_id: str = Form(...), transcript: str = Form(...)):
    """
    Receive an answer, evaluate it, generate feedback and the next question.
    """
    try:
        session = get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found.")

        question = session["current_question"]
        feedback = evaluate_answer(question, transcript)
        session["answers"].append(transcript)

        next_question = generate_question(
            session["resume"],
            session["jd"],
            session["answers"],
        )
        print(f"Next question generated: {next_question!r}")
        update_session(session_id, "current_question", next_question)

        return {
            "feedback": feedback,
            "next_question": next_question,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /answer: {e}")
        raise HTTPException(status_code=400, detail=f"Answer processing failed: {e}")
