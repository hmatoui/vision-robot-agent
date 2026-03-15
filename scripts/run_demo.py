"""Interactive CLI demo for Vision Robot Agent."""

from __future__ import annotations

import threading
import time

from rich.console import Console
from rich.prompt import Prompt

from app.agent.vision_agent import VisionAgent
from app.config.settings import settings
from app.memory.scene_memory import SceneMemory
from app.openai_client.client import OpenAIClient
from app.video.frame_sampler import FrameSampler
from app.video.video_stream import VideoStream
from app.vision.scene_analyzer import SceneAnalyzer

console = Console()


def main() -> None:
    """Run a local CLI question-answering loop over video input."""
    client = OpenAIClient(settings.openai_api_key)
    memory = SceneMemory(settings.memory_retention_seconds, settings.memory_max_entries)
    stream = VideoStream(
        settings.video_source,
        settings.video_source_type,
        livekit_url=settings.livekit_url,
        livekit_token=settings.livekit_token
    )
    analyzer = SceneAnalyzer(client, settings.openai_vision_model)
    sampler = FrameSampler(settings.frame_sample_seconds)
    agent = VisionAgent(client, memory, settings.openai_reasoning_model)

    stream.start()
    running = True

    def memory_worker() -> None:
        while running:
            try:
                if sampler.should_sample():
                    frame = stream.get_latest_frame()
                    description = analyzer.describe_scene(frame)
                    memory.add_observation(description)
            except Exception:
                pass
            time.sleep(0.5)

    thread = threading.Thread(target=memory_worker, daemon=True)
    thread.start()

    console.print("[bold green]Vision Robot Agent CLI started.[/bold green]")
    console.print("Type questions, or 'exit' to quit.\n")

    try:
        while True:
            question = Prompt.ask("[cyan]Question[/cyan]").strip()
            if question.lower() in {"exit", "quit"}:
                break

            frame = stream.get_latest_frame()
            answer = agent.answer(question, frame)
            console.print(f"[yellow]Answer:[/yellow] {answer}\n")
    finally:
        running = False
        stream.stop()
        console.print("[bold]Stopped.[/bold]")


if __name__ == "__main__":
    main()
