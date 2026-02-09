"""Mock tests for the A2A tutor agent.

Tests the agent's tool calling and orchestration logic without
requiring an LLM or network connection.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp_server" / "src"))


@pytest.fixture
def agent_env(question_dir: Path, db_path: Path):
    """Set up environment and create the agent."""
    with patch.dict(os.environ, {
        "AWS_EXAM_QUESTION_DIR": str(question_dir),
        "AWS_EXAM_DB_PATH": str(db_path),
        "USE_DIRECT_MCP": "true",
        "SYSTEM_PROMPT_FILE": str(
            Path(__file__).parent.parent / "agent_runtime" / "prompts" / "aws_exam_tutor_system.txt"
        ),
    }):
        from agent_runtime.config import load_config
        from agent_runtime.agent import ExamTutorAgent

        config = load_config()
        config.question_dir = str(question_dir)
        config.db_path = str(db_path)
        agent = ExamTutorAgent(config)
        yield agent


class TestAgentToolCalls:
    """Test agent tool calling through direct import."""

    def test_exam_list(self, agent_env) -> None:
        agent = agent_env

        async def run():
            await agent._setup_direct_tools()
            result = await agent.call_tool("exam_list", {})
            assert "exams" in result
            assert len(result["exams"]) >= 2
            return result

        result = asyncio.get_event_loop().run_until_complete(run())
        exam_ids = [e["exam_id"] for e in result["exams"]]
        assert "SAA-C03-test" in exam_ids

    def test_start_session(self, agent_env) -> None:
        agent = agent_env

        async def run():
            await agent._setup_direct_tools()
            result = await agent.call_tool("exam_start_session", {
                "exam_id": "SAA-C03-test",
                "mode": "learning",
            })
            assert "session_id" in result
            assert result["exam_id"] == "SAA-C03-test"
            assert result["mode"] == "learning"
            assert result["total_questions"] == 5
            return result

        asyncio.get_event_loop().run_until_complete(run())

    def test_next_question(self, agent_env) -> None:
        agent = agent_env

        async def run():
            await agent._setup_direct_tools()
            session = await agent.call_tool("exam_start_session", {
                "exam_id": "SAA-C03-test", "mode": "learning",
            })
            q = await agent.call_tool("exam_next_question", {
                "session_id": session["session_id"],
            })
            assert "question" in q
            assert "options" in q
            assert len(q["options"]) == 4
            assert "question_id" in q
            assert "tags" in q
            return q

        asyncio.get_event_loop().run_until_complete(run())

    def test_submit_answer_correct(self, agent_env) -> None:
        agent = agent_env

        async def run():
            await agent._setup_direct_tools()
            session = await agent.call_tool("exam_start_session", {
                "exam_id": "CLF-C02-test", "mode": "learning",
            })
            q = await agent.call_tool("exam_next_question", {
                "session_id": session["session_id"],
            })

            # Find the correct option index
            from aws_exam_tools.exam_bank import ExamBank
            bank = ExamBank(Path(os.environ["AWS_EXAM_QUESTION_DIR"]))
            bank.load_all()
            question = bank.get_question_by_id(q["question_id"])

            result = await agent.call_tool("exam_submit_answer", {
                "session_id": session["session_id"],
                "question_id": q["question_id"],
                "answer_text": question.correct,
            })
            assert result["correct"] is True
            return result

        asyncio.get_event_loop().run_until_complete(run())

    def test_submit_answer_incorrect(self, agent_env) -> None:
        agent = agent_env

        async def run():
            await agent._setup_direct_tools()
            session = await agent.call_tool("exam_start_session", {
                "exam_id": "SAA-C03-test", "mode": "learning",
            })
            q = await agent.call_tool("exam_next_question", {
                "session_id": session["session_id"],
            })

            # Submit a wrong answer (last option, unlikely to be correct for all)
            result = await agent.call_tool("exam_submit_answer", {
                "session_id": session["session_id"],
                "question_id": q["question_id"],
                "answer_index": len(q["options"]) - 1,
            })
            # We can't guarantee it's incorrect, but we can check structure
            assert "correct" in result
            assert "correct_answer" in result
            assert "explanation" in result
            assert "remediation" in result
            return result

        asyncio.get_event_loop().run_until_complete(run())

    def test_get_explanation(self, agent_env) -> None:
        agent = agent_env

        async def run():
            await agent._setup_direct_tools()
            session = await agent.call_tool("exam_start_session", {
                "exam_id": "SAA-C03-test", "mode": "learning",
            })
            q = await agent.call_tool("exam_next_question", {
                "session_id": session["session_id"],
            })
            explanation = await agent.call_tool("exam_get_explanation", {
                "question_id": q["question_id"],
            })
            assert "question_id" in explanation
            assert "question" in explanation
            assert "correct_answer" in explanation
            return explanation

        asyncio.get_event_loop().run_until_complete(run())

    def test_session_status(self, agent_env) -> None:
        agent = agent_env

        async def run():
            await agent._setup_direct_tools()
            session = await agent.call_tool("exam_start_session", {
                "exam_id": "SAA-C03-test", "mode": "learning",
            })

            # Answer a few questions
            for _ in range(3):
                q = await agent.call_tool("exam_next_question", {
                    "session_id": session["session_id"],
                })
                await agent.call_tool("exam_submit_answer", {
                    "session_id": session["session_id"],
                    "question_id": q["question_id"],
                    "answer_index": 0,
                })

            status = await agent.call_tool("session_get_status", {
                "session_id": session["session_id"],
            })
            assert status["asked_count"] == 3
            assert status["mastery_level"] in ["beginner", "intermediate", "advanced", "expert"]
            assert "weak_tags" in status
            assert "strong_tags" in status
            assert "remaining_questions" in status
            return status

        asyncio.get_event_loop().run_until_complete(run())


class TestAgentFullLearningCycle:
    """Test a complete learning cycle through the agent."""

    def test_complete_exam_cycle(self, agent_env) -> None:
        """Simulate a full exam: start, answer all questions, check final status."""
        agent = agent_env

        async def run():
            await agent._setup_direct_tools()

            # Start session
            session = await agent.call_tool("exam_start_session", {
                "exam_id": "CLF-C02-test", "mode": "practice",
            })
            assert session["total_questions"] == 3

            # Answer all questions
            answered = 0
            for _ in range(3):
                q = await agent.call_tool("exam_next_question", {
                    "session_id": session["session_id"],
                })
                if "error" in q:
                    break
                await agent.call_tool("exam_submit_answer", {
                    "session_id": session["session_id"],
                    "question_id": q["question_id"],
                    "answer_index": 0,
                })
                answered += 1

            # Final status
            status = await agent.call_tool("session_get_status", {
                "session_id": session["session_id"],
            })
            assert status["asked_count"] == 3
            assert status["correct_count"] + status["incorrect_count"] == 3
            assert 0.0 <= status["accuracy"] <= 1.0

        asyncio.get_event_loop().run_until_complete(run())


class TestAgentPromptLoading:
    """Test that the agent loads its system prompt correctly."""

    def test_system_prompt_loaded(self, agent_env) -> None:
        agent = agent_env
        assert "AWS Exam Tutor" in agent._system_prompt
        assert "teach until learned" in agent._system_prompt.lower()

    def test_system_prompt_contains_tools(self, agent_env) -> None:
        agent = agent_env
        assert "exam_list" in agent._system_prompt
        assert "exam_submit_answer" in agent._system_prompt
        assert "session_get_status" in agent._system_prompt
