"""Tests for the ExamBank question loader."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_server.src.aws_exam_tools.exam_bank import ExamBank


class TestExamBankLoading:
    """Test loading question banks from JSON files."""

    def test_load_all_finds_exams(self, question_dir: Path) -> None:
        bank = ExamBank(question_dir)
        bank.load_all()
        exams = bank.list_exams()
        assert "SAA-C03-test" in exams
        assert "CLF-C02-test" in exams

    def test_question_count(self, question_dir: Path) -> None:
        bank = ExamBank(question_dir)
        bank.load_all()
        assert bank.question_count("SAA-C03-test") == 5
        assert bank.question_count("CLF-C02-test") == 3

    def test_unknown_exam_raises(self, question_dir: Path) -> None:
        bank = ExamBank(question_dir)
        bank.load_all()
        with pytest.raises(KeyError):
            bank.question_count("NONEXISTENT")

    def test_missing_dir_raises(self, tmp_path: Path) -> None:
        bank = ExamBank(tmp_path / "no_such_dir")
        with pytest.raises(FileNotFoundError):
            bank.load_all()


class TestExamBankQuestions:
    """Test question access and properties."""

    def test_get_by_index(self, question_dir: Path) -> None:
        bank = ExamBank(question_dir)
        bank.load_all()
        q = bank.get_question_by_index("SAA-C03-test", 0)
        assert "S3" in q.question or "storage" in q.question.lower()
        assert len(q.options) == 4
        assert q.correct != ""
        assert q.exam_id == "SAA-C03-test"

    def test_get_by_id(self, question_dir: Path) -> None:
        bank = ExamBank(question_dir)
        bank.load_all()
        q0 = bank.get_question_by_index("SAA-C03-test", 0)
        q_by_id = bank.get_question_by_id(q0.question_id)
        assert q_by_id.question == q0.question

    def test_question_id_format(self, question_dir: Path) -> None:
        bank = ExamBank(question_dir)
        bank.load_all()
        q = bank.get_question_by_index("SAA-C03-test", 0)
        parts = q.question_id.split(":")
        assert len(parts) == 3
        assert parts[0] == "SAA-C03-test"
        assert parts[1] == "0"

    def test_out_of_range_raises(self, question_dir: Path) -> None:
        bank = ExamBank(question_dir)
        bank.load_all()
        with pytest.raises(IndexError):
            bank.get_question_by_index("SAA-C03-test", 999)

    def test_all_question_ids(self, question_dir: Path) -> None:
        bank = ExamBank(question_dir)
        bank.load_all()
        ids = bank.all_question_ids("SAA-C03-test")
        assert len(ids) == 5
        assert len(set(ids)) == 5  # all unique

    def test_correct_indices_populated(self, question_dir: Path) -> None:
        bank = ExamBank(question_dir)
        bank.load_all()
        q = bank.get_question_by_index("SAA-C03-test", 0)
        assert len(q.correct_indices) >= 1

    def test_explanation_present_saa(self, question_dir: Path) -> None:
        bank = ExamBank(question_dir)
        bank.load_all()
        q = bank.get_question_by_index("SAA-C03-test", 0)
        assert q.explanation is not None

    def test_clf_no_explanation(self, question_dir: Path) -> None:
        bank = ExamBank(question_dir)
        bank.load_all()
        q = bank.get_question_by_index("CLF-C02-test", 0)
        # CLF questions don't have explanation field
        assert q.explanation is None

    def test_title_derivation(self, question_dir: Path) -> None:
        bank = ExamBank(question_dir)
        bank.load_all()
        title = bank.get_title("SAA-C03-test")
        assert "Solutions Architect" in title


class TestExamBankEdgeCases:
    """Test edge cases in question loading."""

    def test_empty_json_file_skipped(self, tmp_path: Path) -> None:
        qdir = tmp_path / "q"
        qdir.mkdir()
        (qdir / "empty.json").write_text("[]", encoding="utf-8")
        bank = ExamBank(qdir)
        bank.load_all()
        assert "empty" not in bank.list_exams()

    def test_invalid_json_skipped(self, tmp_path: Path) -> None:
        qdir = tmp_path / "q"
        qdir.mkdir()
        (qdir / "bad.json").write_text("not json", encoding="utf-8")
        (qdir / "good.json").write_text(
            json.dumps([{"question": "Q?", "options": ["A", "B"], "correct": "A"}]),
            encoding="utf-8",
        )
        bank = ExamBank(qdir)
        bank.load_all()
        assert "bad" not in bank.list_exams()
        assert "good" in bank.list_exams()

    def test_question_with_colon_prefix(self, tmp_path: Path) -> None:
        qdir = tmp_path / "q"
        qdir.mkdir()
        (qdir / "test.json").write_text(
            json.dumps([{
                "question": ": A question with colon prefix",
                "options": ["A", "B"],
                "correct": "A",
            }]),
            encoding="utf-8",
        )
        bank = ExamBank(qdir)
        bank.load_all()
        q = bank.get_question_by_index("test", 0)
        assert not q.question.startswith(":")
        assert q.question == "A question with colon prefix"
