"""Session store backed by SQLite.

Tracks exam sessions, answers, per-tag accuracy, and weak-area detection.
Designed to swap cleanly to Postgres by replacing this class.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AnswerRecord:
    question_id: str
    tags: list[str]
    correct: bool
    timestamp: float


@dataclass
class Session:
    session_id: str
    exam_id: str
    mode: str  # "learning" | "practice" | "exam"
    user_id: str | None
    created_at: float
    asked_ids: list[str]
    answers: list[AnswerRecord]
    correct_count: int
    incorrect_count: int
    tag_stats: dict[str, dict[str, int]]  # {tag: {"asked": n, "correct": n}}


class SessionStore:
    """SQLite-backed session and progress tracking."""

    def __init__(self, sqlite_path: Path):
        self.sqlite_path = sqlite_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.sqlite_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    exam_id TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'learning',
                    user_id TEXT,
                    created_at REAL NOT NULL,
                    asked_ids TEXT NOT NULL DEFAULT '[]',
                    answers TEXT NOT NULL DEFAULT '[]',
                    correct_count INTEGER NOT NULL DEFAULT 0,
                    incorrect_count INTEGER NOT NULL DEFAULT 0,
                    tag_stats TEXT NOT NULL DEFAULT '{}'
                )
            """)

    def create(self, exam_id: str, mode: str, user_id: str | None) -> Session:
        """Create a new session."""
        s = Session(
            session_id=str(uuid.uuid4()),
            exam_id=exam_id,
            mode=mode,
            user_id=user_id,
            created_at=time.time(),
            asked_ids=[],
            answers=[],
            correct_count=0,
            incorrect_count=0,
            tag_stats={},
        )
        self._save(s)
        return s

    def load(self, session_id: str) -> Session:
        """Load a session by ID."""
        with self._connect() as c:
            row = c.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()

        if not row:
            raise KeyError(f"Unknown session_id: {session_id}")

        answers_raw = json.loads(row["answers"])
        answers = [
            AnswerRecord(
                question_id=a["question_id"],
                tags=a.get("tags", []),
                correct=a["correct"],
                timestamp=a.get("timestamp", 0),
            )
            for a in answers_raw
        ]

        return Session(
            session_id=row["session_id"],
            exam_id=row["exam_id"],
            mode=row["mode"],
            user_id=row["user_id"],
            created_at=row["created_at"],
            asked_ids=json.loads(row["asked_ids"]),
            answers=answers,
            correct_count=int(row["correct_count"]),
            incorrect_count=int(row["incorrect_count"]),
            tag_stats=json.loads(row["tag_stats"]),
        )

    def _save(self, s: Session) -> None:
        answers_data = [
            {
                "question_id": a.question_id,
                "tags": a.tags,
                "correct": a.correct,
                "timestamp": a.timestamp,
            }
            for a in s.answers
        ]

        with self._connect() as c:
            c.execute("""
                INSERT INTO sessions(
                    session_id, exam_id, mode, user_id, created_at,
                    asked_ids, answers, correct_count, incorrect_count, tag_stats
                )
                VALUES(?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(session_id) DO UPDATE SET
                    exam_id=excluded.exam_id,
                    mode=excluded.mode,
                    user_id=excluded.user_id,
                    created_at=excluded.created_at,
                    asked_ids=excluded.asked_ids,
                    answers=excluded.answers,
                    correct_count=excluded.correct_count,
                    incorrect_count=excluded.incorrect_count,
                    tag_stats=excluded.tag_stats
                """,
                (
                    s.session_id,
                    s.exam_id,
                    s.mode,
                    s.user_id,
                    s.created_at,
                    json.dumps(s.asked_ids),
                    json.dumps(answers_data),
                    s.correct_count,
                    s.incorrect_count,
                    json.dumps(s.tag_stats),
                ),
            )

    def record_answer(
        self,
        session_id: str,
        question_id: str,
        tags: list[str],
        correct: bool,
    ) -> Session:
        """Record an answer and update stats."""
        s = self.load(session_id)

        if question_id not in s.asked_ids:
            s.asked_ids.append(question_id)

        s.answers.append(AnswerRecord(
            question_id=question_id,
            tags=tags,
            correct=correct,
            timestamp=time.time(),
        ))

        if correct:
            s.correct_count += 1
        else:
            s.incorrect_count += 1

        for t in tags:
            st = s.tag_stats.setdefault(t, {"asked": 0, "correct": 0})
            st["asked"] += 1
            if correct:
                st["correct"] += 1

        self._save(s)
        return s

    def weak_tags(self, session_id: str, min_asked: int = 2, top_n: int = 5) -> list[str]:
        """Return tags where accuracy is lowest (user's weak areas)."""
        s = self.load(session_id)
        scored: list[tuple[str, float]] = []

        for tag, st in s.tag_stats.items():
            asked = int(st.get("asked", 0))
            correct_count = int(st.get("correct", 0))
            if asked < min_asked:
                continue
            acc = correct_count / asked if asked else 0.0
            scored.append((tag, acc))

        scored.sort(key=lambda x: x[1])  # lowest accuracy first
        return [t for t, _ in scored[:top_n]]

    def strong_tags(self, session_id: str, min_asked: int = 3, top_n: int = 5) -> list[str]:
        """Return tags where accuracy is highest (user's strong areas)."""
        s = self.load(session_id)
        scored: list[tuple[str, float]] = []

        for tag, st in s.tag_stats.items():
            asked = int(st.get("asked", 0))
            correct_count = int(st.get("correct", 0))
            if asked < min_asked:
                continue
            acc = correct_count / asked if asked else 0.0
            scored.append((tag, acc))

        scored.sort(key=lambda x: x[1], reverse=True)  # highest accuracy first
        return [t for t, _ in scored[:top_n]]

    def mastery_level(self, session_id: str) -> str:
        """Derive a mastery level label from overall accuracy."""
        s = self.load(session_id)
        total = s.correct_count + s.incorrect_count
        if total < 5:
            return "beginner"
        accuracy = s.correct_count / total
        if accuracy >= 0.90:
            return "expert"
        elif accuracy >= 0.75:
            return "advanced"
        elif accuracy >= 0.55:
            return "intermediate"
        else:
            return "beginner"
