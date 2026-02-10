import { useState } from "react";

export default function App() {

  const [sessionId, setSessionId] = useState(null);
  const [question, setQuestion] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [transcript, setTranscript] = useState("");
  const [loading, setLoading] = useState(false);

  async function upload(e) {
    e.preventDefault();
    const form = new FormData(e.target);

    const res = await fetch("http://4.210.233.81:8000/upload", {
      method: "POST",
      body: form,
    });

    const data = await res.json();
    setSessionId(data.session_id);
    setQuestion(data.question);
  }

  async function submitAnswer() {
    setLoading(true);
    try {
      const form = new FormData();
      form.append("session_id", sessionId);
      form.append("transcript", transcript);

      const res = await fetch("http://4.210.233.81:8000/answer", {
        method: "POST",
        body: form,
      });

      const data = await res.json();
      console.log("next_question from backend:", data.next_question);
      setFeedback(data.feedback);
      setQuestion(data.next_question);
      setTranscript("");
    } finally {
      setLoading(false);
    }
  }

  // Debug: log question state on every render
  console.log("Current question state:", question);

  return (
    <div style={{ padding: 40 }}>
      {!sessionId && (
        <form onSubmit={upload}>
          <input type="file" name="resume" required />
          <br />
          <textarea name="job_description" placeholder="Job Description" />
          <br />
          <button>Start Interview</button>
        </form>
      )}

      {question && (
        <>
          <h3>AI Interviewer</h3>
          <p>{question}</p>

          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Type your answer (voice later)"
            disabled={loading}
          />
          <br />
          <button onClick={submitAnswer} disabled={loading}>
            {loading ? "Submitting..." : "Submit Answer"}
          </button>
          {loading && (
            <div style={{ marginTop: 10, color: '#888' }}>Waiting for AI response...</div>
          )}
        </>
      )}

      {feedback && (
        <>
          <h4>Instant Feedback</h4>
          <pre>{typeof feedback === 'object' ? JSON.stringify(feedback, null, 2) : feedback}</pre>
        </>
      )}
    </div>
  );
}
