"""Pydantic models for the AWS Exam Tools MCP server."""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class ExamInfo(BaseModel):
    exam_id: str
    title: str = ""
    question_count: int


class ExamListResponse(BaseModel):
    exams: list[ExamInfo]


class StartSessionRequest(BaseModel):
    exam_id: str = Field(..., description="Exam id (usually filename without .json)")
    mode: str = Field("learning", description="learning | practice | exam")
    user_id: Optional[str] = Field(None, description="Optional user id for tracking")


class StartSessionResponse(BaseModel):
    session_id: str
    exam_id: str
    mode: str
    total_questions: int


class NextQuestionResponse(BaseModel):
    session_id: str
    exam_id: str
    question_id: str
    question_number: int
    total_questions: int
    question: str
    options: list[str]
    tags: list[str] = Field(default_factory=list)
    multi_select: bool = False


class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer_text: Optional[str] = Field(None, description="Answer as option text")
    answer_index: Optional[int] = Field(None, description="Answer as option index (0-based)")


class SubmitAnswerResponse(BaseModel):
    session_id: str
    question_id: str
    correct: bool
    submitted: str
    correct_answer: str
    explanation: Optional[str] = None
    references: list[str] = Field(default_factory=list)
    remediation: dict[str, Any] = Field(default_factory=dict)


class ExplanationResponse(BaseModel):
    question_id: str
    question: str
    correct_answer: str
    explanation: Optional[str] = None
    references: list[str] = Field(default_factory=list)


class SessionStatusResponse(BaseModel):
    session_id: str
    exam_id: str
    mode: str
    asked_count: int
    correct_count: int
    incorrect_count: int
    accuracy: float
    weak_tags: list[str] = Field(default_factory=list)
    strong_tags: list[str] = Field(default_factory=list)
    remaining_questions: int
    mastery_level: str  # "beginner" | "intermediate" | "advanced" | "expert"
