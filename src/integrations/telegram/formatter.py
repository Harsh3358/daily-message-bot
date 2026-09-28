"""Telegram message formatter using Telegram HTML formatting mode.

Why HTML over MarkdownV2?
Telegram's MarkdownV2 requires escaping over 18 special characters (including '.', '!', '-', '_'),
which easily breaks on programming problems containing code, math symbols, or punctuation.
HTML mode only requires escaping '<', '>', and '&', making it robust and safe for technical content.
"""
import html
from src.models.enums import DifficultyEnum
from src.models.problem import Problem
from src.models.subject import Subject

# Telegram maximum message length limit
MAX_TELEGRAM_MESSAGE_LENGTH = 4096
SAFE_CONTENT_LIMIT = 3200


def get_difficulty_badge(difficulty: DifficultyEnum) -> str:
    """Return an emoji indicator for difficulty."""
    badges = {
        DifficultyEnum.EASY: "🟢 Easy",
        DifficultyEnum.MEDIUM: "🟡 Medium",
        DifficultyEnum.HARD: "🔴 Hard",
    }
    return badges.get(difficulty, difficulty.value)


def format_problem_message(problem: Problem, subject: Subject) -> str:
    """Format a Problem entity into an HTML message for Telegram."""
    subject_name = html.escape(subject.name)
    title = html.escape(problem.title)
    topic = html.escape(problem.topic)
    badge = get_difficulty_badge(problem.difficulty)
    date_str = problem.scheduled_date.strftime("%B %d, %Y")

    # Safe escaping for content
    content = html.escape(problem.content)
    if len(content) > SAFE_CONTENT_LIMIT:
        content = content[:SAFE_CONTENT_LIMIT] + "\n\n<i>[Content truncated due to length...]</i>"

    lines = [
        f"🎯 <b>Daily Problem | {subject_name}</b>",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"🏷️ <b>Topic:</b> {topic}",
        f"⚡ <b>Difficulty:</b> {badge}",
        f"📅 <b>Date:</b> {date_str}",
        f"",
        f"📌 <b>{title}</b>",
        f"",
        content,
    ]

    if problem.reference_url:
        ref_url = html.escape(problem.reference_url)
        lines.append("")
        lines.append(f"🔗 <a href='{ref_url}'>Click here to practice / view solution</a>")

    lines.append("")
    lines.append("<i>Happy Coding! 🚀</i>")

    formatted = "\n".join(lines)

    # Hard guard against exceeding Telegram's 4096 character limit
    if len(formatted) > MAX_TELEGRAM_MESSAGE_LENGTH:
        formatted = formatted[: MAX_TELEGRAM_MESSAGE_LENGTH - 50] + "\n...[truncated]"

    return formatted
