"""Ollama-powered AI Tutor backend for the React Learning Mode.

Serves on port 8081 with CORS support. Uses the question bank JSON files
as RAG context and Ollama for AI-generated teaching responses.

Endpoints:
    GET  /api/health     - Check if Ollama is available
    GET  /api/exams      - List available exams from the question bank
    POST /api/evaluate   - AI evaluates user answer + provides deep-dive teaching
    POST /api/chat       - Free-form chat about a question topic
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
HOST = os.getenv("TUTOR_HOST", "0.0.0.0")
PORT = int(os.getenv("TUTOR_PORT", "8081"))
QUESTION_DIR = Path(os.getenv("AWS_EXAM_QUESTION_DIR", "./questions"))

# ---------------------------------------------------------------------------
# Question bank loader (lightweight RAG context builder)
# ---------------------------------------------------------------------------
_question_bank: dict[str, list[dict]] = {}
_exam_titles: dict[str, str] = {}

TITLE_MAP = {
    "SAA-C03": "AWS Solutions Architect Associate",
    "SAP-C02": "AWS Solutions Architect Professional",
    "CLF-C02": "AWS Cloud Practitioner",
    "DOP-C02": "AWS DevOps Engineer Professional",
    "MLS-C01": "AWS Machine Learning Specialty",
    "AI-900": "Microsoft Azure AI Fundamentals",
    "AI-102": "Microsoft Azure AI Engineer",
    "DP-100": "Microsoft Azure Data Scientist",
    "GCP-ML": "Google Cloud ML Engineer",
    "GCP-CA": "Google Cloud Associate Cloud Engineer",
}


def _derive_title(exam_id: str) -> str:
    for prefix, title in TITLE_MAP.items():
        if exam_id.upper().startswith(prefix.upper()):
            ver = exam_id.replace(prefix, "").lstrip("-").lstrip("_")
            return f"{title} ({ver})" if ver else title
    return exam_id


def load_question_bank():
    """Load all JSON question banks into memory."""
    global _question_bank, _exam_titles
    _question_bank.clear()
    _exam_titles.clear()

    if not QUESTION_DIR.exists():
        print(f"[tutor] Warning: question dir not found: {QUESTION_DIR}", file=sys.stderr)
        return

    for f in sorted(QUESTION_DIR.glob("*.json")):
        exam_id = f.stem
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(data, list):
            continue

        questions = []
        for i, raw in enumerate(data):
            if not isinstance(raw, dict):
                continue
            q_text = str(raw.get("question", "")).strip()
            if q_text.startswith(": "):
                q_text = q_text[2:].strip()
            if not q_text:
                continue

            options = [str(o).strip() for o in raw.get("options", []) if str(o).strip()]
            if not options:
                continue

            questions.append({
                "index": i,
                "question": q_text,
                "options": options,
                "correct": str(raw.get("correct", "")).strip(),
                "explanation": str(raw.get("explanation", "")).strip() or None,
                "references": raw.get("references"),
            })

        if questions:
            _question_bank[exam_id] = questions
            _exam_titles[exam_id] = _derive_title(exam_id)

    print(f"[tutor] Loaded {sum(len(q) for q in _question_bank.values())} questions "
          f"from {len(_question_bank)} exams", file=sys.stderr)


def _get_question(exam_id: str, question_index: int) -> dict | None:
    """Retrieve a specific question from the bank."""
    qs = _question_bank.get(exam_id, [])
    for q in qs:
        if q["index"] == question_index:
            return q
    return None


def _build_related_context(exam_id: str, question: dict, max_related: int = 3) -> str:
    """Build RAG context from related questions in the same exam."""
    qs = _question_bank.get(exam_id, [])
    keywords = set(question["question"].lower().split())
    # Score questions by keyword overlap
    scored = []
    for q in qs:
        if q["index"] == question["index"]:
            continue
        q_words = set(q["question"].lower().split())
        overlap = len(keywords & q_words)
        if overlap > 3:
            scored.append((overlap, q))
    scored.sort(key=lambda x: x[0], reverse=True)

    parts = []
    for _, rq in scored[:max_related]:
        part = f"Related Q: {rq['question']}\nCorrect: {rq['correct']}"
        if rq.get("explanation"):
            part += f"\nExplanation: {rq['explanation']}"
        parts.append(part)
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Ollama API helpers
# ---------------------------------------------------------------------------
def _ollama_health() -> bool:
    """Check if Ollama is running."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
        resp = urllib.request.urlopen(req, timeout=3)
        return resp.status == 200
    except Exception:
        return False


