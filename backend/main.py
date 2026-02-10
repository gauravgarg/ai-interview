import subprocess
from fastapi import FastAPI, UploadFile, Form, HTTPException, File
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



from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioConfig

import os

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

@app.post("/answer")
async def answer(session_id: str = Form(...), audio: UploadFile = File(None), transcript: str = Form(None)):
    """
    Receive an answer as audio or text, transcribe if audio, evaluate, generate feedback and the next question.
    """
    try:
        print(f"/answer called with session_id={session_id}, audio={audio is not None}, transcript={transcript is not None}")
        session = get_session(session_id)
        if not session:
            print(f"Session not found for session_id={session_id}")
            raise HTTPException(status_code=404, detail="Session not found.")

        answer_text = transcript
        if audio is not None:
            print(f"Audio file received: filename={audio.filename}, content_type={audio.content_type}")
            audio_bytes = await audio.read()
            temp_audio_path = f"/tmp/{audio.filename}"
            with open(temp_audio_path, "wb") as f:
                f.write(audio_bytes)
            print(f"Audio file written to {temp_audio_path}, size={len(audio_bytes)} bytes")
            # Convert to 16kHz, 16-bit, mono WAV using ffmpeg
            converted_path = temp_audio_path + "_converted.wav"
            try:
                subprocess.run([
                    "ffmpeg", "-y", "-i", temp_audio_path,
                    "-ar", "16000", "-ac", "1", "-f", "wav", converted_path
                ], check=True)
                print(f"Audio converted to {converted_path}")
                speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
                audio_config = AudioConfig(filename=converted_path)
                recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
                result = recognizer.recognize_once()
                print(f"Azure Speech result: {result.text}")
                answer_text = result.text
            finally:
                os.remove(temp_audio_path)
                if os.path.exists(converted_path):
                    os.remove(converted_path)
                print(f"Temp files {temp_audio_path} and {converted_path} removed.")
        else:
            print("No audio file provided, using transcript field.")

        print(f"Answer text to evaluate: {answer_text}")
        question = session["current_question"]
        feedback = evaluate_answer(question, answer_text)
        session["answers"].append(answer_text)

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
