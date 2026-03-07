"""Threaded OpenCV video capture for files/cameras/RTSP streams."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from loguru import logger

from app.video.camera_adapter import CameraAdapter


class VideoStream:
    """Continuously captures frames and exposes latest frame snapshot."""

    def __init__(self, source: str, source_type: str = "auto") -> None:
        self.source = source
        self.source_type = source_type

        self._capture: Optional[cv2.VideoCapture] = None
        self._latest_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        """Start capture background thread."""
        if self._running:
            return

        resolved = CameraAdapter.resolve(self.source, self.source_type)
        if resolved.source_type == "file":
            src_path = Path(str(resolved.source_value))
            if not src_path.exists():
                if src_path.as_posix().endswith("tests/sample_videos/test_video.mp4"):
                    self._generate_synthetic_video(src_path)
                else:
                    raise FileNotFoundError(
                        f"Video file not found: {src_path}. Set VIDEO_SOURCE to a valid file/webcam/rtsp."
                    )

        self._capture = cv2.VideoCapture(resolved.source_value)
        if not self._capture.isOpened():
            raise RuntimeError(f"Cannot open video source: {resolved.source_value}")

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

        for _ in range(40):
            try:
                self.get_latest_frame()
                break
            except RuntimeError:
                time.sleep(0.05)

        logger.info(f"VideoStream started ({resolved.source_type}: {resolved.source_value})")

    def stop(self) -> None:
        """Stop capture and release resources."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        if self._capture is not None:
            self._capture.release()
        self._capture = None
        logger.info("VideoStream stopped")

    def get_latest_frame(self) -> np.ndarray:
        """Return latest frame copy."""
        with self._lock:
            if self._latest_frame is None:
                raise RuntimeError("No frame available yet. Stream may still be warming up.")
            return self._latest_frame.copy()

    def _capture_loop(self) -> None:
        """Internal capture loop with loop-back for finite video files."""
        assert self._capture is not None

        while self._running:
            ok, frame = self._capture.read()
            if not ok or frame is None:
                # Loop file streams in dev mode; for camera/rtsp just retry.
                self._capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                time.sleep(0.05)
                continue

            with self._lock:
                self._latest_frame = frame

            time.sleep(0.01)

    @staticmethod
    def _generate_synthetic_video(path: Path, frames: int = 60) -> None:
        """Generate a deterministic dev sample video when default fixture is missing."""
        path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(path), fourcc, 10.0, (640, 360))
        if not writer.isOpened():
            raise RuntimeError(f"Failed to create synthetic video at {path}")

        for i in range(frames):
            frame = np.zeros((360, 640, 3), dtype=np.uint8)
            frame[:] = (20, 20 + i % 80, 40 + i % 100)
            cv2.rectangle(frame, (80 + i * 3 % 300, 120), (260 + i * 3 % 300, 280), (40, 180, 240), -1)
            cv2.putText(
                frame,
                f"sample frame {i}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            writer.write(frame)

        writer.release()
        logger.info(f"Generated synthetic sample video at {path}")