def _ollama_generate(prompt: str, system: str = "", temperature: float = 0.7) -> str:
    """Call Ollama generate API and return the full response."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": 2048},
    }
    if system:
        payload["system"] = system

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        body = json.loads(resp.read().decode("utf-8"))
        return body.get("response", "").strip()
    except urllib.error.URLError as e:
        return f"Error connecting to Ollama: {e}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------
EVALUATE_SYSTEM = """You are an expert certification exam tutor. Your job is to:
1. Check the user's answer against the correct answer
2. If wrong, explain WHY their choice is incorrect and what misconception they have
3. Teach the correct concept by diving deep into AT LEAST 3 related sub-topics
4. Use clear examples and analogies
5. End with a brief summary and a follow-up question to test understanding

Format your response in clear sections using markdown:
- **Result**: Correct/Incorrect
- **Your Answer Analysis**: Why their choice was right/wrong
- **Deep Dive Topics** (at least 3 when incorrect):
  - Topic 1: ...
  - Topic 2: ...
  - Topic 3: ...
- **Key Takeaway**: One-sentence summary
- **Check Your Understanding**: A follow-up question

Be encouraging but thorough. The goal is mastery, not just memorization."""

CHAT_SYSTEM = """You are an expert certification exam tutor helping a student master
cloud computing concepts. You have deep knowledge of AWS, Azure, and GCP services.

Rules:
- Be concise but thorough
- Use real-world examples and analogies
- When explaining, always connect back to the exam topic
- If the student demonstrates understanding, acknowledge it and move on
- If they're still confused, try a different explanation approach
- Use markdown for formatting

Your goal is to help the student truly UNDERSTAND the concept, not just memorize answers."""


# ---------------------------------------------------------------------------
# HTTP Request Handler
# ---------------------------------------------------------------------------
class TutorHandler(BaseHTTPRequestHandler):
    """Handle AI tutor HTTP requests with CORS."""

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            self._handle_health()
        elif self.path == "/api/exams":
            self._handle_exams()
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path == "/api/evaluate":
            self._handle_evaluate()
        elif self.path == "/api/chat":
            self._handle_chat()
        else:
            self._send_json({"error": "Not found"}, 404)

    # --- Handlers ---

    def _handle_health(self):
        ollama_ok = _ollama_health()
        self._send_json({
            "status": "ok" if ollama_ok else "ollama_unavailable",
            "ollama": ollama_ok,
            "model": OLLAMA_MODEL,
        })

    def _handle_exams(self):
        exams = []
        for exam_id, questions in _question_bank.items():
            exams.append({
                "exam_id": exam_id,
                "title": _exam_titles.get(exam_id, exam_id),
                "question_count": len(questions),
            })
        self._send_json({"exams": exams})

    def _handle_evaluate(self):
        body = self._read_body()
        exam_id = body.get("exam_id", "")
        question_index = body.get("question_index")
        user_answer = body.get("user_answer", "")
        question_text = body.get("question_text", "")
        options = body.get("options", [])
        correct_answer = body.get("correct_answer", "")
        explanation = body.get("explanation", "")

        # Try to get question from bank for RAG
        rag_context = ""
        if exam_id and question_index is not None:
            q = _get_question(exam_id, question_index)
            if q:
                question_text = question_text or q["question"]
                options = options or q["options"]
                correct_answer = correct_answer or q["correct"]
                explanation = explanation or q.get("explanation", "")
                rag_context = _build_related_context(exam_id, q)

        is_correct = user_answer.strip().lower() == correct_answer.strip().lower()

        options_str = "\n".join(f"  {chr(65+i)}. {opt}" for i, opt in enumerate(options))
        prompt = f"""Exam: {_exam_titles.get(exam_id, exam_id)}

