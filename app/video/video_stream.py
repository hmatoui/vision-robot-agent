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
from app.video.livekit_stream import LiveKitVideoStream


class VideoStream:
    """Continuously captures frames and exposes latest frame snapshot."""

    def __init__(self, source: str, source_type: str = "auto", livekit_url: str = "", livekit_token: str = "") -> None:
        self.source = source
        self.source_type = source_type
        self.livekit_url = livekit_url
        self.livekit_token = livekit_token

        self._capture: Optional[cv2.VideoCapture] = None
        self._livekit_stream: Optional[LiveKitVideoStream] = None
        self._latest_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        """Start capture background thread."""
        if self._running:
            return

        resolved = CameraAdapter.resolve(self.source, self.source_type)

        if resolved.source_type == "livekit":
            # Use LiveKit stream
            if not self.livekit_url or not self.livekit_token:
                raise ValueError("LiveKit URL and token must be provided for LiveKit sources")
            self._livekit_stream = LiveKitVideoStream(self.livekit_url, self.livekit_token)
            logger.info("LiveKit VideoStream started")
            self._livekit_stream.start()
            self._running = True
            self._thread = threading.Thread(target=self._livekit_capture_loop, daemon=True)
            self._thread.start()
        else:
            # Use OpenCV capture for other sources
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

        # Wait for first frame
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
        if self._livekit_stream is not None:
            self._livekit_stream.stop()
        self._capture = None
        self._livekit_stream = None
        logger.info("VideoStream stopped")

    def get_latest_frame(self) -> np.ndarray:
        """Return latest frame copy."""
        with self._lock:
            if self._latest_frame is None:
                raise RuntimeError("No frame available yet. Stream may still be warming up.")
            return self._latest_frame.copy()

    def _livekit_capture_loop(self) -> None:
        """Internal capture loop for LiveKit streams."""
        assert self._livekit_stream is not None

        while self._running:
            frame = self._livekit_stream.get_latest_frame()
            if frame is not None:
                with self._lock:
                    self._latest_frame = frame
            time.sleep(0.01)

    def _capture_loop(self) -> None:
        """Internal capture loop for OpenCV sources."""
        assert self._capture is not None

        while self._running:
            ret, frame = self._capture.read()
            if ret:
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
