"""Tests for Telegram message formatter."""
import uuid
from datetime import date
from src.integrations.telegram.formatter import format_problem_message, get_difficulty_badge
from src.models.enums import DifficultyEnum
from src.models.problem import Problem
from src.models.subject import Subject


def test_difficulty_badges():
    assert "🟢 Easy" in get_difficulty_badge(DifficultyEnum.EASY)
    assert "🟡 Medium" in get_difficulty_badge(DifficultyEnum.MEDIUM)
    assert "🔴 Hard" in get_difficulty_badge(DifficultyEnum.HARD)


def test_format_problem_message_html_escaping():
    subject = Subject(
        id=uuid.uuid4(),
        name="C++ & Algorithms",
        slug="cpp-algo",
        is_active=True,
    )
    problem = Problem(
        id=uuid.uuid4(),
        subject_id=subject.id,
        title="Find element where A[i] < B[i]",
        topic="Binary Search & Vectors",
        difficulty=DifficultyEnum.MEDIUM,
        content="Check if `x < y && y > z` for all elements.",
        scheduled_date=date(2026, 9, 23),
        reference_url="https://leetcode.com/problems/example",
        is_active=True,
    )

    formatted = format_problem_message(problem, subject)

    # HTML special characters must be escaped safely
    assert "&lt;" in formatted
    assert "&gt;" in formatted
    assert "&amp;" in formatted
    assert "C++ &amp; Algorithms" in formatted
    assert "Binary Search &amp; Vectors" in formatted
    assert "🟡 Medium" in formatted
    assert "https://leetcode.com/problems/example" in formatted
