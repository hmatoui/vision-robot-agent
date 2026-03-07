"""Unit tests for vision agent orchestration."""

from __future__ import annotations

import numpy as np

from app.agent.vision_agent import VisionAgent
from app.memory.scene_memory import SceneMemory


class FakeOpenAIClient:
    """Deterministic fake OpenAI client for tests."""

    def reason_with_image(
        self,
        model: str,
        system_prompt: str,
        question: str,
        memory_context: str,
        image_b64: str,
    ) -> str:
        return (
            f"model={model}; q={question}; "
            f"memory={'yes' if memory_context else 'no'}; image_len={len(image_b64)}"
        )


def test_agent_answer_uses_memory_and_image() -> None:
    memory = SceneMemory(retention_seconds=60, max_entries=10)
    memory.add_observation("person standing")

    client = FakeOpenAIClient()
    agent = VisionAgent(client, memory, reasoning_model="fake-model")

    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    answer = agent.answer("Is anyone there?", frame)

    assert "model=fake-model" in answer
    assert "Is anyone there?" in answer
    assert "memory=yes" in answer