Question: {question_text}

Options:
{options_str}

Correct Answer: {correct_answer}
Student's Answer: {user_answer}
Student was: {"CORRECT" if is_correct else "INCORRECT"}
"""
        if explanation:
            prompt += f"\nOfficial Explanation: {explanation}\n"
        if rag_context:
            prompt += f"\nRelated questions for context:\n{rag_context}\n"

        if is_correct:
            prompt += "\nThe student answered correctly. Briefly confirm they're right, explain WHY this is the correct answer to reinforce the concept, and mention 1-2 related topics they should also understand."
        else:
            prompt += "\nThe student answered incorrectly. Follow the deep-dive teaching format. Explain their misconception, then teach at least 3 related sub-topics to build real understanding."

        response = _ollama_generate(prompt, system=EVALUATE_SYSTEM)

        self._send_json({
            "correct": is_correct,
            "correct_answer": correct_answer,
            "ai_response": response,
            "exam_id": exam_id,
            "question_index": question_index,
        })

    def _handle_chat(self):
        body = self._read_body()
        message = body.get("message", "")
        exam_id = body.get("exam_id", "")
        question_context = body.get("question_context", "")
        conversation_history = body.get("history", [])

        prompt_parts = []
        if question_context:
            prompt_parts.append(f"Current question context:\n{question_context}\n")

        # Include conversation history
        for entry in conversation_history[-6:]:  # Last 6 messages
            role = entry.get("role", "user")
            content = entry.get("content", "")
            prompt_parts.append(f"{role.capitalize()}: {content}")

        prompt_parts.append(f"Student: {message}")
        prompt = "\n\n".join(prompt_parts)

        if exam_id:
            system = CHAT_SYSTEM + f"\n\nYou are tutoring for: {_exam_titles.get(exam_id, exam_id)}"
        else:
            system = CHAT_SYSTEM

        response = _ollama_generate(prompt, system=system)

        self._send_json({
            "response": response,
        })

    def log_message(self, fmt, *args):
        """Log to stderr only."""
        print(f"[tutor] {fmt % args}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print(f"[tutor] Loading question bank from {QUESTION_DIR}...", file=sys.stderr)
    load_question_bank()

    print(f"[tutor] Checking Ollama at {OLLAMA_URL}...", file=sys.stderr)
    if _ollama_health():
        print(f"[tutor] Ollama is running with model {OLLAMA_MODEL}", file=sys.stderr)
    else:
        print(f"[tutor] WARNING: Ollama not detected at {OLLAMA_URL}. "
              f"Start it with: ollama serve", file=sys.stderr)

    server = HTTPServer((HOST, PORT), TutorHandler)
    print(f"[tutor] AI Tutor backend running on http://{HOST}:{PORT}", file=sys.stderr)
    print(f"[tutor] Endpoints:", file=sys.stderr)
    print(f"[tutor]   GET  /api/health    - Check Ollama status", file=sys.stderr)
    print(f"[tutor]   GET  /api/exams     - List exam banks", file=sys.stderr)
    print(f"[tutor]   POST /api/evaluate  - Evaluate answer + teach", file=sys.stderr)
    print(f"[tutor]   POST /api/chat      - Chat about a topic", file=sys.stderr)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[tutor] Shutting down...", file=sys.stderr)
        server.server_close()


if __name__ == "__main__":
    main()
