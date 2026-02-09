"""Ollama-powered AI Tutor backend for the React Learning Mode.

Session-based architecture with adaptive question selection,
teach-until-learned micro-check loop, and structured feedback.

Endpoints:
    GET  /api/health              - Check Ollama status
    POST /api/session/start       - Start a learning session
    POST /api/session/next        - Get next question (adaptive)
    POST /api/session/answer      - Submit answer + get AI feedback
    POST /api/session/microcheck  - Generate or check micro-check question
    GET  /api/session/status      - Session stats + weak topics
    POST /api/chat                - Free-form chat about a topic
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass, field
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
# Tag inference (inline copy from tagging.py for self-containment)
# ---------------------------------------------------------------------------
TAG_RULES: list[tuple[str, list[str]]] = [
    ("iam", [r"\bIAM\b", r"\bpolicy\b", r"\brole\b", r"\bpermission\b",
             r"\bSTS\b", r"\bfederat", r"\bidentity\b", r"\baccess control\b"]),
    ("vpc_networking", [r"\bVPC\b", r"\bsubnet\b", r"\brout(e|ing)\b", r"\bNACL\b",
                        r"\bsecurity group\b", r"\bVPN\b", r"\bDirect Connect\b",
                        r"\bTransit Gateway\b", r"\bPrivateLink\b"]),
    ("s3_storage", [r"\bS3\b", r"\bbucket\b", r"\bobject storage\b", r"\bGlacier\b",
                    r"\bversioning\b", r"\bstorage class\b"]),
    ("ec2_compute", [r"\bEC2\b", r"\bAMI\b", r"\bAuto Scaling\b", r"\bELB\b",
                     r"\bALB\b", r"\bNLB\b", r"\binstance\b", r"\bEBS\b"]),
    ("serverless", [r"\bLambda\b", r"\bAPI Gateway\b", r"\bStep Functions\b",
                    r"\bserverless\b", r"\bFargate\b"]),
    ("containers", [r"\bECS\b", r"\bEKS\b", r"\bDocker\b", r"\bcontainer\b",
                    r"\bKubernetes\b"]),
    ("databases", [r"\bRDS\b", r"\bDynamoDB\b", r"\bAurora\b", r"\bElastiCache\b",
                   r"\bRedshift\b", r"\bdatabase\b"]),
    ("monitoring_logging", [r"\bCloudWatch\b", r"\bCloudTrail\b", r"\bX-Ray\b",
                            r"\blog(s|ging)\b", r"\bmetric\b", r"\balarm\b"]),
    ("security_encryption", [r"\bencrypt\b", r"\bKMS\b", r"\bHSM\b", r"\bWAF\b",
                             r"\bShield\b", r"\bGuardDuty\b"]),
    ("high_availability", [r"\bhigh availability\b", r"\bfailover\b", r"\bmulti-AZ\b",
                           r"\brecovery\b", r"\bRPO\b", r"\bRTO\b"]),
    ("cost_optimization", [r"\bcost\b", r"\bBudgets\b", r"\bpricing\b",
                           r"\bfree tier\b", r"\bCost Explorer\b"]),
    ("devops_cicd", [r"\bCodePipeline\b", r"\bCodeBuild\b", r"\bCloudFormation\b",
                     r"\bCDK\b", r"\bElastic Beanstalk\b"]),
    ("ml_ai", [r"\bSageMaker\b", r"\bmachine learning\b", r"\bML\b",
               r"\bRekognition\b", r"\bComprehend\b"]),
    ("messaging_integration", [r"\bSQS\b", r"\bSNS\b", r"\bKinesis\b",
                               r"\bEventBridge\b", r"\bqueue\b"]),
    ("content_delivery", [r"\bCloudFront\b", r"\bCDN\b", r"\bRoute\\s*53\b",
                          r"\bDNS\b"]),
    ("analytics", [r"\bAthena\b", r"\bGlue\b", r"\bEMR\b", r"\bQuickSight\b",
                   r"\bdata lake\b"]),
    ("migration", [r"\bmigrat\b", r"\bSnowball\b", r"\bDMS\b", r"\bDataSync\b"]),
]


def _infer_tags(text: str) -> list[str]:
    tags = []
    for tag, patterns in TAG_RULES:
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                tags.append(tag)
                break
    return sorted(set(tags)) if tags else ["general"]


# ---------------------------------------------------------------------------
# Question bank loader
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

            correct_raw = str(raw.get("correct", "")).strip()
            multi_select = not correct_raw

            # Find correct indices
            correct_indices = []
            if correct_raw:
                for ci, opt in enumerate(options):
                    if opt.strip().lower() == correct_raw.strip().lower():
                        correct_indices = [ci]
                        break
                if not correct_indices:
                    for ci, opt in enumerate(options):
                        if opt.strip().lower().startswith(correct_raw.strip().lower()[:50]):
                            correct_indices = [ci]
                            break

            questions.append({
                "index": i,
                "question": q_text,
                "options": options,
                "correct": correct_raw,
                "correct_indices": correct_indices,
                "multi_select": multi_select,
                "explanation": str(raw.get("explanation", "")).strip() or None,
                "references": raw.get("references"),
                "tags": _infer_tags(q_text),
            })

        if questions:
            _question_bank[exam_id] = questions
            _exam_titles[exam_id] = _derive_title(exam_id)

    total = sum(len(q) for q in _question_bank.values())
    print(f"[tutor] Loaded {total} questions from {len(_question_bank)} exams", file=sys.stderr)


# ---------------------------------------------------------------------------
# Session store (in-memory)
# ---------------------------------------------------------------------------
@dataclass
class QuestionResult:
    correct: bool
    attempts: int = 1
    micro_check_passed: bool = False
    mastered: bool = False


@dataclass
class LearningSession:
    session_id: str
    exam_id: str
    questions: list[dict]
    asked_indices: list[int] = field(default_factory=list)
    results: dict[int, QuestionResult] = field(default_factory=dict)
    tag_stats: dict[str, dict[str, int]] = field(default_factory=dict)
    current_question_idx: int | None = None
    phase: str = "question"  # question | feedback | teaching | micro_check
    current_micro_check: dict | None = None
    micro_check_attempts: int = 0


_sessions: dict[str, LearningSession] = {}


def _update_tag_stats(session: LearningSession, tags: list[str], correct: bool):
    for tag in tags:
        if tag not in session.tag_stats:
            session.tag_stats[tag] = {"asked": 0, "correct": 0}
        session.tag_stats[tag]["asked"] += 1
        if correct:
            session.tag_stats[tag]["correct"] += 1


def _get_weak_tags(session: LearningSession, top_n: int = 5) -> list[dict]:
    """Return weak tags with accuracy < 60%, sorted worst first."""
    weak = []
    for tag, stats in session.tag_stats.items():
        if stats["asked"] >= 2:
            acc = stats["correct"] / stats["asked"]
            if acc < 0.6:
                weak.append({"tag": tag, "asked": stats["asked"],
                             "correct": stats["correct"],
                             "accuracy": round(acc, 2)})
    weak.sort(key=lambda x: x["accuracy"])
    return weak[:top_n]


def _get_tag_summary(session: LearningSession) -> list[dict]:
    """Return all tags with stats."""
    summary = []
    for tag, stats in sorted(session.tag_stats.items()):
        acc = stats["correct"] / stats["asked"] if stats["asked"] else 0
        summary.append({"tag": tag, "asked": stats["asked"],
                        "correct": stats["correct"],
                        "accuracy": round(acc, 2)})
    summary.sort(key=lambda x: x["accuracy"])
    return summary


def _pick_adaptive_question(session: LearningSession) -> int | None:
    """Pick next question index using adaptive selection.

    Priority:
    1. Questions in weak tags not yet seen
    2. Previously wrong questions not yet mastered
    3. Unseen questions (random)
    4. All mastered -> None (session complete or recycle)
    """
    all_indices = set(range(len(session.questions)))
    seen = set(session.asked_indices)
    unseen = all_indices - seen
    mastered = {i for i, r in session.results.items() if r.mastered}

    # Weak tags
    weak_tags = {w["tag"] for w in _get_weak_tags(session)}

    if weak_tags and unseen:
        # Find unseen questions matching weak tags
        candidates = []
        for idx in unseen:
            q = session.questions[idx]
            if any(t in weak_tags for t in q.get("tags", [])):
                candidates.append(idx)
        if candidates:
            return random.choice(candidates)

    # Previously wrong, not mastered
    wrong_not_mastered = []
    for idx, r in session.results.items():
        if not r.correct and not r.mastered and idx not in seen[-3:] if len(seen) > 3 else True:
            wrong_not_mastered.append(idx)
    if wrong_not_mastered:
        return random.choice(wrong_not_mastered)

    # Unseen questions
    if unseen:
        return random.choice(list(unseen))

    # All seen - pick from non-mastered
    not_mastered = all_indices - mastered
    if not_mastered:
        return random.choice(list(not_mastered))

    return None  # Everything mastered


# ---------------------------------------------------------------------------
# Ollama API helpers
# ---------------------------------------------------------------------------
def _ollama_health() -> bool:
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
        resp = urllib.request.urlopen(req, timeout=3)
        return resp.status == 200
    except Exception:
        return False


def _ollama_generate(prompt: str, system: str = "", temperature: float = 0.7) -> str:
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


def _build_related_context(exam_id: str, question: dict, max_related: int = 3) -> str:
    qs = _question_bank.get(exam_id, [])
    keywords = set(question["question"].lower().split())
    scored = []
    for q in qs:
        if q["index"] == question["index"]:
            continue
        overlap = len(keywords & set(q["question"].lower().split()))
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
# System prompts
# ---------------------------------------------------------------------------
EVALUATE_SYSTEM = """You are an expert certification exam tutor. Your job is to evaluate answers and teach.

