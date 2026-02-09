"""AWS Exam Tools - FastMCP Server.

Enterprise MCP server exposing exam simulator tools:
  - exam_list: List available exams
  - exam_start_session: Start a new exam session
  - exam_next_question: Get next question (adaptive in learning mode)
  - exam_submit_answer: Submit an answer, get feedback + remediation
  - exam_get_explanation: Get explanation for any question
  - session_get_status: Check session accuracy, weak areas, mastery

Environment variables:
  AWS_EXAM_QUESTION_DIR: Path to directory containing *.json question banks
  AWS_EXAM_DB_PATH: Path to SQLite database file (default: ./state/aws_exam.sqlite)

IMPORTANT: All logging goes to stderr to avoid corrupting MCP stdio protocol.
"""
from __future__ import annotations

import logging
import os
import random
import sys
from pathlib import Path

from fastmcp import FastMCP

from .exam_bank import ExamBank
from .models import (
    ExamInfo,
    ExamListResponse,
    ExplanationResponse,
    NextQuestionResponse,
    SessionStatusResponse,
    StartSessionResponse,
    SubmitAnswerResponse,
)
from .session_store import SessionStore
from .tagging import infer_tags

# Log to stderr only - never stdout (stdio MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("aws-exam-tools")

# --- Server setup ---

mcp = FastMCP(
    name="aws-exam-tools",
    version="1.0.0",
    description="Enterprise MCP server for AWS exam simulation with adaptive learning.",
)


def _settings() -> tuple[Path, Path]:
    """Read configuration from environment."""
    question_dir = os.getenv("AWS_EXAM_QUESTION_DIR", "")
    if not question_dir:
        # Default: look for questions/ relative to project root
        project_root = Path(__file__).resolve().parents[4]
        question_dir = str(project_root / "questions")

    qpath = Path(question_dir).expanduser().resolve()
    db_path = Path(
        os.getenv("AWS_EXAM_DB_PATH", "./state/aws_exam.sqlite")
    ).expanduser().resolve()

    return qpath, db_path


QUESTION_DIR, DB_PATH = _settings()
BANK = ExamBank(QUESTION_DIR)
BANK.load_all()
STORE = SessionStore(DB_PATH)

logger.info("Loaded %d exams from %s", len(BANK.list_exams()), QUESTION_DIR)
for eid, count in BANK.list_exams().items():
    logger.info("  %s: %d questions (%s)", eid, count, BANK.get_title(eid))


# --- MCP Tools ---


@mcp.tool(
    description=(
        "List all available exams. Returns exam IDs, titles, and question counts. "
        "Use this to let the user choose which exam to study."
    ),
)
async def exam_list() -> dict:
    """List available exams derived from *.json files in the question bank."""
    exams = [
        ExamInfo(
            exam_id=eid,
            title=BANK.get_title(eid),
            question_count=count,
        )
        for eid, count in BANK.list_exams().items()
    ]
    return ExamListResponse(exams=exams).model_dump()


@mcp.tool(
    description=(
        "Start a new exam session. Returns a session_id to use with other tools. "
        "Modes: 'learning' (adaptive, teaches until learned), 'practice' (all questions, feedback after each), "
        "'exam' (timed, no feedback until end)."
    ),
)
async def exam_start_session(
    exam_id: str,
    mode: str = "learning",
    user_id: str | None = None,
) -> dict:
    """Start a new exam session."""
    total = BANK.question_count(exam_id)  # validates exam exists
    s = STORE.create(exam_id=exam_id, mode=mode, user_id=user_id)
    return StartSessionResponse(
        session_id=s.session_id,
        exam_id=exam_id,
        mode=mode,
        total_questions=total,
    ).model_dump()


def _pick_next_question_id(session_id: str) -> tuple[str, int]:
    """Adaptive question selection algorithm.

    In learning mode:
    - Biases toward weak-tag questions when weak areas are detected
    - Picks unseen questions first
    - Recycles questions when all have been seen (practice/learning)

    Returns (question_id, question_number_1_indexed).
    """
    s = STORE.load(session_id)
    total = BANK.question_count(s.exam_id)

    # Build unseen set
    all_ids = set(BANK.all_question_ids(s.exam_id))
    seen_ids = set(s.asked_ids)
    unseen_ids = all_ids - seen_ids

    if not unseen_ids:
        # All questions seen - recycle in learning/practice, end in exam
        if s.mode == "exam":
            raise StopIteration("All questions answered in exam mode")
        unseen_ids = all_ids  # recycle

    unseen_list = list(unseen_ids)

    # In learning mode, bias toward weak areas
    if s.mode in ("learning", "practice"):
        weak = STORE.weak_tags(session_id, min_asked=2, top_n=3)
        if weak:
            # Find unseen questions matching weak tags
            candidates = []
            for qid in unseen_list:
                q = BANK.get_question_by_id(qid)
                tags = infer_tags(q.question)
                if any(t in tags for t in weak):
                    candidates.append(qid)
            if candidates:
                chosen = random.choice(candidates)
                q = BANK.get_question_by_id(chosen)
                return chosen, len(s.asked_ids) + 1

    # Default: random unseen
    chosen = random.choice(unseen_list)
    return chosen, len(s.asked_ids) + 1


