"""AWS Exam Tutor Agent - LangChain-based A2A agent runtime.

This agent:
1. Connects to the AWS Exam Tools MCP server (stdio or gateway)
2. Uses an LLM with the tutor system prompt to orchestrate exam sessions
3. Adaptively teaches until the user demonstrates understanding
4. Exposes an A2A-compatible endpoint for Context Forge integration

Can run standalone (interactive CLI) or as an HTTP server (A2A endpoint).
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from .config import AgentConfig, load_config

logger = logging.getLogger("aws-exam-tutor")


class ExamTutorAgent:
    """Orchestrates the exam tutoring loop using MCP tools + LLM."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._system_prompt = self._load_system_prompt()
        self._mcp_tools: dict[str, Any] = {}

    def _load_system_prompt(self) -> str:
        """Load the system prompt from file or use default."""
        default_prompt = (
            "You are an AWS Exam Tutor. Help the user study for AWS certification "
            "exams using the available tools. Ask questions, grade answers, and "
            "teach concepts until the user masters them."
        )

        if self.config.system_prompt_file:
            p = Path(self.config.system_prompt_file)
            if p.exists():
                return p.read_text(encoding="utf-8")
            logger.warning("System prompt file not found: %s. Using default.", p)

        return default_prompt

    async def _setup_mcp_client(self) -> None:
        """Set up connection to the MCP server."""
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            server_params = StdioServerParameters(
                command=self.config.mcp_server_command,
                env={
                    "AWS_EXAM_QUESTION_DIR": self.config.question_dir,
                    "AWS_EXAM_DB_PATH": self.config.db_path,
                },
            )

            self._stdio_transport = await stdio_client(server_params).__aenter__()
            read, write = self._stdio_transport
            self._mcp_session = ClientSession(read, write)
            await self._mcp_session.__aenter__()
            await self._mcp_session.initialize()

            # Discover tools
            tools_result = await self._mcp_session.list_tools()
            for tool in tools_result.tools:
                self._mcp_tools[tool.name] = tool
                logger.info("MCP tool discovered: %s", tool.name)

        except ImportError:
            logger.warning("MCP client library not installed. Using direct import fallback.")
            await self._setup_direct_tools()

    async def _setup_direct_tools(self) -> None:
        """Fallback: import tool logic directly without MCP/FastMCP protocol.

        This bypasses FastMCP entirely and uses the underlying exam_bank,
        session_store, and tagging modules directly. This is useful for:
        - Testing without FastMCP dependencies
        - Environments where FastMCP's auth deps (cryptography) are unavailable
        - Lightweight deployments
        """
        import os
        import random

        sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_server" / "src"))
        from aws_exam_tools.exam_bank import ExamBank
        from aws_exam_tools.session_store import SessionStore
        from aws_exam_tools.tagging import infer_tags
        from aws_exam_tools.models import (
            ExamInfo, ExamListResponse, ExplanationResponse,
            NextQuestionResponse, SessionStatusResponse,
            StartSessionResponse, SubmitAnswerResponse,
        )

        # Resolve question directory
        question_dir = self.config.question_dir
        if not question_dir:
            question_dir = os.getenv("AWS_EXAM_QUESTION_DIR", "")
        if not question_dir:
            question_dir = str(Path(__file__).parent.parent / "questions")

        db_path = self.config.db_path
        if not db_path:
            db_path = os.getenv("AWS_EXAM_DB_PATH", "./state/aws_exam.sqlite")

        bank = ExamBank(Path(question_dir))
        bank.load_all()
        store = SessionStore(Path(db_path))

        # Build tool functions that mirror the MCP server's async tools

        async def exam_list_tool() -> dict:
            exams = [
                ExamInfo(exam_id=eid, title=bank.get_title(eid), question_count=count)
                for eid, count in bank.list_exams().items()
            ]
            return ExamListResponse(exams=exams).model_dump()

        async def exam_start_session_tool(exam_id: str, mode: str = "learning", user_id: str | None = None) -> dict:
            total = bank.question_count(exam_id)
            s = store.create(exam_id=exam_id, mode=mode, user_id=user_id)
            return StartSessionResponse(
                session_id=s.session_id, exam_id=exam_id, mode=mode, total_questions=total,
            ).model_dump()

        async def exam_next_question_tool(session_id: str) -> dict:
            s = store.load(session_id)
            total = bank.question_count(s.exam_id)
            all_ids = set(bank.all_question_ids(s.exam_id))
            seen_ids = set(s.asked_ids)
            unseen_ids = all_ids - seen_ids

            if not unseen_ids:
                if s.mode == "exam":
                    return {"error": "exam_complete", "message": "All questions answered."}
                unseen_ids = all_ids

            unseen_list = list(unseen_ids)
            # Adaptive: bias toward weak tags
            if s.mode in ("learning", "practice"):
                weak = store.weak_tags(session_id, min_asked=2, top_n=3)
                if weak:
                    candidates = []
                    for qid in unseen_list:
                        q = bank.get_question_by_id(qid)
                        tags = infer_tags(q.question)
                        if any(t in tags for t in weak):
                            candidates.append(qid)
                    if candidates:
                        unseen_list = candidates

            chosen_id = random.choice(unseen_list)
            q = bank.get_question_by_id(chosen_id)
            tags = infer_tags(q.question)
            return NextQuestionResponse(
                session_id=session_id, exam_id=s.exam_id, question_id=q.question_id,
                question_number=len(s.asked_ids) + 1, total_questions=total,
                question=q.question, options=q.options, tags=tags, multi_select=q.multi_select,
            ).model_dump()

        async def exam_submit_answer_tool(
            session_id: str, question_id: str,
            answer_text: str | None = None, answer_index: int | None = None,
        ) -> dict:
            s = store.load(session_id)
            q = bank.get_question_by_id(question_id)

            # Normalize answer
            if answer_text is not None and answer_text.strip():
                submitted = answer_text.strip()
            elif answer_index is not None:
                submitted = q.options[answer_index].strip()
            else:
                raise ValueError("Provide answer_text or answer_index")

            # Check correctness
            correct = (
                submitted.strip() == q.correct.strip()
                or submitted.strip().lower() == q.correct.strip().lower()
            )

            tags = infer_tags(q.question)
            store.record_answer(session_id=session_id, question_id=question_id, tags=tags, correct=correct)

            remediation: dict = {"tags": tags}
            if not correct:
                remediation["teaching_steps"] = [
                    "Explain the underlying AWS concept in 3-6 concise steps.",
                    "Point out the common misconception that leads to the wrong choice.",
                    "Give a real-world analogy to make the concept memorable.",
                    "Ask a short check question to verify the user understood.",
                ]
            else:
                remediation["reinforcement"] = "Confirm why this answer is correct."

            return SubmitAnswerResponse(
                session_id=session_id, question_id=question_id, correct=correct,
                submitted=submitted, correct_answer=q.correct,
                explanation=q.explanation, references=q.references, remediation=remediation,
            ).model_dump()

        async def exam_get_explanation_tool(question_id: str) -> dict:
            q = bank.get_question_by_id(question_id)
            return ExplanationResponse(
                question_id=question_id, question=q.question,
                correct_answer=q.correct, explanation=q.explanation, references=q.references,
            ).model_dump()

        async def session_get_status_tool(session_id: str) -> dict:
            s = store.load(session_id)
            total = bank.question_count(s.exam_id)
            asked = len(s.asked_ids)
            accuracy = (s.correct_count / asked) if asked else 0.0
            return SessionStatusResponse(
                session_id=session_id, exam_id=s.exam_id, mode=s.mode,
                asked_count=asked, correct_count=s.correct_count,
                incorrect_count=s.incorrect_count, accuracy=round(accuracy, 4),
                weak_tags=store.weak_tags(session_id, min_asked=2, top_n=5),
                strong_tags=store.strong_tags(session_id, min_asked=3, top_n=5),
                remaining_questions=max(0, total - asked),
                mastery_level=store.mastery_level(session_id),
            ).model_dump()

        self._mcp_tools = {
            "exam_list": exam_list_tool,
            "exam_start_session": exam_start_session_tool,
            "exam_next_question": exam_next_question_tool,
            "exam_submit_answer": exam_submit_answer_tool,
            "exam_get_explanation": exam_get_explanation_tool,
            "session_get_status": session_get_status_tool,
        }
        self._direct_mode = True
        logger.info("Loaded %d tools via direct import (no FastMCP)", len(self._mcp_tools))

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Call an MCP tool by name."""
        if hasattr(self, "_mcp_session"):
            result = await self._mcp_session.call_tool(name, arguments)
            # Parse the MCP result
            if result.content:
                for item in result.content:
                    if hasattr(item, "text"):
                        return json.loads(item.text)
            return {}
        elif hasattr(self, "_direct_mode") and self._direct_mode:
            func = self._mcp_tools[name]
            return await func(**arguments)
        else:
            raise RuntimeError("MCP not initialized")

    async def run_interactive(self) -> None:
        """Run the agent in interactive CLI mode."""
        await self._setup_direct_tools()

        print("\n" + "=" * 60)
        print("  AWS Exam Tutor Agent - Interactive Mode")
        print("=" * 60)
        print("\nType 'quit' to exit, 'status' to check progress.\n")

        # Show available exams
        exams = await self.call_tool("exam_list", {})
        print("Available exams:")
        for exam in exams.get("exams", []):
            print(f"  - {exam['exam_id']}: {exam.get('title', '')} ({exam['question_count']} questions)")

        # Get exam choice
        print()
        exam_id = input("Which exam would you like to study? Enter exam ID: ").strip()

        # Start session
        try:
            session = await self.call_tool("exam_start_session", {
                "exam_id": exam_id,
                "mode": "learning",
            })
        except (KeyError, Exception) as e:
            print(f"Error: {e}")
            return

        session_id = session["session_id"]
        print(f"\nSession started! ({session['total_questions']} questions available)")
        print("Mode: Learning (adaptive - focuses on your weak areas)\n")

        question_count = 0
        while True:
            # Get next question
            q_result = await self.call_tool("exam_next_question", {
                "session_id": session_id,
            })

            if "error" in q_result:
                print(f"\n{q_result['message']}")
                break

            question_count += 1
            qid = q_result["question_id"]
            tags = q_result.get("tags", [])

            print(f"\n{'─' * 50}")
            print(f"Question {q_result['question_number']}/{q_result['total_questions']}  "
                  f"[{', '.join(tags)}]")
            print(f"{'─' * 50}")
            print(f"\n{q_result['question']}\n")

            for i, opt in enumerate(q_result["options"]):
                print(f"  {i + 1}. {opt}")

            # Get answer
            print()
            answer = input("Your answer (number or text, 'skip' to skip, 'quit' to exit): ").strip()

            if answer.lower() == "quit":
                break
            if answer.lower() == "skip":
                explanation = await self.call_tool("exam_get_explanation", {
                    "question_id": qid,
                })
                if explanation.get("explanation"):
                    print(f"\nCorrect answer: {explanation['correct_answer']}")
                    print(f"Explanation: {explanation['explanation']}")
                continue
            if answer.lower() == "status":
                status = await self.call_tool("session_get_status", {
                    "session_id": session_id,
                })
                self._print_status(status)
                continue

            # Submit answer
            submit_args: dict[str, Any] = {
                "session_id": session_id,
                "question_id": qid,
            }
            try:
                idx = int(answer) - 1
                submit_args["answer_index"] = idx
            except ValueError:
                submit_args["answer_text"] = answer

            try:
                result = await self.call_tool("exam_submit_answer", submit_args)
            except (ValueError, Exception) as e:
                print(f"Error: {e}")
                continue

            if result["correct"]:
                print("\n  Correct!")
                if result.get("explanation"):
                    print(f"\n  {result['explanation'][:200]}...")
            else:
                print(f"\n  Incorrect.")
                print(f"  Correct answer: {result['correct_answer']}")
                if result.get("explanation"):
                    print(f"\n  Explanation: {result['explanation']}")
                remediation = result.get("remediation", {})
                if remediation.get("teaching_steps"):
                    print("\n  Teaching steps:")
                    for step in remediation["teaching_steps"]:
                        print(f"    - {step}")

            # Periodic status check
            if question_count % 5 == 0:
                status = await self.call_tool("session_get_status", {
                    "session_id": session_id,
                })
                print(f"\n  Progress: {status['correct_count']}/{status['asked_count']} correct "
                      f"({status['accuracy']:.0%}) | Level: {status['mastery_level']}")
                if status["weak_tags"]:
                    print(f"  Weak areas: {', '.join(status['weak_tags'])}")

        # Final summary
        print("\n" + "=" * 60)
        print("  Session Summary")
        print("=" * 60)
        status = await self.call_tool("session_get_status", {
            "session_id": session_id,
        })
        self._print_status(status)

    def _print_status(self, status: dict) -> None:
        """Print a formatted status summary."""
        print(f"\n  Exam: {status['exam_id']}")
        print(f"  Questions answered: {status['asked_count']}")
        print(f"  Correct: {status['correct_count']}")
        print(f"  Incorrect: {status['incorrect_count']}")
        print(f"  Accuracy: {status['accuracy']:.1%}")
        print(f"  Mastery: {status['mastery_level']}")
        print(f"  Remaining: {status['remaining_questions']}")
        if status["weak_tags"]:
            print(f"  Weak areas: {', '.join(status['weak_tags'])}")
        if status["strong_tags"]:
            print(f"  Strong areas: {', '.join(status['strong_tags'])}")


async def main_interactive() -> None:
    """Entry point for interactive CLI mode."""
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stderr)])
    config = load_config()
    agent = ExamTutorAgent(config)
    await agent.run_interactive()