When the student is CORRECT:
- Confirm they're right with brief encouragement
- Explain WHY this is the correct answer (reinforce the concept)
- Mention 1-2 related concepts they should also understand

When the student is INCORRECT or said "I don't know":
- Do NOT be harsh - be encouraging but clear
- Explain the misconception in their choice
- Deep dive into AT LEAST 3 related sub-topics:
  - The core concept behind the correct answer
  - Why the wrong options are wrong (common traps)
  - A real-world analogy or example
- End with a "Key Takeaway" summary

Format with markdown: use **bold**, bullet lists, and headers.
Keep it focused and exam-relevant. Goal is mastery, not memorization."""

MICRO_CHECK_SYSTEM = """You are an expert exam tutor. Generate exactly ONE short verification question
to check if the student understood the concept just taught.

Rules:
- The question must be different from the original exam question
- It should test the SAME underlying concept
- Provide exactly 2 options: one correct, one plausible but wrong
- Return ONLY valid JSON in this exact format, nothing else:

{"question": "your question here", "options": ["correct answer", "wrong answer"], "correct_index": 0, "explanation": "brief explanation"}

Do not include any text outside the JSON object."""

CHAT_SYSTEM = """You are an expert certification exam tutor helping a student master
cloud computing concepts. Be concise but thorough. Use real-world examples.
When the student demonstrates understanding, acknowledge it and move on.
If they're confused, try a different explanation. Use markdown formatting."""


