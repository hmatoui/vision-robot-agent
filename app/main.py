"""Application composition root and FastAPI app."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.agent.vision_agent import VisionAgent
from app.api.routes import build_router
from app.config.settings import settings
from app.memory.scene_memory import SceneMemory
from app.openai_client.client import OpenAIClient
from app.video.frame_sampler import FrameSampler
from app.video.video_stream import VideoStream
from app.vision.scene_analyzer import SceneAnalyzer


@dataclass
class AppContainer:
    """Shared runtime services and adapters."""

    video_stream: VideoStream
    scene_memory: SceneMemory
    scene_analyzer: SceneAnalyzer
    frame_sampler: FrameSampler
    agent: VisionAgent
    conversation_history: list[dict[str, str]]


def _build_container() -> AppContainer:
    client = OpenAIClient(api_key=settings.openai_api_key)
    memory = SceneMemory(
        retention_seconds=settings.memory_retention_seconds,
        max_entries=settings.memory_max_entries,
    )
    stream = VideoStream(
        source=settings.video_source,
        source_type=settings.video_source_type,
        livekit_url=settings.livekit_url,
        livekit_token=settings.livekit_token
    )
    analyzer = SceneAnalyzer(client=client, model=settings.openai_vision_model)
    sampler = FrameSampler(interval_seconds=settings.frame_sample_seconds)
    agent = VisionAgent(
        openai_client=client,
        scene_memory=memory,
        reasoning_model=settings.openai_reasoning_model,
    )
    return AppContainer(
        video_stream=stream,
        scene_memory=memory,
        scene_analyzer=analyzer,
        frame_sampler=sampler,
        agent=agent,
        conversation_history=[],
    )


def _create_app() -> FastAPI:
    container = _build_container()

    #logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level="WARNING",  # Only show warnings and errors in console
        backtrace=False,
        diagnose=False,
    )
    # Conversation logger that only logs conversations to file
    conversation_logger = logger.bind(name="conversation")
    conversation_logger.add(
        settings.log_file,
        level="INFO",
        rotation="10 MB",
        retention="1 week",
        encoding="utf-8",
        filter=lambda record: record["extra"].get("name") == "conversation"
    )

    app = FastAPI(title="Vision Robot Agent", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.container = container
    logger.info("App container initialized with video stream, scene memory, analyzer, and agent")
    app.include_router(build_router(container))

    web_dir = Path(__file__).resolve().parent.parent / "web"
    if web_dir.exists():
        app.mount("/dashboard", StaticFiles(directory=str(web_dir), html=True), name="dashboard")

    @app.on_event("startup")
    async def startup_event() -> None:
        container.video_stream.start()
        logger.info("Video stream started, initializing memory update loop")

        async def memory_loop() -> None:
            while True:
                try:
                    if container.frame_sampler.should_sample():
                        frame = container.video_stream.get_latest_frame()
                        description = container.scene_analyzer.describe_scene(frame)
                        container.scene_memory.add_observation(description)
                        logger.info(f"Memory updated: {description}")
                except RuntimeError as exc:
                    # Frame capture may take a moment to warm up, especially on slow sources.
                    # Avoid spamming the log with repeated errors while waiting for the first frame.
                    if "No frame available yet" in str(exc):
                        logger.debug("Waiting for first video frame (stream warming up)")
                        continue
                    logger.error(f"Memory update loop error: {exc}")
                except Exception as exc:  # noqa: BLE001
                    logger.error(f"Memory update loop error: {exc}")
                await asyncio.sleep(0.5)

        app.state.memory_task = asyncio.create_task(memory_loop())
        logger.info("Application startup complete")

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        task = getattr(app.state, "memory_task", None)
        if task:
            task.cancel()
        container.video_stream.stop()
        logger.info("Application shutdown complete")

    return app


app = _create_app()
