"""Image utility helpers for frame conversion and encoding."""

from __future__ import annotations

import base64
from typing import Tuple

import cv2
import numpy as np


def frame_to_jpeg_bytes(frame: np.ndarray, quality: int = 85) -> bytes:
    """Encode a BGR OpenCV frame to JPEG bytes."""
    success, buffer = cv2.imencode(
        ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
    )
    if not success:
        raise ValueError("Failed to encode frame to JPEG")
    return buffer.tobytes()


def frame_to_base64_jpeg(frame: np.ndarray, quality: int = 85) -> str:
    """Encode frame to base64 JPEG string."""
    jpeg = frame_to_jpeg_bytes(frame, quality=quality)
    return base64.b64encode(jpeg).decode("utf-8")


def resize_frame(frame: np.ndarray, max_size: Tuple[int, int] = (1024, 1024)) -> np.ndarray:
    """Resize frame while preserving aspect ratio with an upper size bound."""
    max_w, max_h = max_size
    h, w = frame.shape[:2]
    scale = min(max_w / w, max_h / h, 1.0)
    if scale == 1.0:
        return frame
    new_size = (int(w * scale), int(h * scale))
    return cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)
