"""Utility script to validate a configured video source."""

from __future__ import annotations

from app.config.settings import settings
from app.video.video_stream import VideoStream


def main() -> None:
    """Start stream and print a quick validation message."""
    stream = VideoStream(
        settings.video_source,
        settings.video_source_type,
        livekit_url=settings.livekit_url,
        livekit_token=settings.livekit_token
    )
    stream.start()
    frame = stream.get_latest_frame()
    print(f"Loaded frame shape: {frame.shape}")
    stream.stop()


if __name__ == "__main__":
    main()
