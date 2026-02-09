"""Exam question bank loader.

Loads *.json question banks from a directory. Compatible with both
AWS-Exam-Simulator JSON formats:

Format A (SAA-C03-v1 style):
  {"question": "...", "options": ["A. ...", "B. ..."], "correct": "A. ...",
   "explanation": "...", "references": "..."}

Format B (CLF-C02 style):
  {"question": "...", "options": ["option1", "option2"], "correct": "option1"}

Handles:
- Questions starting with ": " prefix (common in the dataset)
- Empty correct field (multi-select questions)
- References as string or list
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


# Friendly names for exam IDs
EXAM_TITLES: dict[str, str] = {
    "SAA-C03": "AWS Solutions Architect Associate",
    "SAP-C02": "AWS Solutions Architect Professional",
    "CLF-C02": "AWS Cloud Practitioner",
    "DOP-C02": "AWS DevOps Engineer Professional",
    "MLS-C01": "AWS Machine Learning Specialty",
    "AI-900": "Microsoft Azure AI Fundamentals",
    "AI-102": "Microsoft Azure AI Engineer",
    "DP-100": "Microsoft Azure Data Scientist",
    "GCP-ML": "Google Cloud Machine Learning Engineer",
    "GCP-CA": "Google Cloud Associate Cloud Engineer",
}


def _derive_title(exam_id: str) -> str:
    """Derive a human-readable title from exam_id."""
    for prefix, title in EXAM_TITLES.items():
        if exam_id.upper().startswith(prefix.upper()):
            version = exam_id.replace(prefix, "").lstrip("-").lstrip("_")
            if version:
                return f"{title} ({version})"
            return title
    return exam_id


@dataclass(frozen=True)
class Question:
    exam_id: str
    index: int
    question_id: str
    question: str
    options: list[str]
    correct: str
    correct_indices: list[int]  # 0-based indices into options
    explanation: str | None
    references: list[str]
    multi_select: bool


def _clean_question_text(text: str) -> str:
    """Remove leading ': ' artifact common in the dataset."""
    text = text.strip()
    if text.startswith(": "):
        text = text[2:]
    return text.strip()


def _parse_references(raw: str | list | None) -> list[str]:
    """Normalize references field to a list of URLs/strings."""
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(r).strip() for r in raw if str(r).strip()]

    # Split string references on whitespace/newlines that precede http
    refs = re.split(r'\s+(?=https?://)', str(raw).strip())
    return [r.strip() for r in refs if r.strip()]


def _find_correct_indices(options: list[str], correct: str) -> list[int]:
    """Find which option indices match the correct answer string."""
    if not correct:
        return []

    correct_normalized = correct.strip().lower()

    # Exact match
    for i, opt in enumerate(options):
        if opt.strip().lower() == correct_normalized:
            return [i]

    # Prefix match (handles truncated correct answers)
    for i, opt in enumerate(options):
        if opt.strip().lower().startswith(correct_normalized[:50]):
            return [i]
        if correct_normalized.startswith(opt.strip().lower()[:50]):
            return [i]

    # Letter-prefix match (e.g., correct="A" matches "A. something")
    if len(correct.strip()) <= 2:
        letter = correct.strip().upper().rstrip(".")
        for i, opt in enumerate(options):
            if opt.strip().upper().startswith(f"{letter}.") or opt.strip().upper().startswith(f"{letter} "):
                return [i]

    return []


class ExamBank:
    """Loads and provides access to exam question banks."""

    def __init__(self, question_dir: Path):
        self.question_dir = question_dir
        self._exams: dict[str, list[Question]] = {}
        self._titles: dict[str, str] = {}

    def load_all(self) -> None:
        """Load all *.json question files from the question directory."""
        if not self.question_dir.exists():
            raise FileNotFoundError(f"Question directory not found: {self.question_dir}")

        self._exams.clear()
        self._titles.clear()

        for f in sorted(self.question_dir.glob("*.json")):
            exam_id = f.stem
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue  # skip invalid files

            if not isinstance(data, list):
                continue

            questions: list[Question] = []
            for i, raw in enumerate(data):
                if not isinstance(raw, dict):
                    continue

                q_text = _clean_question_text(str(raw.get("question", "")))
                if not q_text:
                    continue

                options = [str(o).strip() for o in raw.get("options", []) if str(o).strip()]
                if not options:
                    continue

                correct = str(raw.get("correct", "")).strip()
                explanation = raw.get("explanation")
                if explanation:
                    explanation = str(explanation).strip()
                    # Clean "Explanation " prefix
                    if explanation.startswith("Explanation "):
                        explanation = explanation[len("Explanation "):]
                    elif explanation.startswith("Explanation\n"):
                        explanation = explanation[len("Explanation\n"):]

                references = _parse_references(raw.get("references"))
                correct_indices = _find_correct_indices(options, correct)
                multi_select = not correct  # empty correct = multi-select

                # Stable question_id: exam_id + index + content hash
                h = hashlib.sha256()
                h.update(exam_id.encode("utf-8"))
                h.update(str(i).encode("utf-8"))
                h.update(q_text.encode("utf-8"))
                question_id = f"{exam_id}:{i}:{h.hexdigest()[:12]}"

                questions.append(
                    Question(
                        exam_id=exam_id,
                        index=i,
                        question_id=question_id,
                        question=q_text,
                        options=options,
                        correct=correct,
                        correct_indices=correct_indices,
                        explanation=explanation if explanation else None,
                        references=references,
                        multi_select=multi_select,
                    )
                )

            if questions:
                self._exams[exam_id] = questions
                self._titles[exam_id] = _derive_title(exam_id)

    def list_exams(self) -> dict[str, int]:
        """Return {exam_id: question_count}."""
        return {eid: len(qs) for eid, qs in self._exams.items()}

    def get_title(self, exam_id: str) -> str:
        return self._titles.get(exam_id, exam_id)

    def get_question_by_id(self, question_id: str) -> Question:
        """Look up a question by its stable question_id."""
        exam_id = question_id.split(":")[0]
        if exam_id not in self._exams:
            raise KeyError(f"Unknown exam_id: {exam_id}")
        for q in self._exams[exam_id]:
            if q.question_id == question_id:
                return q
        raise KeyError(f"Unknown question_id: {question_id}")

    def get_question_by_index(self, exam_id: str, index: int) -> Question:
        """Get question by exam_id and sequential index."""
        if exam_id not in self._exams:
            raise KeyError(f"Unknown exam_id: {exam_id}")
        qs = self._exams[exam_id]
        if index < 0 or index >= len(qs):
            raise IndexError(f"Index {index} out of range for {exam_id} (0..{len(qs)-1})")
        return qs[index]

    def question_count(self, exam_id: str) -> int:
        if exam_id not in self._exams:
            raise KeyError(f"Unknown exam_id: {exam_id}")
        return len(self._exams[exam_id])

    def all_question_ids(self, exam_id: str) -> list[str]:
        """Get all question IDs for an exam."""
        if exam_id not in self._exams:
            raise KeyError(f"Unknown exam_id: {exam_id}")
        return [q.question_id for q in self._exams[exam_id]]
