"""A2A-compatible HTTP server for the AWS Exam Tutor Agent.

Exposes the tutor agent as an HTTP endpoint that can be registered
with Context Forge's A2A routing.

Endpoints:
  POST /a2a/invoke   - Invoke the tutor agent with a message
  GET  /a2a/health   - Health check
  GET  /a2a/card     - Agent card (A2A discovery)
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

from .agent import ExamTutorAgent
from .config import load_config

logger = logging.getLogger("aws-exam-tutor-server")

# Store active sessions per conversation
_sessions: dict[str, dict[str, Any]] = {}


class TutorRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler for A2A requests."""

    agent: ExamTutorAgent  # set at class level

    def do_GET(self) -> None:
        if self.path == "/a2a/health":
            self._json_response(200, {"status": "healthy", "agent": "aws-exam-tutor"})
        elif self.path == "/a2a/card":
            self._json_response(200, self._agent_card())
        else:
            self._json_response(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path == "/a2a/invoke":
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
            self._json_response(200, result)
        else:
            self._json_response(404, {"error": "not found"})

    async def _handle_invoke(self, request: dict) -> dict:
        """Handle an A2A invoke request."""
        message = request.get("message", "")
        conversation_id = request.get("conversation_id", str(uuid.uuid4()))

        # Get or create session context
        ctx = _sessions.setdefault(conversation_id, {"session_id": None})

        try:
            # Simple command routing based on message content
            msg_lower = message.lower().strip()

            if not ctx["session_id"] and ("list" in msg_lower or "exams" in msg_lower or "start" in msg_lower or not ctx.get("initialized")):
                ctx["initialized"] = True
                result = await self.agent.call_tool("exam_list", {})
                return {
                    "conversation_id": conversation_id,
                    "response": "Available exams:\n" + "\n".join(
                        f"- **{e['exam_id']}**: {e.get('title', '')} ({e['question_count']} questions)"
                        for e in result.get("exams", [])
                    ) + "\n\nWhich exam would you like to study? Tell me the exam ID.",
                    "metadata": {"exams": result},
                }

            # Start session if exam ID mentioned and no session
            if not ctx["session_id"]:
                exams = await self.agent.call_tool("exam_list", {})
                exam_ids = [e["exam_id"] for e in exams.get("exams", [])]
                for eid in exam_ids:
                    if eid.lower() in msg_lower or eid.lower().replace("-", "") in msg_lower.replace("-", ""):
                        session = await self.agent.call_tool("exam_start_session", {
                            "exam_id": eid, "mode": "learning",
                        })
                        ctx["session_id"] = session["session_id"]
                        ctx["exam_id"] = eid

                        # Get first question
                        q = await self.agent.call_tool("exam_next_question", {
                            "session_id": ctx["session_id"],
                        })
                        ctx["current_question_id"] = q["question_id"]

                        options_text = "\n".join(
                            f"{i+1}. {opt}" for i, opt in enumerate(q["options"])
                        )
                        return {
                            "conversation_id": conversation_id,
                            "response": (
                                f"Session started for **{eid}** ({session['total_questions']} questions).\n\n"
                                f"**Question {q['question_number']}/{q['total_questions']}** "
                                f"[{', '.join(q.get('tags', []))}]\n\n"
                                f"{q['question']}\n\n{options_text}\n\nWhat's your answer?"
                            ),
                            "metadata": {"question": q},
                        }

                return {
                    "conversation_id": conversation_id,
                    "response": "Please specify which exam you'd like to study.",
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

                # Get next question
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
                else:
                    ctx["current_question_id"] = q["question_id"]
                    options_text = "\n".join(
                        f"{i+1}. {opt}" for i, opt in enumerate(q["options"])
                    )
                    response_parts.append(
                        f"\n\n**Question {q['question_number']}/{q['total_questions']}** "
                        f"[{', '.join(q.get('tags', []))}]\n\n"
                        f"{q['question']}\n\n{options_text}\n\nWhat's your answer?"
                    )

                return {
                    "conversation_id": conversation_id,
                    "response": "\n".join(response_parts),
                    "metadata": {"result": result},
                }

        except Exception as e:
            logger.exception("Error handling invoke")
            return {
                "conversation_id": conversation_id,
                "response": f"Error: {str(e)}",
            }

        return {
            "conversation_id": conversation_id,
            "response": "I'm not sure what you'd like to do. Try 'list exams' or answer the current question.",
        }

    def _agent_card(self) -> dict:
        """Return A2A agent card for discovery."""
        return {
            "name": "aws-exam-tutor",
            "description": (
                "AI-powered AWS exam tutor that adaptively teaches certification "
                "content. Supports learning, practice, and exam modes with "
                "teach-until-learned methodology."
            ),
            "version": "1.0.0",
            "capabilities": [
                "exam_list",
                "exam_start_session",
                "exam_next_question",
                "exam_submit_answer",
                "exam_get_explanation",
                "session_get_status",
            ],
            "supported_exams": [
                "SAA-C03", "SAP-C02", "CLF-C02", "DOP-C02",
                "MLS-C01", "AI-900", "AI-102", "DP-100",
                "GCP-ML", "GCP-CA",
            ],
            "modes": ["learning", "practice", "exam"],
            "endpoints": {
                "invoke": "/a2a/invoke",
                "health": "/a2a/health",
                "card": "/a2a/card",
            },
        }

    def _json_response(self, status: int, data: dict) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        logger.info(format, *args)


def run_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Run the A2A HTTP server."""
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stderr)])

    config = load_config()
    agent = ExamTutorAgent(config)

    # Initialize tools synchronously
    loop = asyncio.new_event_loop()
    loop.run_until_complete(agent._setup_direct_tools())

    TutorRequestHandler.agent = agent

    server = HTTPServer((host, port), TutorRequestHandler)
    logger.info("AWS Exam Tutor A2A server running on %s:%d", host, port)
    logger.info("Endpoints: /a2a/invoke, /a2a/health, /a2a/card")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down.")
        server.server_close()
