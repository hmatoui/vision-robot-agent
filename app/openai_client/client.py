"""OpenAI client wrapper for vision and reasoning calls."""

from __future__ import annotations

from typing import Any

from loguru import logger
from openai import APIConnectionError, APITimeoutError, OpenAI


class OpenAIClient:
    """Small adapter around OpenAI SDK with safe fallbacks for local dev."""

    def __init__(self, api_key: str | None = None) -> None:
        self._enabled = bool(api_key)
        self._client = OpenAI(api_key=api_key) if api_key else None
        if not self._enabled:
            logger.warning(
                "OPENAI_API_KEY not set. Running in fallback mode with synthetic responses."
            )

    @property
    def enabled(self) -> bool:
        """Whether external OpenAI calls are available."""
        return self._enabled and self._client is not None

    def vision_describe(self, model: str, prompt: str, image_b64: str) -> str:
        """Generate a compact scene description from an image."""
        if not self.enabled:
            return "Scene appears static in local fallback mode."

        assert self._client is not None
        try:
            response = self._client.responses.create(
                model=model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{image_b64}",
                            },
                        ],
                    }
                ],
                max_output_tokens=120,
            )
            return (response.output_text or "").strip() or "No scene description returned."
        except (APIConnectionError, APITimeoutError) as exc:
            logger.warning(f"OpenAI vision request failed due to connection issue: {exc}")
            return "Scene description unavailable due to OpenAI connection issues."

    def reason_with_image(
        self,
        model: str,
        system_prompt: str,
        question: str,
        memory_context: str,
        image_b64: str,
    ) -> str:
        """Answer a user question using image and temporal context."""
        if not self.enabled:
            return (
                "Fallback answer: I cannot call OpenAI right now. "
                f"Question received: '{question}'. Recent memory: {memory_context}"
            )

        assert self._client is not None
        content: list[dict[str, Any]] = [
            {
                "type": "input_text",
                "text": (
                    f"{system_prompt}\n\n"
                    f"Recent observations:\n{memory_context or 'No recent observations.'}\n\n"
                    f"User question: {question}\n"
                    "Answer concisely, mention uncertainty when needed."
                ),
            },
            {
                "type": "input_image",
                "image_url": f"data:image/jpeg;base64,{image_b64}",
            },
        ]

        logger.info("Sending OpenAI reasoning request for user question.")
        try:
            response = self._client.responses.create(
                model=model,
                input=[{"role": "user", "content": content}],
                max_output_tokens=220,
            )
            return (response.output_text or "").strip() or "No answer returned from model."
        except (APIConnectionError, APITimeoutError) as exc:
            logger.warning(f"OpenAI reasoning request failed due to connection issue: {exc}")
            return (
                "Fallback answer: OpenAI is temporarily unreachable. "
                f"Question received: '{question}'. Recent memory: {memory_context}"
            )
