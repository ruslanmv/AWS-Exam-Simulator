"""A2A-compatible HTTP server for the AWS Exam Tutor Agent.

Compatible with Context Forge's A2A routing. Accepts both:
  - Context Forge envelope: {interaction_type, protocol_version, parameters}
  - Simple format: {message, conversation_id, ...}

Endpoints:
  POST /a2a/invoke                    - Invoke the tutor agent
  POST /a2a                           - Alias for /a2a/invoke
  GET  /a2a/health                    - Health check
  GET  /a2a/card                      - Agent card (A2A discovery)
  GET  /.well-known/a2a/agent.json    - Agent manifest (Context Forge)
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

from .agent import ExamTutorAgent
from .config import load_config

logger = logging.getLogger("aws-exam-tutor-server")

# Store active sessions per conversation
_sessions: dict[str, dict[str, Any]] = {}

# Agent manifest for Context Forge registration
AGENT_MANIFEST = {
    "name": "aws-exam-tutor",
    "version": "1.0.0",
    "description": (
        "AI-powered AWS exam tutor that adaptively teaches certification "
        "content. Supports learning, practice, and exam modes with "
        "teach-until-learned methodology."
    ),
    "interaction_types": ["query"],
    "protocol_version": "v1",
    "input_schema": {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "Optional user identifier"},
            "exam_id": {"type": "string", "description": "Exam ID to study"},
            "mode": {"type": "string", "enum": ["learning", "practice", "exam"]},
            "message": {"type": "string", "description": "User message or answer"},
            "session_id": {"type": "string", "description": "Active session ID"},
        },
        "required": ["message"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "session_id": {"type": "string"},
            "ui": {"type": "object"},
        },
        "required": ["message"],
    },
    "required_tools": [
        "exam_list",
        "exam_start_session",
        "exam_next_question",
        "exam_submit_answer",
        "exam_get_explanation",
        "session_get_status",
    ],
    "endpoints": {
        "invoke": "/a2a/invoke",
        "health": "/a2a/health",
        "card": "/a2a/card",
        "manifest": "/.well-known/a2a/agent.json",
    },
}


def _extract_message_from_request(request: dict) -> tuple[str, str, dict]:
    """Extract message, conversation_id, and extra params from request.

    Handles both Context Forge envelope and simple format.
    Returns (message, conversation_id, extra_params).
    """
    # Context Forge envelope format
    if "interaction_type" in request and "parameters" in request:
        params = request.get("parameters", {})
        message = params.get("message", "")
        conv_id = params.get("conversation_id", params.get("session_id", str(uuid.uuid4())))
        return message, conv_id, params

    # Simple format
    message = request.get("message", "")
    conv_id = request.get("conversation_id", str(uuid.uuid4()))
    return message, conv_id, request


def _wrap_response(result: dict, request: dict) -> dict:
    """Wrap response in Context Forge envelope if request used it."""
    if "interaction_type" in request and "protocol_version" in request:
        return {
            "protocol_version": request.get("protocol_version", "v1"),
            "interaction_type": request.get("interaction_type", "query"),
            "result": result,
        }
    return result


class TutorRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler for A2A requests."""

    agent: ExamTutorAgent  # set at class level

    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/a2a/health":
            self._json_response(200, {"status": "healthy", "agent": "aws-exam-tutor"})
        elif self.path == "/a2a/card":
            self._json_response(200, AGENT_MANIFEST)
        elif self.path == "/.well-known/a2a/agent.json":
            self._json_response(200, AGENT_MANIFEST)
        else:
            self._json_response(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path in ("/a2a/invoke", "/a2a"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                request = json.loads(body)
            except json.JSONDecodeError:
                self._json_response(400, {"error": "invalid JSON"})
                return

            result = asyncio.get_event_loop().run_until_complete(
                self._handle_invoke(request)
            )
            self._json_response(200, _wrap_response(result, request))
        else:
            self._json_response(404, {"error": "not found"})

    async def _handle_invoke(self, request: dict) -> dict:
        """Handle an A2A invoke request."""
        message, conversation_id, params = _extract_message_from_request(request)

        # Get or create session context
        ctx = _sessions.setdefault(conversation_id, {"session_id": None})

        try:
            msg_lower = message.lower().strip()

            if not ctx["session_id"] and ("list" in msg_lower or "exams" in msg_lower or "start" in msg_lower or not ctx.get("initialized")):
                ctx["initialized"] = True
                result = await self.agent.call_tool("exam_list", {})
                return {
                    "conversation_id": conversation_id,
                    "message": "Available exams:\n" + "\n".join(
                        f"- **{e['exam_id']}**: {e.get('title', '')} ({e['question_count']} questions)"
                        for e in result.get("exams", [])
                    ) + "\n\nWhich exam would you like to study? Tell me the exam ID.",
                    "session_id": None,
                    "ui": {"phase": "select_exam", "exams": result.get("exams", [])},
                }

            # Start session if exam ID mentioned
            if not ctx["session_id"]:
                exam_id = params.get("exam_id", "")
                if not exam_id:
                    exams = await self.agent.call_tool("exam_list", {})
                    exam_ids = [e["exam_id"] for e in exams.get("exams", [])]
                    for eid in exam_ids:
                        if eid.lower() in msg_lower or eid.lower().replace("-", "") in msg_lower.replace("-", ""):
                            exam_id = eid
                            break

                if exam_id:
                    mode = params.get("mode", "learning")
                    session = await self.agent.call_tool("exam_start_session", {
                        "exam_id": exam_id, "mode": mode,
                    })
                    ctx["session_id"] = session["session_id"]
                    ctx["exam_id"] = exam_id

                    q = await self.agent.call_tool("exam_next_question", {
                        "session_id": ctx["session_id"],
                    })
                    ctx["current_question_id"] = q["question_id"]

                    options_text = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(q["options"]))
                    return {
                        "conversation_id": conversation_id,
                        "message": (
                            f"Session started for **{exam_id}** ({session['total_questions']} questions).\n\n"
                            f"**Question {q['question_number']}/{q['total_questions']}** "
                            f"[{', '.join(q.get('tags', []))}]\n\n"
                            f"{q['question']}\n\n{options_text}\n\nWhat's your answer?"
                        ),
                        "session_id": ctx["session_id"],
                        "ui": {"phase": "question", "question": q},
                    }

                return {
                    "conversation_id": conversation_id,
                    "message": "Please specify which exam you'd like to study.",
                    "session_id": None,
                }

            # Handle answer submission
            if ctx.get("current_question_id"):
                submit_args: dict[str, Any] = {
                    "session_id": ctx["session_id"],
                    "question_id": ctx["current_question_id"],
                }
                try:
                    idx = int(msg_lower.strip()) - 1
                    submit_args["answer_index"] = idx
                except ValueError:
                    submit_args["answer_text"] = message.strip()

                result = await self.agent.call_tool("exam_submit_answer", submit_args)

                response_parts = []
                if result["correct"]:
                    response_parts.append("**Correct!**")
                else:
                    response_parts.append("**Incorrect.**")
                    response_parts.append(f"The correct answer is: {result['correct_answer']}")

                if result.get("explanation"):
                    response_parts.append(f"\n**Explanation:** {result['explanation']}")

                q = await self.agent.call_tool("exam_next_question", {
                    "session_id": ctx["session_id"],
                })

                if "error" in q:
                    status = await self.agent.call_tool("session_get_status", {
                        "session_id": ctx["session_id"],
                    })
                    response_parts.append(f"\n\n**Session Complete!**\n"
                                          f"Score: {status['correct_count']}/{status['asked_count']} "
                                          f"({status['accuracy']:.0%})\n"
                                          f"Mastery: {status['mastery_level']}")
                    ctx["current_question_id"] = None
                    ui_phase = "complete"
                    ui_data = {"phase": "complete", "status": status}
                else:
                    ctx["current_question_id"] = q["question_id"]
                    options_text = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(q["options"]))
                    response_parts.append(
                        f"\n\n**Question {q['question_number']}/{q['total_questions']}** "
                        f"[{', '.join(q.get('tags', []))}]\n\n"
                        f"{q['question']}\n\n{options_text}\n\nWhat's your answer?"
                    )
                    ui_data = {"phase": "question", "question": q, "previous_result": result}

                return {
                    "conversation_id": conversation_id,
                    "message": "\n".join(response_parts),
                    "session_id": ctx["session_id"],
                    "ui": ui_data,
                }

        except Exception as e:
            logger.exception("Error handling invoke")
            return {
                "conversation_id": conversation_id,
                "message": f"Error: {str(e)}",
                "session_id": ctx.get("session_id"),
            }

        return {
            "conversation_id": conversation_id,
            "message": "I'm not sure what you'd like to do. Try 'list exams' or answer the current question.",
            "session_id": ctx.get("session_id"),
        }

    def _json_response(self, status: int, data: dict) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._send_cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        logger.info(format, *args)


def run_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Run the A2A HTTP server."""
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stderr)])

    config = load_config()
    agent = ExamTutorAgent(config)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(agent._setup_direct_tools())

    TutorRequestHandler.agent = agent

    server = HTTPServer((host, port), TutorRequestHandler)
    logger.info("AWS Exam Tutor A2A server running on %s:%d", host, port)
    logger.info("Endpoints: /a2a/invoke, /a2a/health, /a2a/card, /.well-known/a2a/agent.json")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down.")
        server.server_close()
