"""Unit tests for video streaming service."""

from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from app.video.video_stream import VideoStream


def _generate_sample_video(path: Path, frames: int = 25) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, 10.0, (320, 240))
    if not writer.isOpened():
        raise RuntimeError("Failed to initialize sample video writer")

    for i in range(frames):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        color = (i * 10 % 255, 120, 220)
        frame[:] = color
        cv2.putText(
            frame,
            f"frame {i}",
            (40, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        writer.write(frame)

    writer.release()


def test_video_stream_reads_frames(tmp_path: Path) -> None:
    video_path = tmp_path / "sample.mp4"
    _generate_sample_video(video_path)

    stream = VideoStream(source=str(video_path), source_type="file")
    stream.start()
    time.sleep(0.2)

    frame = stream.get_latest_frame()
    assert frame.shape[0] > 0 and frame.shape[1] > 0

    stream.stop()
