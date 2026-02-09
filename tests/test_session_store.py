"""Tests for the session store."""
from __future__ import annotations

from pathlib import Path

import pytest

from mcp_server.src.aws_exam_tools.session_store import SessionStore


class TestSessionCreation:
    """Test session creation and loading."""

    def test_create_session(self, db_path: Path) -> None:
        store = SessionStore(db_path)
        s = store.create(exam_id="SAA-C03-test", mode="learning", user_id=None)
        assert s.session_id
        assert s.exam_id == "SAA-C03-test"
        assert s.mode == "learning"
        assert s.correct_count == 0
        assert s.incorrect_count == 0

    def test_load_session(self, db_path: Path) -> None:
        store = SessionStore(db_path)
        s = store.create(exam_id="CLF-C02", mode="practice", user_id="user-1")
        loaded = store.load(s.session_id)
        assert loaded.session_id == s.session_id
        assert loaded.exam_id == "CLF-C02"
        assert loaded.user_id == "user-1"

    def test_load_nonexistent_raises(self, db_path: Path) -> None:
        store = SessionStore(db_path)
        with pytest.raises(KeyError):
            store.load("nonexistent-id")

    def test_multiple_sessions(self, db_path: Path) -> None:
        store = SessionStore(db_path)
        s1 = store.create(exam_id="SAA-C03", mode="learning", user_id=None)
        s2 = store.create(exam_id="CLF-C02", mode="exam", user_id=None)
        assert s1.session_id != s2.session_id
        assert store.load(s1.session_id).exam_id == "SAA-C03"
        assert store.load(s2.session_id).exam_id == "CLF-C02"


class TestAnswerRecording:
    """Test recording answers and computing stats."""

    def test_record_correct(self, db_path: Path) -> None:
        store = SessionStore(db_path)
        s = store.create(exam_id="test", mode="learning", user_id=None)

        s = store.record_answer(s.session_id, "q1", ["iam"], correct=True)
        assert s.correct_count == 1
        assert s.incorrect_count == 0
        assert "q1" in s.asked_ids

    def test_record_incorrect(self, db_path: Path) -> None:
        store = SessionStore(db_path)
        s = store.create(exam_id="test", mode="learning", user_id=None)

        s = store.record_answer(s.session_id, "q1", ["s3_storage"], correct=False)
        assert s.correct_count == 0
        assert s.incorrect_count == 1

    def test_tag_stats_tracked(self, db_path: Path) -> None:
        store = SessionStore(db_path)
        s = store.create(exam_id="test", mode="learning", user_id=None)

        store.record_answer(s.session_id, "q1", ["iam"], correct=True)
        store.record_answer(s.session_id, "q2", ["iam"], correct=False)
        store.record_answer(s.session_id, "q3", ["iam"], correct=True)

        loaded = store.load(s.session_id)
        assert loaded.tag_stats["iam"]["asked"] == 3
        assert loaded.tag_stats["iam"]["correct"] == 2

    def test_multiple_tags_per_question(self, db_path: Path) -> None:
        store = SessionStore(db_path)
        s = store.create(exam_id="test", mode="learning", user_id=None)

        store.record_answer(s.session_id, "q1", ["iam", "s3_storage"], correct=True)
        loaded = store.load(s.session_id)
        assert "iam" in loaded.tag_stats
        assert "s3_storage" in loaded.tag_stats

    def test_asked_ids_not_duplicated(self, db_path: Path) -> None:
        store = SessionStore(db_path)
        s = store.create(exam_id="test", mode="learning", user_id=None)

        store.record_answer(s.session_id, "q1", ["iam"], correct=True)
        store.record_answer(s.session_id, "q1", ["iam"], correct=False)

        loaded = store.load(s.session_id)
        assert loaded.asked_ids.count("q1") == 1


class TestWeakStrongTags:
    """Test weak/strong tag detection."""

    def _populate_session(self, store: SessionStore) -> str:
        s = store.create(exam_id="test", mode="learning", user_id=None)

        # IAM: 1/4 correct = 25% (weak)
        for i in range(4):
            store.record_answer(s.session_id, f"iam-{i}", ["iam"], correct=(i == 0))

        # S3: 3/4 correct = 75% (medium)
        for i in range(4):
            store.record_answer(s.session_id, f"s3-{i}", ["s3_storage"], correct=(i < 3))

        # VPC: 4/4 correct = 100% (strong)
        for i in range(4):
            store.record_answer(s.session_id, f"vpc-{i}", ["vpc_networking"], correct=True)

        return s.session_id

    def test_weak_tags(self, db_path: Path) -> None:
        store = SessionStore(db_path)
        sid = self._populate_session(store)
        weak = store.weak_tags(sid, min_asked=3)
        assert weak[0] == "iam"  # lowest accuracy

    def test_strong_tags(self, db_path: Path) -> None:
        store = SessionStore(db_path)
        sid = self._populate_session(store)
        strong = store.strong_tags(sid, min_asked=3)
        assert strong[0] == "vpc_networking"  # highest accuracy

    def test_mastery_beginner(self, db_path: Path) -> None:
        store = SessionStore(db_path)
        s = store.create(exam_id="test", mode="learning", user_id=None)
        assert store.mastery_level(s.session_id) == "beginner"

    def test_mastery_expert(self, db_path: Path) -> None:
        store = SessionStore(db_path)
        s = store.create(exam_id="test", mode="learning", user_id=None)
        for i in range(20):
            store.record_answer(s.session_id, f"q-{i}", ["general"], correct=True)
        assert store.mastery_level(s.session_id) == "expert"

    def test_mastery_intermediate(self, db_path: Path) -> None:
        store = SessionStore(db_path)
        s = store.create(exam_id="test", mode="learning", user_id=None)
        for i in range(10):
            store.record_answer(s.session_id, f"q-{i}", ["general"], correct=(i < 6))
        assert store.mastery_level(s.session_id) == "intermediate"
