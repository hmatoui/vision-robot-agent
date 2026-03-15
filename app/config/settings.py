"""Application settings and environment configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    openai_api_key: str = ""
    openai_vision_model: str = "gpt-4.1-mini"
    openai_reasoning_model: str = "gpt-4.1-mini"

    video_source: str = "tests/sample_videos/test_video.mp4"
    video_source_type: str = "auto"  # auto | file | webcam | rtsp | livekit

    # LiveKit configuration
    livekit_url: str = "ws://172.28.209.77:17880"
    livekit_token: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzM2MTUxMTQsImlkZW50aXR5Ijoidmlld2VyLXdlYiIsImlzcyI6Im15a2V5IiwibmJmIjoxNzczNTI4NzE0LCJzdWIiOiJ2aWV3ZXItd2ViIiwidmlkZW8iOnsiY2FuUHVibGlzaCI6ZmFsc2UsImNhblN1YnNjcmliZSI6dHJ1ZSwicm9vbSI6ImRldi1yb29tIiwicm9vbUpvaW4iOnRydWV9fQ.iHytBRBIRnyW2a9f1eKRUV4U27xZN3f8e2y7mdpkR3s"

    frame_sample_seconds: int = 5
    memory_retention_seconds: int = 60
    memory_max_entries: int = 12

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    log_file: str = "logs/conversation.log"

    @classmethod
    def from_env(cls, env_file: str | Path = ".env") -> "Settings":
        """Load settings from .env and process environment variables."""
        load_dotenv(dotenv_path=env_file, override=False)
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_vision_model=os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini"),
            openai_reasoning_model=os.getenv("OPENAI_REASONING_MODEL", "gpt-4.1-mini"),
            video_source=os.getenv("VIDEO_SOURCE", "tests/sample_videos/test_video.mp4"),
            video_source_type=os.getenv("VIDEO_SOURCE_TYPE", "auto"),
            livekit_url=os.getenv("LIVEKIT_URL", ""),
            livekit_token=os.getenv("LIVEKIT_TOKEN", ""),
            frame_sample_seconds=int(os.getenv("FRAME_SAMPLE_SECONDS", "5")),
            memory_retention_seconds=int(os.getenv("MEMORY_RETENTION_SECONDS", "60")),
            memory_max_entries=int(os.getenv("MEMORY_MAX_ENTRIES", "12")),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "logs/conversation.log"),
        )


settings = Settings.from_env()
