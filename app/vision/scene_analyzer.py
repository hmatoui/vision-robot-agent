"""Scene analysis service using OpenAI Vision model."""

from __future__ import annotations

import numpy as np

from app.openai_client.client import OpenAIClient
from app.vision.image_utils import frame_to_base64_jpeg, resize_frame


class SceneAnalyzer:
    """Generate concise scene descriptions from frames."""

    def __init__(self, client: OpenAIClient, model: str) -> None:
        self._client = client
        self._model = model

    def describe_scene(self, frame: np.ndarray) -> str:
        """Return compact scene description for memory updates."""
        reduced = resize_frame(frame, max_size=(1024, 1024))
        image_b64 = frame_to_base64_jpeg(reduced, quality=80)
        return self._client.vision_describe(
            model=self._model,
            prompt=(
                "You are a robot scene summarizer. Describe visible people, objects, "
                "and motion in one short sentence."
            ),
            image_b64=image_b64,
        )
