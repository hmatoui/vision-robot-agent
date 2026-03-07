"""FastAPI route definitions for the Vision Agent backend."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.vision.image_utils import frame_to_jpeg_bytes


class AskRequest(BaseModel):
    """Incoming ask request payload."""

    question: str = Field(min_length=1, max_length=500)


class AskResponse(BaseModel):
    """Answer payload."""

    answer: str


def build_router(container: Any) -> APIRouter:
    """Create API router with bound dependencies."""
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/frame")
    def get_frame() -> Response:
        try:
            frame = container.video_stream.get_latest_frame()
            return Response(content=frame_to_jpeg_bytes(frame), media_type="image/jpeg")
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @router.get("/memory")
    def get_memory() -> dict[str, list[dict[str, Any]]]:
        return {"observations": container.scene_memory.get_observations()}

    @router.post("/ask", response_model=AskResponse)
    def ask(req: AskRequest) -> AskResponse:
        try:
            frame = container.video_stream.get_latest_frame()
            answer = container.agent.answer(req.question, frame)
            return AskResponse(answer=answer)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return router
