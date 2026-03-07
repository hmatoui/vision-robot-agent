"""Prompt and reasoning helpers for question answering."""

from __future__ import annotations


def build_system_prompt() -> str:
    """System prompt for robot vision QA behavior."""
    return (
        "You are a robot vision assistant. "
        "Use the provided latest camera image plus recent observations to answer. "
        "Be concise and practical. If uncertain, say what you are uncertain about."
    )
