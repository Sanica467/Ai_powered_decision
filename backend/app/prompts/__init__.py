"""Prompts package."""
from app.prompts.prompts import (
    SYSTEM_PROMPT,
    chat_prompt,
    dataset_summary_prompt,
    diagnosis_prompt,
    executive_summary_prompt,
    recommendations_prompt,
    root_cause_prompt,
    suggest_questions_prompt,
    what_if_prompt,
)

__all__ = [
    "SYSTEM_PROMPT",
    "chat_prompt",
    "dataset_summary_prompt",
    "diagnosis_prompt",
    "executive_summary_prompt",
    "recommendations_prompt",
    "root_cause_prompt",
    "suggest_questions_prompt",
    "what_if_prompt",
]
