"""Video source resolution and adaptation utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CameraSource:
    """Resolved camera source metadata."""

    source_type: str
    source_value: int | str


class CameraAdapter:
    """Resolve an input source into a concrete OpenCV capture value."""

    @staticmethod
    def resolve(source: str, source_type: str = "auto") -> CameraSource:
        """Resolve source into one of: file, webcam, rtsp, livekit."""
        normalized_type = source_type.lower().strip()

        if normalized_type == "webcam":
            return CameraSource(source_type="webcam", source_value=int(source))
        if normalized_type == "rtsp":
            return CameraSource(source_type="rtsp", source_value=source)
        if normalized_type == "file":
            return CameraSource(source_type="file", source_value=source)
        if normalized_type == "livekit":
            return CameraSource(source_type="livekit", source_value=source)

        # auto mode
        if source.lower().startswith("rtsp://"):
            return CameraSource(source_type="rtsp", source_value=source)
        if source.lower().startswith(("ws://", "wss://")):
            return CameraSource(source_type="livekit", source_value=source)
        if source.isdigit():
            return CameraSource(source_type="webcam", source_value=int(source))
        return CameraSource(source_type="file", source_value=source)
