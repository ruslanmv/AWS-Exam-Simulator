"""Integration tests for MCP tools - tests the full exam flow.

These tests mock the MCP server tools directly (no network), simulating
what the A2A agent would do: list exams, start session, ask questions,
submit answers, check status.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add mcp_server/src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp_server" / "src"))


@pytest.fixture
def mcp_env(question_dir: Path, db_path: Path):
    """Set up environment for MCP server and import the module."""
    with patch.dict(os.environ, {
        "AWS_EXAM_QUESTION_DIR": str(question_dir),
        "AWS_EXAM_DB_PATH": str(db_path),
    }):
        # Reimport the module with correct env
        from aws_exam_tools.exam_bank import ExamBank
        from aws_exam_tools.session_store import SessionStore
        from aws_exam_tools.tagging import infer_tags

        bank = ExamBank(question_dir)
        bank.load_all()
        store = SessionStore(db_path)

        yield bank, store, infer_tags


class TestExamListTool:
    """Test exam_list tool behavior."""

    def test_lists_all_loaded_exams(self, mcp_env) -> None:
        bank, store, _ = mcp_env
        exams = bank.list_exams()
        assert len(exams) >= 2
        assert "SAA-C03-test" in exams
        assert "CLF-C02-test" in exams

    def test_question_counts_correct(self, mcp_env) -> None:
        bank, store, _ = mcp_env
        assert bank.question_count("SAA-C03-test") == 5
        assert bank.question_count("CLF-C02-test") == 3


class TestFullExamFlow:
    """Test the complete exam flow: start -> question -> answer -> status."""

    def test_learning_session_flow(self, mcp_env) -> None:
        bank, store, infer_tags = mcp_env

        # 1. Start session
        session = store.create(exam_id="SAA-C03-test", mode="learning", user_id=None)
        assert session.session_id
        assert session.exam_id == "SAA-C03-test"

        # 2. Get a question
        q = bank.get_question_by_index("SAA-C03-test", 0)
        assert q.question
        assert len(q.options) == 4
        assert q.correct

        # 3. Submit correct answer
        tags = infer_tags(q.question)
        is_correct = True  # simulate correct
        session = store.record_answer(session.session_id, q.question_id, tags, correct=is_correct)
        assert session.correct_count == 1

        # 4. Submit incorrect answer for question 2
        q2 = bank.get_question_by_index("SAA-C03-test", 1)
        tags2 = infer_tags(q2.question)
        session = store.record_answer(session.session_id, q2.question_id, tags2, correct=False)
        assert session.incorrect_count == 1

        # 5. Check status
        loaded = store.load(session.session_id)
        assert loaded.correct_count == 1
        assert loaded.incorrect_count == 1
        assert len(loaded.asked_ids) == 2

    def test_full_exam_mode(self, mcp_env) -> None:
        bank, store, infer_tags = mcp_env

        session = store.create(exam_id="CLF-C02-test", mode="exam", user_id="tester")
        total = bank.question_count("CLF-C02-test")
        assert total == 3

        # Answer all questions
        for i in range(total):
            q = bank.get_question_by_index("CLF-C02-test", i)
            tags = infer_tags(q.question)
            # Simulate alternating correct/incorrect
            correct = i % 2 == 0
            store.record_answer(session.session_id, q.question_id, tags, correct=correct)

        # Check final status
        loaded = store.load(session.session_id)
        assert loaded.correct_count == 2  # indices 0, 2
        assert loaded.incorrect_count == 1  # index 1
        assert len(loaded.asked_ids) == 3


class TestAdaptiveSelection:
    """Test that the adaptive question selection works."""

    def test_weak_area_bias(self, mcp_env) -> None:
        bank, store, infer_tags = mcp_env

        session = store.create(exam_id="SAA-C03-test", mode="learning", user_id=None)

        # Create a weak area in security_encryption
        for i in range(3):
            store.record_answer(
                session.session_id,
                f"fake-sec-{i}",
                ["security_encryption"],
                correct=False,
            )

        # Create a strong area in s3_storage
        for i in range(3):
            store.record_answer(
                session.session_id,
                f"fake-s3-{i}",
                ["s3_storage"],
                correct=True,
            )

        # Verify weak tags detected
        weak = store.weak_tags(session.session_id, min_asked=2)
        assert "security_encryption" in weak

        # Verify strong tags detected
        strong = store.strong_tags(session.session_id, min_asked=3)
        assert "s3_storage" in strong


class TestAnswerMatching:
    """Test answer correctness checking."""

    def test_exact_match(self, mcp_env) -> None:
        bank, _, _ = mcp_env
        q = bank.get_question_by_index("SAA-C03-test", 0)
        assert q.correct == "A. S3 Standard"

    def test_clf_format_match(self, mcp_env) -> None:
        bank, _, _ = mcp_env
        q = bank.get_question_by_index("CLF-C02-test", 0)
        assert q.correct == "AWS Management Console"

    def test_correct_indices(self, mcp_env) -> None:
        bank, _, _ = mcp_env
        q = bank.get_question_by_index("SAA-C03-test", 0)
        assert 0 in q.correct_indices  # "A. S3 Standard" is first option


class TestExplanationsAndReferences:
    """Test explanation and reference retrieval."""

    def test_saa_has_explanation(self, mcp_env) -> None:
        bank, _, _ = mcp_env
        q = bank.get_question_by_index("SAA-C03-test", 0)
        assert q.explanation is not None
        assert "S3 Standard" in q.explanation

    def test_saa_has_references(self, mcp_env) -> None:
        bank, _, _ = mcp_env
        q = bank.get_question_by_index("SAA-C03-test", 0)
        assert len(q.references) > 0
        assert any("aws.amazon.com" in r or "docs.aws" in r for r in q.references)

    def test_clf_no_explanation(self, mcp_env) -> None:
        bank, _, _ = mcp_env
        q = bank.get_question_by_index("CLF-C02-test", 0)
        assert q.explanation is None