@mcp.tool(
    description=(
        "Get the next question for a session. In learning mode, adaptively selects "
        "questions from the user's weak areas. Returns the question text, options, "
        "and domain tags."
    ),
)
async def exam_next_question(session_id: str) -> dict:
    """Get the next question for this session."""
    s = STORE.load(session_id)
    total = BANK.question_count(s.exam_id)

    try:
        qid, qnum = _pick_next_question_id(session_id)
    except StopIteration:
        return {
            "error": "exam_complete",
            "message": "All questions have been answered. Use session_get_status to see results.",
        }

    q = BANK.get_question_by_id(qid)
    tags = infer_tags(q.question)

    return NextQuestionResponse(
        session_id=session_id,
        exam_id=s.exam_id,
        question_id=q.question_id,
        question_number=qnum,
        total_questions=total,
        question=q.question,
        options=q.options,
        tags=tags,
        multi_select=q.multi_select,
    ).model_dump()


def _normalize_answer(options: list[str], answer_text: str | None, answer_index: int | None) -> str:
    """Normalize user answer to option text."""
    if answer_text is not None and answer_text.strip():
        return answer_text.strip()
    if answer_index is not None:
        if answer_index < 0 or answer_index >= len(options):
            raise ValueError(f"answer_index {answer_index} out of range (0..{len(options)-1})")
        return options[answer_index].strip()
    raise ValueError("Provide either answer_text or answer_index")


def _check_answer(question_correct: str, submitted: str, options: list[str]) -> bool:
    """Check if submitted answer matches the correct answer.

    Handles various matching strategies:
    1. Exact match
    2. Normalized match (case-insensitive, stripped)
    3. Prefix letter match (e.g., "A" matches "A. something")
    4. Option-index match
    """
    if not question_correct:
        return False  # multi-select: can't auto-grade

    # Exact
    if submitted.strip() == question_correct.strip():
        return True

    # Case-insensitive
    if submitted.strip().lower() == question_correct.strip().lower():
        return True

    # Prefix match (common with truncated options)
    sub_lower = submitted.strip().lower()
    cor_lower = question_correct.strip().lower()
    if len(sub_lower) > 10 and cor_lower.startswith(sub_lower[:50]):
        return True
    if len(cor_lower) > 10 and sub_lower.startswith(cor_lower[:50]):
        return True

    return False


@mcp.tool(
    description=(
        "Submit an answer for a question. Returns correctness, the correct answer, "
        "explanation, references, and remediation guidance. The remediation field "
        "contains structured hints for the tutor agent to teach the concept."
    ),
)
async def exam_submit_answer(
    session_id: str,
    question_id: str,
    answer_text: str | None = None,
    answer_index: int | None = None,
) -> dict:
    """Submit an answer and get feedback."""
    s = STORE.load(session_id)
    q = BANK.get_question_by_id(question_id)

    submitted = _normalize_answer(q.options, answer_text, answer_index)
    correct = _check_answer(q.correct, submitted, q.options)
    tags = infer_tags(q.question)

    STORE.record_answer(
        session_id=session_id,
        question_id=question_id,
        tags=tags,
        correct=correct,
    )

    # Remediation guidance for the A2A tutor agent
    remediation: dict = {
        "tags": tags,
    }
    if not correct:
        remediation["teaching_steps"] = [
            "Explain the underlying AWS concept in 3-6 concise steps.",
            "Point out the common misconception that leads to the wrong choice.",
            "Give a real-world analogy to make the concept memorable.",
            "Ask a short check question to verify the user understood.",
        ]
        remediation["if_still_confused"] = (
            "Re-teach using a simpler example. Ask the user to restate "
            "the key rule in their own words before moving on."
        )
    else:
        remediation["reinforcement"] = (
            "Briefly confirm why this answer is correct. "
            "Mention one related concept the user should also know."
        )

    return SubmitAnswerResponse(
        session_id=session_id,
        question_id=question_id,
        correct=correct,
        submitted=submitted,
        correct_answer=q.correct,
        explanation=q.explanation,
        references=q.references,
        remediation=remediation,
    ).model_dump()


@mcp.tool(
    description=(
        "Get the explanation and references for a specific question. "
        "Useful when the tutor needs to teach a concept in depth."
    ),
)
async def exam_get_explanation(question_id: str) -> dict:
    """Fetch explanation + references for a question."""
    q = BANK.get_question_by_id(question_id)
    return ExplanationResponse(
        question_id=question_id,
        question=q.question,
        correct_answer=q.correct,
        explanation=q.explanation,
        references=q.references,
    ).model_dump()


@mcp.tool(
    description=(
        "Get session status: accuracy, weak/strong tags, mastery level, "
        "remaining questions. Use this to decide whether to continue, "
        "focus on weak areas, or end the session."
    ),
)
async def session_get_status(session_id: str) -> dict:
    """Return session status with analytics."""
    s = STORE.load(session_id)
    total = BANK.question_count(s.exam_id)
    asked = len(s.asked_ids)
    accuracy = (s.correct_count / asked) if asked else 0.0

    return SessionStatusResponse(
        session_id=session_id,
        exam_id=s.exam_id,
        mode=s.mode,
        asked_count=asked,
        correct_count=s.correct_count,
        incorrect_count=s.incorrect_count,
        accuracy=round(accuracy, 4),
        weak_tags=STORE.weak_tags(session_id, min_asked=2, top_n=5),
        strong_tags=STORE.strong_tags(session_id, min_asked=3, top_n=5),
        remaining_questions=max(0, total - asked),
        mastery_level=STORE.mastery_level(session_id),
    ).model_dump()


def main() -> None:
    """Entry point: run MCP server on stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
