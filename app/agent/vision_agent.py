"""Vision AI Agent orchestration layer."""

from __future__ import annotations

import numpy as np
from loguru import logger

from app.agent.reasoning import build_system_prompt
from app.memory.scene_memory import SceneMemory
from app.openai_client.client import OpenAIClient
from app.vision.image_utils import frame_to_base64_jpeg, resize_frame


class VisionAgent:
    """Answer user questions by combining latest frame and temporal memory."""

    def __init__(
        self,
        openai_client: OpenAIClient,
        scene_memory: SceneMemory,
        reasoning_model: str,
    ) -> None:
        self._client = openai_client
        self._memory = scene_memory
        self._reasoning_model = reasoning_model

    def answer(self, question: str, latest_frame: np.ndarray) -> str:
        """Generate answer for a user question."""
        logger.info(f"User query: {question}")
        image_b64 = frame_to_base64_jpeg(resize_frame(latest_frame), quality=82)
        memory_context = self._memory.get_context()

        return self._client.reason_with_image(
            model=self._reasoning_model,
            system_prompt=build_system_prompt(),
            question=question,
            memory_context=memory_context,
            image_b64=image_b64,
        )