# ---------------------------------------------------------------------------
# HTTP Request Handler
# ---------------------------------------------------------------------------
class TutorHandler(BaseHTTPRequestHandler):

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
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            self._handle_health()
        elif self.path.startswith("/api/session/status"):
            self._handle_session_status()
        elif self.path == "/api/exams":
            self._handle_exams()
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = self.path
        if path == "/api/session/start":
            self._handle_session_start()
        elif path == "/api/session/next":
            self._handle_session_next()
        elif path == "/api/session/answer":
            self._handle_session_answer()
        elif path == "/api/session/microcheck":
            self._handle_session_microcheck()
        elif path == "/api/chat":
            self._handle_chat()
        elif path == "/api/evaluate":
            self._handle_evaluate_legacy()
        else:
            self._send_json({"error": "Not found"}, 404)

    # --- Health & Exams ---

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

    # --- Session Management ---

    def _handle_session_start(self):
        body = self._read_body()
        exam_id = body.get("exam_id", "")
        if exam_id not in _question_bank:
            self._send_json({"error": f"Unknown exam: {exam_id}"}, 400)
            return

        sid = str(uuid.uuid4())[:12]
        questions = list(_question_bank[exam_id])  # shallow copy
        session = LearningSession(
            session_id=sid,
            exam_id=exam_id,
            questions=questions,
        )
        _sessions[sid] = session

        # Pick first question
        idx = _pick_adaptive_question(session)
        session.current_question_idx = idx
        session.phase = "question"
        if idx is not None:
            session.asked_indices.append(idx)

        q = questions[idx] if idx is not None else None
        self._send_json({
            "session_id": sid,
            "exam_id": exam_id,
            "total_questions": len(questions),
            "question": self._format_question(q, idx, len(questions)) if q else None,
        })

    def _handle_session_next(self):
        body = self._read_body()
        sid = body.get("session_id", "")
        session = _sessions.get(sid)
        if not session:
            self._send_json({"error": "Invalid session_id"}, 400)
            return

        idx = _pick_adaptive_question(session)
        if idx is None:
            self._send_json({
                "session_id": sid,
                "complete": True,
                "message": "All questions mastered!",
                "stats": self._build_stats(session),
            })
            return

        session.current_question_idx = idx
        session.phase = "question"
        session.current_micro_check = None
        session.micro_check_attempts = 0
        if idx not in session.asked_indices:
            session.asked_indices.append(idx)

        q = session.questions[idx]
        self._send_json({
            "session_id": sid,
            "complete": False,
            "question": self._format_question(q, idx, len(session.questions)),
            "stats": self._build_stats(session),
        })

    def _handle_session_answer(self):
        body = self._read_body()
        sid = body.get("session_id", "")
        session = _sessions.get(sid)
        if not session:
            self._send_json({"error": "Invalid session_id"}, 400)
            return

        idx = session.current_question_idx
        if idx is None:
            self._send_json({"error": "No current question"}, 400)
            return

        q = session.questions[idx]
        answer_index = body.get("answer_index")  # int or None
        answer_indices = body.get("answer_indices")  # list[int] for multi-select
        idk = body.get("idk", False)  # "I don't know"

        # Determine correctness
        if idk or (answer_index is None and answer_indices is None):
            is_correct = False
            user_answer = "I don't know"
        elif q["multi_select"] and answer_indices is not None:
            is_correct = sorted(answer_indices) == sorted(q["correct_indices"])
            user_answer = ", ".join(q["options"][i] for i in answer_indices if i < len(q["options"]))
        elif answer_index is not None:
            is_correct = answer_index in q["correct_indices"]
            user_answer = q["options"][answer_index] if answer_index < len(q["options"]) else ""
        else:
            is_correct = False
            user_answer = ""

        # Update results
        prev = session.results.get(idx)
        if prev:
            prev.correct = is_correct
            prev.attempts += 1
        else:
            session.results[idx] = QuestionResult(correct=is_correct)

        _update_tag_stats(session, q.get("tags", ["general"]), is_correct)

        # Generate AI feedback
        session.phase = "feedback"
        ai_response = self._generate_feedback(session, q, user_answer, is_correct, idk)

        # Determine if micro-check is needed (wrong or IDK)
        needs_micro_check = not is_correct

        self._send_json({
            "session_id": sid,
            "correct": is_correct,
            "correct_answer": q["correct"],
            "correct_indices": q["correct_indices"],
            "user_answer": user_answer,
            "explanation": q.get("explanation"),
            "ai_response": ai_response,
            "needs_micro_check": needs_micro_check,
            "tags": q.get("tags", []),
            "phase": "teaching" if needs_micro_check else "feedback",
            "stats": self._build_stats(session),
        })

        if is_correct and not idk:
            # Correct on first try with no IDK -> mark mastered
            result = session.results[idx]
            if result.attempts == 1:
                result.micro_check_passed = True
                result.mastered = True

    def _handle_session_microcheck(self):
        body = self._read_body()
        sid = body.get("session_id", "")
        session = _sessions.get(sid)
        if not session:
            self._send_json({"error": "Invalid session_id"}, 400)
            return

        idx = session.current_question_idx
        if idx is None:
            self._send_json({"error": "No current question"}, 400)
            return

        q = session.questions[idx]
        action = body.get("action", "generate")  # "generate" or "check"

        if action == "generate":
            mc = self._generate_micro_check(session, q)
            session.current_micro_check = mc
            session.micro_check_attempts = 0
            session.phase = "micro_check"
            self._send_json({
                "session_id": sid,
                "micro_check": mc,
                "phase": "micro_check",
            })

        elif action == "check":
            mc = session.current_micro_check
            if not mc:
                self._send_json({"error": "No micro-check to check"}, 400)
                return

            user_idx = body.get("answer_index", -1)
            correct = user_idx == mc.get("correct_index", -1)
            session.micro_check_attempts += 1

            if correct:
                # Mark mastered
                result = session.results.get(idx)
                if result:
                    result.micro_check_passed = True
                    result.mastered = True
                session.phase = "question"
                self._send_json({
                    "session_id": sid,
                    "correct": True,
                    "explanation": mc.get("explanation", ""),
                    "mastered": True,
                    "phase": "mastered",
                    "stats": self._build_stats(session),
                })
            else:
                can_retry = session.micro_check_attempts < 2
                self._send_json({
                    "session_id": sid,
                    "correct": False,
                    "explanation": mc.get("explanation", ""),
                    "mastered": False,
                    "can_retry": can_retry,
                    "phase": "micro_check_failed",
                    "stats": self._build_stats(session),
                })

    def _handle_session_status(self):
        # Parse session_id from query string
        path = self.path
        sid = ""
        if "?" in path:
            params = path.split("?", 1)[1]
            for part in params.split("&"):
                if part.startswith("session_id="):
                    sid = part.split("=", 1)[1]

        session = _sessions.get(sid)
        if not session:
            self._send_json({"error": "Invalid session_id"}, 400)
            return

        self._send_json({
            "session_id": sid,
            "stats": self._build_stats(session),
        })

    # --- Chat ---

    def _handle_chat(self):
        body = self._read_body()
        message = body.get("message", "")
        exam_id = body.get("exam_id", "")
        question_context = body.get("question_context", "")
        history = body.get("history", [])

        prompt_parts = []
        if question_context:
            prompt_parts.append(f"Current question context:\n{question_context}\n")
        for entry in history[-6:]:
            role = entry.get("role", "user")
            content = entry.get("content", "")
            prompt_parts.append(f"{role.capitalize()}: {content}")
        prompt_parts.append(f"Student: {message}")
        prompt = "\n\n".join(prompt_parts)

        system = CHAT_SYSTEM
        if exam_id:
            system += f"\n\nTutoring for: {_exam_titles.get(exam_id, exam_id)}"

        response = _ollama_generate(prompt, system=system)
        self._send_json({"response": response})

    # --- Legacy evaluate (backward compat) ---

    def _handle_evaluate_legacy(self):
        body = self._read_body()
        exam_id = body.get("exam_id", "")
        user_answer = body.get("user_answer", "")
        question_text = body.get("question_text", "")
        options = body.get("options", [])
        correct_answer = body.get("correct_answer", "")
        explanation = body.get("explanation", "")

        is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
        options_str = "\n".join(f"  {chr(65+i)}. {opt}" for i, opt in enumerate(options))

        prompt = f"""Question: {question_text}\nOptions:\n{options_str}\n
Correct Answer: {correct_answer}\nStudent's Answer: {user_answer}
Student was: {"CORRECT" if is_correct else "INCORRECT"}"""
        if explanation:
            prompt += f"\nOfficial Explanation: {explanation}"

        response = _ollama_generate(prompt, system=EVALUATE_SYSTEM)
        self._send_json({
            "correct": is_correct,
            "correct_answer": correct_answer,
            "ai_response": response,
        })

    # --- Helpers ---

    def _format_question(self, q: dict, idx: int, total: int) -> dict:
        return {
            "index": idx,
            "question_number": idx + 1,
            "total": total,
            "text": q["question"],
            "options": q["options"],
            "correct_indices": q["correct_indices"],
            "multi_select": q["multi_select"],
            "tags": q.get("tags", []),
            "explanation": q.get("explanation"),
            "references": q.get("references"),
        }

    def _build_stats(self, session: LearningSession) -> dict:
        total = len(session.questions)
        answered = len(session.results)
        correct = sum(1 for r in session.results.values() if r.correct)
        mastered = sum(1 for r in session.results.values() if r.mastered)
        accuracy = correct / answered if answered else 0

        return {
            "total_questions": total,
            "answered": answered,
            "correct": correct,
            "incorrect": answered - correct,
            "mastered": mastered,
            "accuracy": round(accuracy, 2),
            "weak_tags": _get_weak_tags(session),
            "tag_summary": _get_tag_summary(session),
            "mastery_level": (
                "expert" if accuracy >= 0.9 and answered >= 5
                else "advanced" if accuracy >= 0.75 and answered >= 5
                else "intermediate" if accuracy >= 0.55 and answered >= 3
                else "beginner"
            ),
        }

    def _generate_feedback(self, session: LearningSession, q: dict,
                           user_answer: str, is_correct: bool, idk: bool) -> str:
        exam_title = _exam_titles.get(session.exam_id, session.exam_id)
        options_str = "\n".join(f"  {chr(65+i)}. {opt}" for i, opt in enumerate(q["options"]))
        rag_context = _build_related_context(session.exam_id, q)

        prompt = f"""Exam: {exam_title}

Question: {q["question"]}

Options:
{options_str}

Correct Answer: {q["correct"]}
Student's Answer: {user_answer}
Student was: {"CORRECT" if is_correct else "said 'I don't know'" if idk else "INCORRECT"}
"""
        if q.get("explanation"):
            prompt += f"\nOfficial Explanation: {q['explanation']}\n"
        if rag_context:
            prompt += f"\nRelated questions context:\n{rag_context}\n"

        if is_correct:
            prompt += "\nThe student answered correctly. Briefly confirm, explain WHY this is correct, and mention 1-2 related concepts."
        elif idk:
            prompt += "\nThe student said 'I don't know'. Be encouraging. Teach the concept from scratch with 3+ sub-topics. Make it simple and memorable."
        else:
            prompt += "\nThe student answered incorrectly. Explain the misconception, then deep-dive into at least 3 sub-topics. Be encouraging but thorough."

        return _ollama_generate(prompt, system=EVALUATE_SYSTEM)

    def _generate_micro_check(self, session: LearningSession, q: dict) -> dict:
        """Generate a micro-check question via Ollama, with rule-based fallback."""
        exam_title = _exam_titles.get(session.exam_id, session.exam_id)

        prompt = f"""Based on this exam question and its correct answer, generate a SHORT verification question.

Original question: {q["question"]}
Correct answer: {q["correct"]}
Topic tags: {", ".join(q.get("tags", []))}
Exam: {exam_title}

Generate a simple true/false or 2-option question that tests if the student understood the core concept.
Return ONLY valid JSON: {{"question": "...", "options": ["correct", "wrong"], "correct_index": 0, "explanation": "..."}}"""

        response = _ollama_generate(prompt, system=MICRO_CHECK_SYSTEM, temperature=0.3)

        # Try to parse JSON from response
        try:
            # Find JSON in response
            json_match = re.search(r'\{[^{}]*"question"[^{}]*\}', response, re.DOTALL)
            if json_match:
                mc = json.loads(json_match.group())
                if "question" in mc and "options" in mc and len(mc["options"]) >= 2:
                    return {
                        "question": mc["question"],
                        "options": mc["options"][:2],
                        "correct_index": mc.get("correct_index", 0),
                        "explanation": mc.get("explanation", ""),
                    }
        except (json.JSONDecodeError, KeyError):
            pass

        # Fallback: rule-based micro-check
        return self._fallback_micro_check(q)

    def _fallback_micro_check(self, q: dict) -> dict:
        """Generate a simple rule-based micro-check from the question data."""
        correct = q["correct"]
        options = q["options"]

        # Pick a wrong option
        wrong_options = [o for i, o in enumerate(options) if i not in q["correct_indices"]]
        wrong = random.choice(wrong_options) if wrong_options else "None of the above"

        # Create a simple "which is correct" question
        tags = q.get("tags", ["this topic"])
        tag_str = tags[0].replace("_", " ") if tags else "this topic"

        # Randomize option order
        if random.random() > 0.5:
            return {
                "question": f"Regarding {tag_str}: which statement is correct?",
                "options": [correct, wrong],
                "correct_index": 0,
                "explanation": f"The correct answer is: {correct}",
            }
        else:
            return {
                "question": f"Regarding {tag_str}: which statement is correct?",
                "options": [wrong, correct],
                "correct_index": 1,
                "explanation": f"The correct answer is: {correct}",
            }

    def log_message(self, fmt, *args):
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
        print(f"[tutor] WARNING: Ollama not detected. Start with: ollama serve", file=sys.stderr)

    server = HTTPServer((HOST, PORT), TutorHandler)
    print(f"[tutor] AI Tutor backend running on http://{HOST}:{PORT}", file=sys.stderr)
    print(f"[tutor] Session endpoints:", file=sys.stderr)
    print(f"[tutor]   POST /api/session/start    - Start learning session", file=sys.stderr)
    print(f"[tutor]   POST /api/session/next     - Get next question (adaptive)", file=sys.stderr)
    print(f"[tutor]   POST /api/session/answer   - Submit answer", file=sys.stderr)
    print(f"[tutor]   POST /api/session/microcheck - Micro-check loop", file=sys.stderr)
    print(f"[tutor]   GET  /api/session/status   - Session stats", file=sys.stderr)
    print(f"[tutor]   POST /api/chat             - Free chat", file=sys.stderr)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[tutor] Shutting down...", file=sys.stderr)
        server.server_close()


if __name__ == "__main__":
    main()
