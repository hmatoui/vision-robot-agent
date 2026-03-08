"""FastAPI route definitions for the Vision Agent backend."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from loguru import logger
from pydantic import BaseModel, Field

from app.config.settings import settings
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

    @router.get("/conversation")
    def get_conversation() -> dict[str, list[dict[str, str]]]:
        return {"history": container.conversation_history[-5:]}

    @router.post("/reset-conversations")
    def reset_conversations() -> dict[str, str]:
        container.conversation_history.clear()
        return {"message": "Conversation history reset"}

    @router.post("/reset-log")
    def reset_log() -> dict[str, str]:
        try:
            with open(settings.log_file, "w", encoding="utf-8") as f:
                f.write("")
            return {"message": "Log file reset"}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @router.post("/ask", response_model=AskResponse)
    def ask(req: AskRequest) -> AskResponse:
        try:
            frame = container.video_stream.get_latest_frame()
            answer = container.agent.answer(req.question, frame)
            interaction = {"question": req.question, "answer": answer}
            container.conversation_history.append(interaction)
            if len(container.conversation_history) > 5:
                container.conversation_history.pop(0)
            
            # Get video time from latest observation
            observations = container.scene_memory.get_observations()
            video_time = observations[-1]["timestamp"] if observations else "unknown"
            
            # Log only conversations with video time
            conversation_logger = logger.bind(name="conversation")
            conversation_logger.info(f"[{video_time}] Q: {req.question} | A: {answer}")
            
            return AskResponse(answer=answer)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return router
